"""
Configuration module.
Loads environment variables and exposes app-wide settings.
"""

import os
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()

# OpenRouter API key – required for LLM calls
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

# Optional metadata for OpenRouter analytics (recommended)
HTTP_REFERER: str = os.getenv("HTTP_REFERER", "http://localhost:8000")
X_TITLE: str = os.getenv("X_TITLE", "CV Summarizer API")

# Guard: fail fast if the key is missing
if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY is not set. "
        "Create a .env file with OPENROUTER_API_KEY=sk-or-..."
    )