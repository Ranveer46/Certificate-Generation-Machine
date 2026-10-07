# 🎓 Bulk Certificate Generator — Backend System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Celery](https://img.shields.io/badge/Celery-5.4+-37814A.svg?logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![Redis](https://img.shields.io/badge/Redis-7.0+-DC382D.svg?logo=redis&logoColor=white)](https://redis.io)
[![Tests](https://img.shields.io/badge/Tests-37%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

A production-grade, asynchronous bulk PDF certificate generation backend built with **FastAPI**, **Celery**, **Redis**, **SQLAlchemy**, and **ReportLab**. Designed to accept large batches of participants in a single non-blocking request, track granular job and per-recipient progress in real time, isolate individual failures, and serve cryptographic-style vector-rendered luxury PDF certificates.

---

## 🌐 Live Deployment & Interactive Documentation

The service is fully deployed and accessible in the cloud:

| Resource | Live Link |
|---|---|
| **Live Interactive Swagger UI** | [https://certificate-generation-machine.onrender.com/docs](https://certificate-generation-machine.onrender.com/docs) |
| **Alternative ReDoc UI** | [https://certificate-generation-machine.onrender.com/redoc](https://certificate-generation-machine.onrender.com/redoc) |
| **Health Check Endpoint** | [https://certificate-generation-machine.onrender.com/health](https://certificate-generation-machine.onrender.com/health) |
| **GitHub Repository** | [https://github.com/Ranveer46/Certificate-Generation-Machine](https://github.com/Ranveer46/Certificate-Generation-Machine) |

---

## 📑 Table of Contents

1. [Assignment Requirements Coverage](#-assignment-requirements-coverage)
2. [Architecture & System Flow](#-architecture--system-flow)
3. [Certificate Template Design](#-certificate-template-design)
4. [Quickstart Guide (Testing the Live API)](#-quickstart-guide-testing-the-live-api)
5. [Local Setup & Development](#-local-setup--development)
6. [Docker & Containerized Deployment](#-docker--containerized-deployment)
7. [Running the Test Suite](#-running-the-test-suite)
8. [API Reference & Endpoints](#-api-reference--endpoints)
9. [Key Design Decisions & Architecture Trade-offs](#-key-design-decisions--architecture-trade-offs)
10. [Project Structure](#-project-structure)

---

## ✅ Assignment Requirements Coverage

| Requirement | Implementation Detail | Status |
|---|---|:---:|
| **Bulk API Endpoint** | `POST /jobs` accepts unlimited recipients in one batch request. Responds immediately with `202 Accepted` and a `job_id`. | ✅ Complete |
| **Input Validation** | Pydantic v2 validates event info, dates, and email formats via `email-validator`. Returns structured `422 Unprocessable Entity` on bad payloads. | ✅ Complete |
| **Predefined Template** | Single, elegant A4-landscape vector template featuring warm parchment background, guilloche rosette watermark, 32-point embossed gold seal, and cursive signatures. | ✅ Complete |
| **Progress & Status Tracking** | `GET /jobs/{job_id}` returns overall status (`pending` → `processing` → `completed` / `failed`), total/successful/failed counts, and per-certificate breakdown. | ✅ Complete |
| **Failure Isolation** | Each certificate generation is wrapped in isolated exception blocks; one corrupted recipient never blocks or fails the remaining certificates in the job. | ✅ Complete |
| **Certificate Retrieval** | `GET /jobs/{job_id}/certificates/{cert_id}/download` serves the generated PDF with `Content-Type: application/pdf` and sanitized download filenames. | ✅ Complete |
| **Automated Test Suite** | 37 comprehensive unit and integration tests covering job dispatch, validation, ReportLab rendering, polling, failure handling, and downloads. | ✅ Complete |

---

## 🏛️ Architecture & System Flow

```
                      +---------------------------------------+
                      |               Client                  |
                      +---------------------------------------+
                        |                 ^                 ^
       1. POST /jobs    |                 |                 | 4. GET /download
      (Bulk Recipients) |                 | 3. Poll Status  | (Retrieve PDF)
                        v                 |                 |
             +--------------------+       |                 |
             |   FastAPI (HTTP)   |-------+                 |
             +--------------------+                         |
               |                |                           |
  Persist Job  |                | Dispatch Task             |
  & Certs      |                | process_certificate_job   |
               v                v                           |
         +----------+     +-------------------+             |
         | SQLite / |     |   Redis (Broker)  |             |
         | Postgres |     +-------------------+             |
         +----------+               |                       |
               ^                    v                       |
               |          +-------------------+             |
               | Updates  |   Celery Worker   |             |
               +----------|  (Background Task)|             |
                          +-------------------+             |
                                    |                       |
                             Generates PDF                  |
                                    v                       |
                          +-------------------+             |
                          |     ReportLab     |             |
                          |   PDF Generator   |             |
                          +-------------------+             |
                                    |                       |
                             Saves to Disk                  |
                                    v                       |
                          +-------------------+             |
                          | /generated_certs/ |-------------+
                          +-------------------+
```

### Lifecycle State Machine
- **Job Status:** `PENDING` ➔ `PROCESSING` ➔ `COMPLETED` *(or `FAILED` if all certificates fail)*
- **Certificate Status:** `PENDING` ➔ `SUCCESS` *(with `file_path`)* or `FAILED` *(with `error_message`)*

---

## 🎨 Certificate Template Design

Rather than basic solid color bands, the PDF generator produces an **executive luxury academic credential** rendered purely through vector operations on ReportLab Canvas:

- **A4 Landscape Canvas:** Crisp geometry with zero quality loss regardless of zoom level.
- **Warm Ivory Parchment (`#FCFAF6`):** Authentic academic background texture.
- **Guilloche Security Watermark:** Intricate mathematical rosette curves and concentric watermark rings drawn behind the text.
- **Art Deco Multi-Tier Frame:** 3 nested gold-bordered bands with bevelled 45-degree corner facets and solid gold diamond gems.
- **Institutional Crest Emblem:** Top heraldic shield with golden stars, laurel sprig arcs, and tracked typography.
- **Bespoke Calligraphy Accent:** Recipient name displayed in high-contrast `Times-BoldItalic` with a diamond-studded gold divider bar.
- **Embossed 32-Point Gold Medallion Seal:** Scalloped starburst badge with embossed rings and dual flowing satin ribbons with notched fishtail ends.
- **Dual Executive Signatures:** Hand-drawn vector cursive fountain-pen signature strokes with institutional titles.
- **Verification ID Pill:** Tamper-evident credential pill containing the certificate UUID and microprint security baseline.

---

## 🚀 Quickstart Guide (Testing the Live API)

You can test the entire workflow live in your browser using **Swagger UI**:

👉 **[Open Live Swagger UI](https://certificate-generation-machine.onrender.com/docs)**

### Step 1 — Submit a Bulk Generation Job (`POST /jobs`)
Send a batch of recipients:
```json
{
  "event_name": "Executive AI & Cloud Summit 2026",
  "issuer_name": "Stanford Technology Institute",
  "issue_date": "2026-10-07",
  "recipients": [
    {
      "name": "Alexander Vance",
      "email": "alexander.vance@example.com"
    },
    {
      "name": "Priya Mehta",
      "email": "priya.mehta@example.com"
    },
    {
      "name": "Marcus Aurelius Chen",
      "email": "marcus.chen@example.com"
    }
  ]
}
```
**Response (`202 Accepted`):**
```json
{
  "job_id": "6a1df6c1-d377-4537-bf1a-870dd82fa447",
  "status": "pending",
  "total_recipients": 3,
  "message": "Job created successfully. 3 certificate(s) are being generated in the background. Poll GET /jobs/{job_id} to check progress."
}
```

### Step 2 — Check Progress (`GET /jobs/{job_id}`)
Pass the `job_id` to inspect real-time progress:
```json
{
  "id": "6a1df6c1-d377-4537-bf1a-870dd82fa447",
  "event_name": "Executive AI & Cloud Summit 2026",
  "issuer_name": "Stanford Technology Institute",
  "issue_date": "2026-10-07",
  "status": "completed",
  "total": 3,
  "successful": 3,
  "failed": 0,
  "certificates": [
    {
      "id": "978ab534-9316-47b2-beff-3df9283b77c5",
      "recipient_name": "Alexander Vance",
      "recipient_email": "alexander.vance@example.com",
      "status": "success",
      "error_message": null
    }
  ]
}
```

### Step 3 — Download the Generated Certificate (`GET /jobs/{job_id}/certificates/{cert_id}/download`)
Paste the `job_id` and `cert_id` to download the high-resolution vector PDF.

---

## 💻 Local Setup & Development

### Prerequisites
- Python 3.10+
- Redis (native service or Docker)

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/Ranveer46/Certificate-Generation-Machine.git
cd Certificate-Generation-Machine

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root (or copy `.env.example`):
```env
APP_NAME=Bulk Certificate Generator
APP_VERSION=1.0.0
DEBUG=false
DATABASE_URL=sqlite:///./certificates.db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CERTIFICATES_DIR=generated_certificates
```

### 4. Run the Application

You need Redis, the FastAPI web server, and the Celery background worker running:

**Terminal 1 — Start Redis:**
```bash
docker run -d -p 6379:6379 redis:7
# Or native: redis-server
```

**Terminal 2 — Start FastAPI:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 — Start Celery Worker:**
```bash
# Windows:
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo

# Linux / macOS:
celery -A app.celery_app.celery_app worker --loglevel=info
```

Interactive documentation is available at: `http://localhost:8000/docs`

---

## 🐳 Docker & Containerized Deployment

Run the complete multi-container architecture (FastAPI + Redis + Celery Worker + persistent volumes) with a single command:

```bash
docker compose up --build -d
```

- **API:** Accessible at `http://localhost:8000/docs`
- **Redis:** Running on port `6379`
- **Worker:** Processing background tasks with auto-restart enabled
- **Volumes:** Database and PDF files are persisted across container restarts.

To tear down:
```bash
docker compose down
```

---

## 🧪 Running the Test Suite

The project features **37 automated pytest tests** covering:
- Job submission & HTTP 202 acceptance
- Input validation (empty fields, malformed emails, date checks)
- ReportLab PDF byte integrity, size constraints, and custom metadata
- Status polling and counter accuracy
- Isolated failure handling (corrupted recipients do not break batches)
- Certificate file download validations and 409 Conflict handling for pending jobs

Tests run against an in-memory SQLite database with Celery tasks executing in **eager mode** (`CELERY_TASK_ALWAYS_EAGER=true`), requiring **no running Redis server**:

```bash
pytest
```

For verbose output with test names:
```bash
pytest -v
```

---

## 📖 API Reference & Endpoints

### 1. `POST /jobs` — Create Bulk Certificate Job
- **Status Code:** `202 Accepted` (on success) | `422 Unprocessable Entity` (validation error)
- **Request Body:**
```json
{
  "event_name": "string (min 1 char)",
  "issuer_name": "string (min 1 char)",
  "issue_date": "YYYY-MM-DD",
  "recipients": [
    {
      "name": "string (min 1 char)",
      "email": "valid-email@domain.com"
    }
  ]
}
```

### 2. `GET /jobs/{job_id}` — Get Job Progress & Details
- **Status Code:** `200 OK` | `404 Not Found`
- Returns counters (`total`, `successful`, `failed`), overall status, and each recipient's certificate ID, individual status, and error details if failed.

### 3. `GET /jobs/{job_id}/certificates/{cert_id}/download` — Download PDF
- **Status Code:** `200 OK` (`application/pdf`) | `404 Not Found` | `409 Conflict` (if still pending)
- Downloads the generated certificate PDF file with a sanitized name: `{Recipient_Name}.pdf`.

### 4. `GET /health` — Liveness & Readiness Probe
- **Status Code:** `200 OK`
- Response: `{"status": "ok", "version": "1.0.0"}`

---

## 💡 Key Design Decisions & Architecture Trade-offs

### 1. Asynchronous Task Processing (Celery + Redis)
- **Why not synchronous?** Generating PDFs involves canvas drawing, font rendering, and disk I/O (~6ms per PDF). Generating 1,000 certificates synchronously would hold an HTTP connection open for 6+ seconds, leading to browser timeouts, proxy drops, and server thread exhaustion.
- **Why Celery?** Celery is battle-tested, durable, and provides out-of-the-box support for retries, rate-limiting, and distributed worker scaling across multiple machines.

### 2. Job-Level Task Dispatch vs. Task-Per-Certificate
- **Decision:** One Celery task is dispatched per *job*, and it iterates over recipients internally.
- **Rationale:** Disagreeing with dispatching 5,000 micro-tasks to Redis for a 5,000-person event prevents Redis connection churn and scheduling overhead. Status tracking remains atomic and straightforward.
- **Scaling Path:** For enterprise scale (>50,000 recipients), this architecture seamlessly converts into a Celery `chord` (fan-out chunks to worker pools with a final aggregation callback) without altering the client-facing API.

### 3. Failure Isolation
- In `app/tasks.py`, each individual certificate generation is enclosed in an isolated `try...except` block.
- If recipient #12 fails (e.g., corrupted string encoding), the failure is logged and recorded in the database with an explicit `error_message`, while recipients #13 through #500 continue without interruption.
- The overall job is only marked `FAILED` if **zero** certificates succeeded; otherwise, it finishes as `COMPLETED`.

### 4. Pure Vector PDF Generation (ReportLab)
- **Why ReportLab over HTML-to-PDF tools (WeasyPrint / Puppeteer)?**
  - High performance (~0.005 seconds per certificate).
  - Pure Python without requiring heavy external headless browsers or complex C-dependencies (Chromium/Cairo).
  - Crisp, mathematically perfect vector lines that never pixelate on high-resolution prints.

### 5. Relational Database with SQLAlchemy
- Clean separation between parent `CertificateJob` (1) and child `Certificate` (N) records.
- Database agnostic: Defaults to SQLite for zero-config simplicity, while fully compatible with PostgreSQL in production by modifying `DATABASE_URL`.

---

## 📁 Project Structure

```
Certificate-Generation-Machine/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application factory & lifespan
│   ├── config.py                 # Pydantic BaseSettings & configuration
│   ├── database.py               # SQLAlchemy database engine & session factory
│   ├── models.py                 # ORM models (CertificateJob, Certificate)
│   ├── schemas.py                # Pydantic validation schemas
│   ├── routes.py                 # REST API route handlers
│   ├── certificate_generator.py  # ReportLab vector certificate rendering logic
│   ├── celery_app.py             # Celery instance & broker configuration
│   └── tasks.py                  # Celery background job processing logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Shared fixtures (in-memory SQLite, eager Celery)
│   ├── test_create_job.py        # Job creation & validation tests
│   ├── test_certificate_generation.py  # ReportLab unit tests
│   ├── test_job_status.py        # Progress polling & failure isolation tests
│   └── test_download.py          # PDF download route tests
├── Dockerfile                    # Production container image
├── docker-compose.yml            # Multi-container orchestration (API + Worker + Redis)
├── render.yaml                   # Infrastructure-as-code cloud blueprint
├── requirements.txt              # Production Python dependencies
├── pytest.ini                    # Pytest configuration
├── .env.example                  # Environment variable template
└── README.md                     # Comprehensive project documentation
```
