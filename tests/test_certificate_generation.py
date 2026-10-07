"""
Tests: Certificate PDF generation (unit tests – no HTTP layer).
"""

import os
import tempfile
from pathlib import Path

import pytest

from app.certificate_generator import generate_certificate_pdf


@pytest.fixture()
def output_dir(tmp_path, monkeypatch):
    """Redirect generated PDFs to a tmp directory."""
    from app import certificate_generator as gen_module
    from app import config as cfg_module
    monkeypatch.setattr(cfg_module.settings, "CERTIFICATES_DIR", str(tmp_path))
    monkeypatch.setattr(gen_module.settings, "CERTIFICATES_DIR", str(tmp_path))
    return tmp_path


class TestCertificateGeneration:
    def test_generates_pdf_file(self, output_dir):
        path = generate_certificate_pdf(
            cert_id="test-cert-001",
            recipient_name="Jane Doe",
            recipient_email="jane@example.com",
            event_name="Test Event",
            issuer_name="Test Org",
            issue_date="2025-01-01",
        )
        assert Path(path).exists()
        assert path.endswith(".pdf")

    def test_pdf_is_non_empty(self, output_dir):
        path = generate_certificate_pdf(
            cert_id="test-cert-002",
            recipient_name="John Smith",
            recipient_email="john@example.com",
            event_name="Demo Course",
            issuer_name="Demo Org",
            issue_date="2025-03-15",
        )
        assert Path(path).stat().st_size > 1000  # PDF should be at least 1 KB

    def test_pdf_starts_with_pdf_header(self, output_dir):
        path = generate_certificate_pdf(
            cert_id="test-cert-003",
            recipient_name="Test User",
            recipient_email="test@example.com",
            event_name="Course X",
            issuer_name="Org Y",
            issue_date="2025-06-01",
        )
        with open(path, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"

    def test_filename_uses_cert_id(self, output_dir):
        cert_id = "my-unique-cert-id-123"
        path = generate_certificate_pdf(
            cert_id=cert_id,
            recipient_name="Someone",
            recipient_email="someone@example.com",
            event_name="Event",
            issuer_name="Org",
            issue_date="2025-07-01",
        )
        assert cert_id in Path(path).name

    def test_blank_recipient_name_raises(self, output_dir):
        with pytest.raises(ValueError, match="recipient_name"):
            generate_certificate_pdf(
                cert_id="err-cert-001",
                recipient_name="   ",
                recipient_email="x@example.com",
                event_name="Event",
                issuer_name="Org",
                issue_date="2025-07-01",
            )

    def test_blank_event_name_raises(self, output_dir):
        with pytest.raises(ValueError, match="event_name"):
            generate_certificate_pdf(
                cert_id="err-cert-002",
                recipient_name="Someone",
                recipient_email="x@example.com",
                event_name="   ",
                issuer_name="Org",
                issue_date="2025-07-01",
            )

    def test_multiple_certificates_unique_files(self, output_dir):
        paths = []
        for i in range(3):
            p = generate_certificate_pdf(
                cert_id=f"multi-cert-{i}",
                recipient_name=f"User {i}",
                recipient_email=f"user{i}@example.com",
                event_name="Batch Event",
                issuer_name="Batch Org",
                issue_date="2025-08-01",
            )
            paths.append(p)
        assert len(set(paths)) == 3  # all paths are distinct
