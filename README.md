# Bulk Certificate Generator

A production-ready backend API for bulk PDF certificate generation. Submit a list of recipients in one request; the system generates personalised certificates asynchronously and lets you track progress and download results.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Setup](#setup)
4. [Running the Application](#running-the-application)
5. [Running Tests](#running-tests)
6. [API Reference](#api-reference)
7. [Design Decisions](#design-decisions)

---

## Architecture Overview

```
Client
  |
  v
FastAPI (HTTP API)           <- validates input, persists records, dispatches tasks
  |
  |-- SQLite (SQLAlchemy)    <- stores Job and Certificate records
  |
  +-- Celery Task --> Redis  <- background PDF generation per job
                      |
                      +-- ReportLab  <- generates A4 landscape PDF per recipient
```

---

## Project Structure

```
.
+-- app/
|   +-- __init__.py
|   +-- main.py                 # FastAPI app factory + lifespan
|   +-- config.py               # Settings (pydantic-settings, reads .env)
|   +-- database.py             # SQLAlchemy engine + session factory
|   +-- models.py               # ORM models: CertificateJob, Certificate
|   +-- schemas.py              # Pydantic request/response schemas
|   +-- routes.py               # API route handlers
|   +-- certificate_generator.py # ReportLab PDF generation logic
|   +-- celery_app.py           # Celery application instance
|   +-- tasks.py                # Celery background task
+-- tests/
|   +-- conftest.py             # Shared pytest fixtures
|   +-- test_create_job.py      # Job creation + input validation tests
|   +-- test_certificate_generation.py  # PDF generation unit tests
|   +-- test_job_status.py      # Status/progress + failure handling tests
|   +-- test_download.py        # Certificate download tests
+-- .env.example
+-- pytest.ini
+-- requirements.txt
+-- README.md
```

---

## Setup

### Prerequisites

- Python 3.10+
- Redis (for Celery broker/backend)

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd "Certificate Generation Machine"
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment (optional)

```bash
cp .env.example .env
# Edit .env if you need non-default settings (e.g. PostgreSQL, custom Redis URL)
```

The defaults work out of the box with SQLite and a local Redis on port 6379.

### 4. Start Redis

```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 redis:7

# Or install Redis natively and run:
redis-server
```

---

## Running the Application

You need **two** processes running simultaneously:

### Terminal 1 - FastAPI server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Celery worker

```bash
# Windows
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo

# macOS / Linux
celery -A app.celery_app.celery_app worker --loglevel=info
```

The API will be available at http://localhost:8000.
Interactive docs: http://localhost:8000/docs

---

## Running Tests

Tests use an in-memory SQLite database and run Celery tasks **synchronously** (no Redis or worker required).

```bash
pytest
```

To see verbose output:

```bash
pytest -v
```

To run a specific test file:

```bash
pytest tests/test_certificate_generation.py -v
```

---

## API Reference

### POST /jobs - Create a certificate generation job

**Request body:**

```json
{
  "event_name": "Python Bootcamp 2025",
  "issuer_name": "Tech Academy",
  "issue_date": "2025-06-15",
  "recipients": [
    { "name": "Alice Smith", "email": "alice@example.com" },
    { "name": "Bob Jones",   "email": "bob@example.com" }
  ]
}
```

**Response (202 Accepted):**

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "pending",
  "total_recipients": 2,
  "message": "Job created successfully. 2 certificate(s) are being generated in the background..."
}
```

---

### GET /jobs/{job_id} - Get job status and progress

**Response (200 OK):**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "event_name": "Python Bootcamp 2025",
  "issuer_name": "Tech Academy",
  "issue_date": "2025-06-15",
  "status": "completed",
  "total": 2,
  "successful": 2,
  "failed": 0,
  "certificates": [
    {
      "id": "cert-uuid-1",
      "recipient_name": "Alice Smith",
      "recipient_email": "alice@example.com",
      "status": "success",
      "error_message": null
    }
  ]
}
```

**Job statuses:** pending -> processing -> completed / failed
**Certificate statuses:** pending -> success / failed

---

### GET /jobs/{job_id}/certificates/{cert_id}/download - Download a PDF

Returns the generated PDF file with Content-Type: application/pdf.
Returns 409 Conflict if the certificate is not yet ready, 404 if not found.

---

### GET /health - Liveness probe

```json
{ "status": "ok", "version": "1.0.0" }
```

---

## Design Decisions

### Why Background Processing (Celery + Redis)?

Generating PDFs for hundreds of recipients can take significant time. A synchronous approach would block the HTTP connection until all PDFs are done - a poor user experience and brittle under load. With Celery:

- The API responds **immediately** with a `job_id` (202 Accepted).
- The client **polls** `GET /jobs/{job_id}` at its own pace.
- The worker can be **scaled horizontally** by adding more Celery workers.
- **Broker durability**: Redis persists tasks so they survive a worker restart.

### Why one task per job (not one per certificate)?

One Celery task is dispatched per job. Inside the task, each certificate is generated in a loop. This avoids Redis overhead from dispatching hundreds of small tasks and makes job-level status tracking simpler (one task owns the entire job's lifecycle).

For very high-throughput scenarios, this could be changed to a Celery Chord (fan-out + aggregation) without changing the API surface.

### Failure Isolation

Each certificate's generation is wrapped in its own try/except block. A failure records status=failed and error_message for that certificate, then continues to the next. The job is only marked FAILED if **every** certificate failed; otherwise it is COMPLETED.

### Why SQLite?

SQLite is ideal for this assignment: zero configuration, file-based, ACID-compliant. The code is database-agnostic via SQLAlchemy, so switching to PostgreSQL requires only changing DATABASE_URL in .env.

### Why ReportLab?

ReportLab is the de-facto standard Python PDF library: mature, pure-Python, well-documented. It gives precise control over layout without requiring external system dependencies (unlike WeasyPrint which needs a browser engine).

### Certificate Template Design

A single hardcoded A4-landscape template is used. It consists of:
- Dark blue header band with the issuer name
- Gold decorative double border
- "Certificate of Completion" title
- Recipient name in large italic font
- Event name and issue date in the body
- Certificate ID in the footer for verification

### Validation

Pydantic v2 handles all input validation. Invalid requests return a structured 422 Unprocessable Entity with field-level error details before any database write occurs.
