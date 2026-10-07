"""
API router for certificate job endpoints.

Endpoints:
  POST /jobs                     – Create a new generation job
  GET  /jobs/{job_id}            – Get job status and progress
  GET  /jobs/{job_id}/certificates/{cert_id}/download  – Download a PDF
"""

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Certificate, CertificateJob, CertificateStatus, JobStatus
from app.schemas import JobCreateRequest, JobCreateResponse, JobStatusResponse
from app.tasks import process_certificate_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a certificate generation job",
)
def create_job(payload: JobCreateRequest, db: Session = Depends(get_db)):
    """
    Accept a bulk certificate generation request.

    - Validates all recipient data via Pydantic (returns 422 on invalid input).
    - Creates a Job record and individual Certificate records (all PENDING).
    - Dispatches a background Celery task to generate the PDFs.
    - Returns immediately with the job_id so the client can poll for progress.
    """
    # Create the parent job
    job = CertificateJob(
        event_name=payload.event_name,
        issuer_name=payload.issuer_name,
        issue_date=str(payload.issue_date),
        total=len(payload.recipients),
    )
    db.add(job)
    db.flush()  # get job.id without committing yet

    # Create individual certificate records
    for recipient in payload.recipients:
        cert = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=str(recipient.email),
        )
        db.add(cert)

    db.commit()
    db.refresh(job)

    # Dispatch background task
    process_certificate_job.delay(job.id)

    return JobCreateResponse(
        job_id=job.id,
        status=job.status.value,
        total_recipients=job.total,
        message=(
            f"Job created successfully. {job.total} certificate(s) are being generated "
            "in the background. Poll GET /jobs/{job_id} to check progress."
        ),
    )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status and per-certificate results",
)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Return the current status of a certificate job.

    Includes:
    - Overall status (pending / processing / completed / failed)
    - Counters for total, successful, and failed certificates
    - Per-certificate status with error messages for failures
    """
    job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    return job


@router.get(
    "/{job_id}/certificates/{cert_id}/download",
    summary="Download a generated certificate PDF",
)
def download_certificate(job_id: str, cert_id: str, db: Session = Depends(get_db)):
    """
    Download the generated PDF for a specific certificate.

    Returns 404 if the job or certificate does not exist, and 409 if
    the certificate has not been successfully generated yet.
    """
    job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )

    cert = (
        db.query(Certificate)
        .filter(Certificate.id == cert_id, Certificate.job_id == job_id)
        .first()
    )
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{cert_id}' not found in job '{job_id}'.",
        )

    if cert.status != CertificateStatus.SUCCESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Certificate is not ready. Current status: {cert.status.value}. "
                + (f"Error: {cert.error_message}" if cert.error_message else "")
            ),
        )

    if not cert.file_path or not Path(cert.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Certificate file is missing from disk.",
        )

    safe_name = f"certificate_{cert.recipient_name.replace(' ', '_')}_{cert.id[:8]}.pdf"
    return FileResponse(
        path=cert.file_path,
        media_type="application/pdf",
        filename=safe_name,
    )
