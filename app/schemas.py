from datetime import date
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RecipientIn(BaseModel):
    """A single recipient in a generation request."""

    name: str = Field(..., min_length=1, max_length=255, description="Recipient full name")
    email: EmailStr = Field(..., description="Recipient email address")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class JobCreateRequest(BaseModel):
    """Request body for creating a new certificate generation job."""

    event_name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the event or course"
    )
    issuer_name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the issuing organisation"
    )
    issue_date: date = Field(..., description="Date to print on the certificate (YYYY-MM-DD)")
    recipients: List[RecipientIn] = Field(
        ..., min_length=1, description="List of recipients (at least one required)"
    )

    @field_validator("event_name", "issuer_name")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must not be blank")
        return v.strip()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class CertificateOut(BaseModel):
    """Individual certificate summary returned to the client."""

    id: str
    recipient_name: str
    recipient_email: str
    status: str
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class JobStatusResponse(BaseModel):
    """Full job status including per-certificate details."""

    id: str
    event_name: str
    issuer_name: str
    issue_date: str
    status: str
    total: int
    successful: int
    failed: int
    certificates: List[CertificateOut]

    model_config = {"from_attributes": True}


class JobCreateResponse(BaseModel):
    """Lightweight response returned immediately after job creation."""

    job_id: str
    status: str
    total_recipients: int
    message: str
