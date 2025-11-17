"""Pydantic models for API requests and responses."""

from typing import Optional, List
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Request model for POST /ask endpoint."""

    prompt: str = Field(..., description="The prompt to send to Gemini")
    model: str = Field(
        default="gemini-2.5-pro",
        description="Model to use: 'gemini-2.5-pro' or 'gemini-2.5-flash'"
    )
    fallback_to_flash: bool = Field(
        default=True,
        description="Automatically fallback to Flash if Pro quota exceeded"
    )
    files: Optional[List[str]] = Field(
        default=None,
        description="List of file paths to upload (not implemented in v1)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Explain quantum computing in simple terms",
                "model": "gemini-2.5-pro",
                "fallback_to_flash": True
            }
        }


class ResponseMeta(BaseModel):
    """Metadata about the response."""

    latency_ms: int = Field(..., description="Total latency in milliseconds")


class AskResponse(BaseModel):
    """Success response model for POST /ask endpoint."""

    model_requested: str = Field(..., description="Model that was requested")
    model_used: str = Field(..., description="Model that was actually used")
    fallback_triggered: bool = Field(
        ...,
        description="Whether fallback from Pro to Flash was triggered"
    )
    response_text: str = Field(..., description="Plain text response from Gemini")
    raw_response_html: Optional[str] = Field(
        default=None,
        description="Raw HTML of the response (optional)"
    )
    meta: ResponseMeta = Field(..., description="Response metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "model_requested": "gemini-2.5-pro",
                "model_used": "gemini-2.5-pro",
                "fallback_triggered": False,
                "response_text": "Quantum computing is a type of computing...",
                "raw_response_html": "<div>...</div>",
                "meta": {
                    "latency_ms": 5432
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    details: str = Field(..., description="Detailed error message")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "gemini_session_expired",
                "details": "Detected Google login page; please rerun login helper."
            }
        }
