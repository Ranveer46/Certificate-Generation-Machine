"""
Tests: Job status / progress tracking and individual certificate failure handling.
"""

import pytest
from unittest.mock import patch


VALID_PAYLOAD = {
    "event_name": "Leadership Summit",
    "issuer_name": "Global Corp",
    "issue_date": "2025-09-01",
    "recipients": [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
        {"name": "Carol", "email": "carol@example.com"},
    ],
}


class TestJobStatus:
    def test_get_status_404_for_unknown_job(self, client):
        resp = client.get("/jobs/nonexistent-job-id")
        assert resp.status_code == 404

    def test_get_status_contains_required_fields(self, client):
        create_resp = client.post("/jobs", json=VALID_PAYLOAD)
        job_id = create_resp.json()["job_id"]

        resp = client.get(f"/jobs/{job_id}")
        assert resp.status_code == 200
        data = resp.json()

        required_fields = {"id", "event_name", "issuer_name", "issue_date", "status", "total", "successful", "failed", "certificates"}
        assert required_fields.issubset(data.keys())

    def test_job_total_matches_recipient_count(self, client):
        create_resp = client.post("/jobs", json=VALID_PAYLOAD)
        job_id = create_resp.json()["job_id"]

        status_resp = client.get(f"/jobs/{job_id}")
        assert status_resp.json()["total"] == 3

    def test_job_certificates_list_length(self, client):
        create_resp = client.post("/jobs", json=VALID_PAYLOAD)
        job_id = create_resp.json()["job_id"]

        status_resp = client.get(f"/jobs/{job_id}")
        assert len(status_resp.json()["certificates"]) == 3

    def test_completed_job_has_correct_counters(self, client):
        """All valid recipients → successful == total, failed == 0."""
        create_resp = client.post("/jobs", json=VALID_PAYLOAD)
        job_id = create_resp.json()["job_id"]

        status_resp = client.get(f"/jobs/{job_id}")
        data = status_resp.json()
        assert data["status"] == "completed"
        assert data["successful"] == 3
        assert data["failed"] == 0

    def test_certificate_status_is_success(self, client):
        create_resp = client.post("/jobs", json=VALID_PAYLOAD)
        job_id = create_resp.json()["job_id"]

        status_resp = client.get(f"/jobs/{job_id}")
        certs = status_resp.json()["certificates"]
        assert all(c["status"] == "success" for c in certs)

    def test_event_name_reflected_in_status(self, client):
        create_resp = client.post("/jobs", json=VALID_PAYLOAD)
        job_id = create_resp.json()["job_id"]

        status_resp = client.get(f"/jobs/{job_id}")
        assert status_resp.json()["event_name"] == "Leadership Summit"


class TestIndividualCertificateFailure:
    def test_one_failure_does_not_stop_others(self, client):
        """
        Simulate a failure on the second recipient by patching generate_certificate_pdf
        to raise on a specific name. The other two should still succeed.
        """
        original_payload = {
            "event_name": "Failure Test Event",
            "issuer_name": "Test Org",
            "issue_date": "2025-10-01",
            "recipients": [
                {"name": "Good User 1", "email": "good1@example.com"},
                {"name": "Bad User",   "email": "bad@example.com"},
                {"name": "Good User 2", "email": "good2@example.com"},
            ],
        }

        def mock_generate(cert_id, recipient_name, **kwargs):
            if recipient_name == "Bad User":
                raise RuntimeError("Simulated generation failure")
            from app.certificate_generator import generate_certificate_pdf as real_gen
            return real_gen(cert_id=cert_id, recipient_name=recipient_name, **kwargs)

        with patch("app.tasks.generate_certificate_pdf", side_effect=mock_generate):
            create_resp = client.post("/jobs", json=original_payload)

        job_id = create_resp.json()["job_id"]
        status_resp = client.get(f"/jobs/{job_id}")
        data = status_resp.json()

        assert data["status"] == "completed"  # job completed despite one failure
        assert data["successful"] == 2
        assert data["failed"] == 1

    def test_failed_certificate_has_error_message(self, client):
        payload = {
            "event_name": "Error Test",
            "issuer_name": "Org",
            "issue_date": "2025-11-01",
            "recipients": [
                {"name": "Fail This", "email": "fail@example.com"},
                {"name": "Pass This", "email": "pass@example.com"},
            ],
        }

        def mock_generate(cert_id, recipient_name, **kwargs):
            if recipient_name == "Fail This":
                raise ValueError("Bad data")
            from app.certificate_generator import generate_certificate_pdf as real_gen
            return real_gen(cert_id=cert_id, recipient_name=recipient_name, **kwargs)

        with patch("app.tasks.generate_certificate_pdf", side_effect=mock_generate):
            create_resp = client.post("/jobs", json=payload)

        job_id = create_resp.json()["job_id"]
        status_resp = client.get(f"/jobs/{job_id}")
        certs = status_resp.json()["certificates"]

        failed_certs = [c for c in certs if c["status"] == "failed"]
        assert len(failed_certs) == 1
        assert failed_certs[0]["error_message"] is not None
        assert "Bad data" in failed_certs[0]["error_message"]

    def test_all_fail_marks_job_as_failed(self, client):
        payload = {
            "event_name": "All Fail Event",
            "issuer_name": "Org",
            "issue_date": "2025-12-01",
            "recipients": [
                {"name": "User A", "email": "a@example.com"},
                {"name": "User B", "email": "b@example.com"},
            ],
        }

        with patch("app.tasks.generate_certificate_pdf", side_effect=RuntimeError("always fails")):
            create_resp = client.post("/jobs", json=payload)

        job_id = create_resp.json()["job_id"]
        status_resp = client.get(f"/jobs/{job_id}")
        data = status_resp.json()

        assert data["status"] == "failed"
        assert data["successful"] == 0
        assert data["failed"] == 2
