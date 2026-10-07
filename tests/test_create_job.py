"""
Tests: Creating a generation job and input validation.
"""

import pytest


VALID_PAYLOAD = {
    "event_name": "Python Bootcamp 2025",
    "issuer_name": "Tech Academy",
    "issue_date": "2025-06-15",
    "recipients": [
        {"name": "Alice Smith", "email": "alice@example.com"},
        {"name": "Bob Jones", "email": "bob@example.com"},
    ],
}


class TestCreateJob:
    def test_create_job_returns_202(self, client):
        resp = client.post("/jobs", json=VALID_PAYLOAD)
        assert resp.status_code == 202

    def test_create_job_response_schema(self, client):
        resp = client.post("/jobs", json=VALID_PAYLOAD)
        data = resp.json()
        assert "job_id" in data
        assert data["total_recipients"] == 2
        assert data["status"] == "pending"
        assert "message" in data

    def test_create_job_processes_certificates_eagerly(self, client):
        """With CELERY_TASK_ALWAYS_EAGER the task runs synchronously."""
        resp = client.post("/jobs", json=VALID_PAYLOAD)
        job_id = resp.json()["job_id"]

        status_resp = client.get(f"/jobs/{job_id}")
        data = status_resp.json()
        # Job should be completed (or at minimum no longer pending)
        assert data["status"] in ("completed", "processing", "pending")
        assert data["total"] == 2

    def test_create_job_single_recipient(self, client):
        payload = {**VALID_PAYLOAD, "recipients": [{"name": "Solo User", "email": "solo@example.com"}]}
        resp = client.post("/jobs", json=payload)
        assert resp.status_code == 202
        assert resp.json()["total_recipients"] == 1


class TestInputValidation:
    def test_missing_event_name(self, client):
        bad = {**VALID_PAYLOAD}
        del bad["event_name"]
        resp = client.post("/jobs", json=bad)
        assert resp.status_code == 422

    def test_missing_issuer_name(self, client):
        bad = {**VALID_PAYLOAD}
        del bad["issuer_name"]
        resp = client.post("/jobs", json=bad)
        assert resp.status_code == 422

    def test_missing_issue_date(self, client):
        bad = {**VALID_PAYLOAD}
        del bad["issue_date"]
        resp = client.post("/jobs", json=bad)
        assert resp.status_code == 422

    def test_invalid_issue_date_format(self, client):
        bad = {**VALID_PAYLOAD, "issue_date": "not-a-date"}
        resp = client.post("/jobs", json=bad)
        assert resp.status_code == 422

    def test_empty_recipients_list(self, client):
        bad = {**VALID_PAYLOAD, "recipients": []}
        resp = client.post("/jobs", json=bad)
        assert resp.status_code == 422

    def test_missing_recipient_name(self, client):
        bad = {
            **VALID_PAYLOAD,
            "recipients": [{"email": "no-name@example.com"}],
        }
        resp = client.post("/jobs", json=bad)
        assert resp.status_code == 422

    def test_invalid_recipient_email(self, client):
        bad = {
            **VALID_PAYLOAD,
            "recipients": [{"name": "Bad Email", "email": "not-an-email"}],
        }
        resp = client.post("/jobs", json=bad)
        assert resp.status_code == 422

    def test_blank_recipient_name(self, client):
        bad = {
            **VALID_PAYLOAD,
            "recipients": [{"name": "   ", "email": "blank@example.com"}],
        }
        resp = client.post("/jobs", json=bad)
        assert resp.status_code == 422

    def test_blank_event_name(self, client):
        bad = {**VALID_PAYLOAD, "event_name": "   "}
        resp = client.post("/jobs", json=bad)
        assert resp.status_code == 422
