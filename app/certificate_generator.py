"""
Certificate PDF generation using ReportLab.

A single predefined template is used for all certificates:
  - A4 landscape orientation
  - Decorative border and background
  - Organisation / event details from the job
  - Recipient name prominently displayed
"""

import os
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.enums import TA_CENTER

from app.config import settings


# ---------------------------------------------------------------------------
# Colours used in the template
# ---------------------------------------------------------------------------
GOLD = colors.HexColor("#C9A84C")
DARK_BLUE = colors.HexColor("#1A2B4A")
LIGHT_GOLD = colors.HexColor("#F5E9C8")
WHITE = colors.white
MID_BLUE = colors.HexColor("#2E4A7A")


def _ensure_output_dir() -> Path:
    out = Path(settings.CERTIFICATES_DIR)
    out.mkdir(parents=True, exist_ok=True)
    return out


def _draw_border(c: rl_canvas.Canvas, width: float, height: float) -> None:
    """Draw a decorative double-line border around the page."""
    margin = 15 * mm
    inner_margin = 18 * mm

    # Outer border
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    # Inner border
    c.setLineWidth(1)
    c.rect(inner_margin, inner_margin, width - 2 * inner_margin, height - 2 * inner_margin)

    # Corner ornaments (small filled squares)
    sq = 4 * mm
    corners = [
        (margin - sq / 2, margin - sq / 2),
        (width - margin - sq / 2, margin - sq / 2),
        (margin - sq / 2, height - margin - sq / 2),
        (width - margin - sq / 2, height - margin - sq / 2),
    ]
    c.setFillColor(GOLD)
    for x, y in corners:
        c.rect(x, y, sq, sq, fill=1, stroke=0)


def _draw_background(c: rl_canvas.Canvas, width: float, height: float) -> None:
    """Draw a subtle gradient-like background using rectangles."""
    c.setFillColor(colors.HexColor("#FAFAF7"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Header band
    c.setFillColor(DARK_BLUE)
    c.rect(0, height - 60 * mm, width, 60 * mm, fill=1, stroke=0)

    # Footer band
    c.setFillColor(DARK_BLUE)
    c.rect(0, 0, width, 25 * mm, fill=1, stroke=0)


def _draw_header(c: rl_canvas.Canvas, width: float, height: float, issuer_name: str) -> None:
    """Draw the header with organisation name."""
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 30 * mm, issuer_name.upper())

    c.setFont("Helvetica", 12)
    c.setFillColor(GOLD)
    c.drawCentredString(width / 2, height - 42 * mm, "─" * 60)


def _draw_body(
    c: rl_canvas.Canvas,
    width: float,
    height: float,
    recipient_name: str,
    event_name: str,
    issue_date: str,
) -> None:
    """Draw the main certificate body content."""
    mid_y = height / 2

    # "Certificate of Completion" title
    c.setFillColor(DARK_BLUE)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width / 2, mid_y + 55 * mm, "Certificate of Completion")

    # Separator
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    sep_w = 120 * mm
    c.line((width - sep_w) / 2, mid_y + 48 * mm, (width + sep_w) / 2, mid_y + 48 * mm)

    # Presentation line
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, mid_y + 38 * mm, "This is to certify that")

    # Recipient name
    c.setFillColor(MID_BLUE)
    c.setFont("Helvetica-BoldOblique", 40)
    c.drawCentredString(width / 2, mid_y + 18 * mm, recipient_name)

    # Underline below name
    name_width = c.stringWidth(recipient_name, "Helvetica-BoldOblique", 40)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(
        (width - name_width) / 2,
        mid_y + 14 * mm,
        (width + name_width) / 2,
        mid_y + 14 * mm,
    )

    # Completion text
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, mid_y + 4 * mm, "has successfully completed")

    # Event name
    c.setFillColor(DARK_BLUE)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, mid_y - 10 * mm, event_name)

    # Date
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawCentredString(width / 2, mid_y - 22 * mm, f"Issued on: {issue_date}")


def _draw_footer(c: rl_canvas.Canvas, width: float, height: float, cert_id: str) -> None:
    """Draw footer with certificate ID."""
    c.setFillColor(LIGHT_GOLD)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 10 * mm, f"Certificate ID: {cert_id}")


def generate_certificate_pdf(
    cert_id: str,
    recipient_name: str,
    recipient_email: str,
    event_name: str,
    issuer_name: str,
    issue_date: str,
) -> str:
    """
    Generate a PDF certificate and return the file path.

    Args:
        cert_id: Unique certificate ID (used for filename and printed on the cert).
        recipient_name: Full name of the recipient.
        recipient_email: Email (used for subfolder organisation, not printed).
        event_name: Name of the event/course.
        issuer_name: Issuing organisation.
        issue_date: Date string (YYYY-MM-DD).

    Returns:
        Absolute path to the generated PDF file.

    Raises:
        ValueError: If any required field is empty.
        Exception: Re-raises any ReportLab errors.
    """
    if not recipient_name.strip():
        raise ValueError("recipient_name must not be blank")
    if not event_name.strip():
        raise ValueError("event_name must not be blank")
    if not issuer_name.strip():
        raise ValueError("issuer_name must not be blank")

    out_dir = _ensure_output_dir()
    file_name = f"{cert_id}.pdf"
    file_path = str(out_dir / file_name)

    page_size = landscape(A4)
    width, height = page_size

    c = rl_canvas.Canvas(file_path, pagesize=page_size)
    c.setTitle(f"Certificate – {recipient_name}")
    c.setAuthor(issuer_name)
    c.setSubject(event_name)

    _draw_background(c, width, height)
    _draw_border(c, width, height)
    _draw_header(c, width, height, issuer_name)
    _draw_body(c, width, height, recipient_name, event_name, issue_date)
    _draw_footer(c, width, height, cert_id)

    c.save()
    return file_path
