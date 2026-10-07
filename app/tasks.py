"""
Celery tasks for background certificate generation.

Design decisions:
- One Celery task per JOB (process_certificate_job).
  It iterates over all recipients inside the task so that a single Redis
  round-trip dispatches all work, keeping overhead low for large batches.
- Individual certificate failures are caught and recorded without aborting
  the rest of the job, satisfying the requirement that one bad certificate
  must not block the others.
- The job status transitions are:
    PENDING → PROCESSING (when the task starts)
    PROCESSING → COMPLETED / FAILED (when all certificates are done)
  The job is marked FAILED only if every single certificate failed;
  otherwise it is COMPLETED (with per-certificate failure details available).
"""

import logging
from typing import List

from app.celery_app import celery_app
from app.certificate_generator import generate_certificate_pdf
from app.database import SessionLocal
from app.models import Certificate, CertificateJob, CertificateStatus, JobStatus

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_certificate_job(self, job_id: str) -> dict:
    """
    Background task: generate all certificates for a job.

    Args:
        job_id: Primary key of the CertificateJob to process.

    Returns:
        A summary dict {job_id, successful, failed}.
    """
    db = SessionLocal()
    try:
        job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
        if not job:
            logger.error("Job %s not found", job_id)
            return {"error": f"Job {job_id} not found"}

        # Transition to PROCESSING
        job.status = JobStatus.PROCESSING
        db.commit()

        certificates = (
            db.query(Certificate).filter(Certificate.job_id == job_id).all()
        )

        successful = 0
        failed = 0

        for cert in certificates:
            try:
                file_path = generate_certificate_pdf(
                    cert_id=cert.id,
                    recipient_name=cert.recipient_name,
                    recipient_email=cert.recipient_email,
                    event_name=job.event_name,
                    issuer_name=job.issuer_name,
                    issue_date=job.issue_date,
                )
                cert.status = CertificateStatus.SUCCESS
                cert.file_path = file_path
                successful += 1
                logger.info("Generated certificate %s for %s", cert.id, cert.recipient_email)
            except Exception as exc:
                cert.status = CertificateStatus.FAILED
                cert.error_message = str(exc)
                failed += 1
                logger.warning(
                    "Failed to generate certificate %s: %s", cert.id, exc
                )
            finally:
                db.commit()

        # Update job counters and final status
        job.successful = successful
        job.failed = failed
        # If at least one succeeded → COMPLETED; all failed → FAILED
        job.status = JobStatus.COMPLETED if successful > 0 else JobStatus.FAILED
        db.commit()

        logger.info(
            "Job %s finished: %d successful, %d failed", job_id, successful, failed
        )
        return {"job_id": job_id, "successful": successful, "failed": failed}

    except Exception as exc:
        # Unexpected error: mark job as FAILED and re-raise for Celery retry
        db.rollback()
        try:
            job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                db.commit()
        except Exception:
            pass
        logger.exception("Unexpected error processing job %s", job_id)
        raise self.retry(exc=exc)
    finally:
        db.close()
