"""
Pydantic models for request/response validation and serialization.
"""

from pydantic import BaseModel, Field


class CVSummary(BaseModel):
    """Structured summary extracted from a CV."""

    name: str = Field(
        ...,
        description="Full name of the candidate",
        examples=["Jane Doe"],
    )
    location: str = Field(
        ...,
        description="City, country or region where the candidate is based",
        examples=["Berlin, Germany"],
    )
    work_experience_summary: str = Field(
        ...,
        description="Concise summary of the candidate's work experience",
        examples=[
            "5+ years as a backend engineer at fintech startups, "
            "specialising in Python and distributed systems."
        ],
    )


class ErrorResponse(BaseModel):
    """Standard error payload returned by the API."""

    error: str = Field(..., description="Human-readable error message")
    detail: str | None = Field(
        None, description="Additional technical detail (optional)"
    )