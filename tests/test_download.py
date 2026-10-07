"""
Tests: Downloading / retrieving generated certificates.
"""

import pytest


VALID_PAYLOAD = {
    "event_name": "Download Test Event",
    "issuer_name": "Download Org",
    "issue_date": "2025-04-01",
    "recipients": [
        {"name": "Download User", "email": "download@example.com"},
    ],
}


class TestDownloadCertificate:
    def _create_and_get_ids(self, client):
        """Helper: create a job, return (job_id, cert_id)."""
        create_resp = client.post("/jobs", json=VALID_PAYLOAD)
        job_id = create_resp.json()["job_id"]
        status_resp = client.get(f"/jobs/{job_id}")
        cert_id = status_resp.json()["certificates"][0]["id"]
        return job_id, cert_id

    def test_download_returns_200(self, client):
        job_id, cert_id = self._create_and_get_ids(client)
        resp = client.get(f"/jobs/{job_id}/certificates/{cert_id}/download")
        assert resp.status_code == 200

    def test_download_content_type_is_pdf(self, client):
        job_id, cert_id = self._create_and_get_ids(client)
        resp = client.get(f"/jobs/{job_id}/certificates/{cert_id}/download")
        assert "application/pdf" in resp.headers["content-type"]

    def test_download_content_is_valid_pdf(self, client):
        job_id, cert_id = self._create_and_get_ids(client)
        resp = client.get(f"/jobs/{job_id}/certificates/{cert_id}/download")
        assert resp.content[:4] == b"%PDF"

    def test_download_wrong_job_id_returns_404(self, client):
        job_id, cert_id = self._create_and_get_ids(client)
        resp = client.get(f"/jobs/wrong-job-id/certificates/{cert_id}/download")
        assert resp.status_code == 404

    def test_download_wrong_cert_id_returns_404(self, client):
        job_id, _ = self._create_and_get_ids(client)
        resp = client.get(f"/jobs/{job_id}/certificates/wrong-cert-id/download")
        assert resp.status_code == 404

    def test_download_pending_certificate_returns_409(self, client):
        """A certificate that hasn't been generated yet should return 409 Conflict."""
        from unittest.mock import patch
        payload = {
            "event_name": "Pending Test",
            "issuer_name": "Org",
            "issue_date": "2025-05-01",
            "recipients": [{"name": "Pending User", "email": "pending@example.com"}],
        }

        # Block generation so cert stays PENDING
        with patch("app.tasks.generate_certificate_pdf", side_effect=RuntimeError("blocked")):
            create_resp = client.post("/jobs", json=payload)

        job_id = create_resp.json()["job_id"]
        status_resp = client.get(f"/jobs/{job_id}")
        cert_id = status_resp.json()["certificates"][0]["id"]

        resp = client.get(f"/jobs/{job_id}/certificates/{cert_id}/download")
        assert resp.status_code == 409

    def test_download_cert_from_wrong_job_returns_404(self, client):
        """cert_id exists but belongs to a different job."""
        # Create job 1
        job1_id, cert1_id = self._create_and_get_ids(client)
        # Create job 2
        job2_id, cert2_id = self._create_and_get_ids(client)

        # Try to download cert from job1 using job2's ID
        resp = client.get(f"/jobs/{job2_id}/certificates/{cert1_id}/download")
        assert resp.status_code == 404
