"""
OpenRouter LLM client.

Sends the extracted CV text to a selected model and asks for a structured
JSON summary containing name, location, and work-experience summary.
"""

import json
from openrouter import OpenRouter

from app.config import OPENROUTER_API_KEY, HTTP_REFERER, X_TITLE
from app.models import CVSummary

# System prompt – instructs the model to behave as a CV parser.
SYSTEM_PROMPT = """\
You are an expert CV/resume parser. You will receive raw text extracted from a
candidate's CV. Your task is to extract exactly three fields and return them as
a valid JSON object:

{
  "name": "<full name of the candidate>",
  "location": "<city, country or region where the candidate is based>",
  "work_experience_summary": "<concise 2–4 sentence summary of the candidate's work experience, including roles, companies, years, and key skills>"
}

Rules:
- If a field cannot be determined, use the string "Not specified".
- Do NOT include any text outside the JSON object.
- Ensure the JSON is valid and parseable.
"""


async def summarize_cv(cv_text: str) -> CVSummary:
    """
    Call OpenRouter with the CV text and return a validated CVSummary.

    Parameters
    ----------
    cv_text : str
        Raw text extracted from the candidate's PDF.

    Returns
    -------
    CVSummary
        Pydantic model with name, location, and work-experience summary.

    Raises
    ------
    RuntimeError
        If the LLM returns malformed JSON or the API call fails.
    """
    # --- 1. Build the messages payload ------------------------------------
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Extract the required fields from this CV text:\n\n{cv_text}",
        },
    ]

    # --- 2. Call OpenRouter -----------------------------------------------
    try:
        with OpenRouter(
            api_key=OPENROUTER_API_KEY,
            http_referer=HTTP_REFERER,  # optional – helps with rankings
            x_title=X_TITLE,  # optional – app display name
        ) as client:
            response = client.chat.send(
                model="openai/gpt-4o-mini",  # fast & cheap; swap as needed
                messages=messages,
                stream=False,
                temperature=0.0,  # deterministic output
            )
    except Exception as exc:
        raise RuntimeError(f"OpenRouter API call failed: {exc}") from exc

    # --- 3. Extract the assistant's reply ---------------------------------
    try:
        content: str = response.choices[0].message.content
    except (AttributeError, IndexError) as exc:
        raise RuntimeError(
            "Unexpected response structure from OpenRouter."
        ) from exc

    # --- 4. Parse the JSON string into a dict -----------------------------
    try:
        # Some models wrap JSON in markdown fences – strip them if present.
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]  # remove the fence
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]  # remove the language tag
        data: dict = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"LLM returned invalid JSON: {content[:200]}..."
        ) from exc

    # --- 5. Validate & return the Pydantic model --------------------------
    return CVSummary(**data)