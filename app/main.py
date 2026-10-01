"""
FastAPI application – CV Summarizer API.

Endpoints
---------
POST /summarize
    Accepts a PDF file, extracts text, calls OpenRouter, and returns a
    structured JSON summary.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.pdf_extractor import extract_text_from_pdf
from app.llm_client import summarize_cv
from app.models import CVSummary, ErrorResponse

# App instance
app = FastAPI(
    title="CV Summarizer API",
    description=(
        "Upload a PDF CV and receive a structured summary "
        "(name, location, work experience) powered by an LLM."
    ),
    version="1.0.0",
)


# Global exception handlers – ensure every error is structured JSON
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    """Return a consistent ErrorResponse for all HTTP errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=None,
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Handle Pydantic validation errors (e.g., missing file)."""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation error",
            detail=str(exc.errors()),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    """Catch-all for unexpected errors – never leak stack traces."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail="An unexpected error occurred. Please try again later.",
        ).model_dump(),
    )



# Endpoint
# ---------------------------------------------------------------------------
@app.post(
    "/summarize",
    response_model=CVSummary,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid PDF"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal error"},
    },
    summary="Summarize a CV PDF",
    description=(
        "Upload a PDF file containing a CV. The API extracts the text, "
        "sends it to an LLM via OpenRouter, and returns a JSON object "
        "with the candidate's name, location, and work-experience summary."
    ),
)
async def summarize_cv_endpoint(
    file: UploadFile = File(
        ...,
        description="PDF file of the candidate's CV/resume",
    ),
):
    """
    Main endpoint – orchestrates PDF extraction → LLM summarization.
    """
    # 1. Extract text from the uploaded PDF
    cv_text: str = await extract_text_from_pdf(file)

    # 2. Call the LLM and get a structured summary
    try:
        summary: CVSummary = await summarize_cv(cv_text)
    except RuntimeError as exc:
        # Convert LLM/parsing errors into a 502 Bad Gateway
        raise HTTPException(
            status_code=502,
            detail=f"LLM summarization failed: {exc}",
        ) from exc

    # 3. Return the structured response
    return summary


# ---------------------------------------------------------------------------
# Health check (useful for deployment platforms)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["ops"])
async def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}