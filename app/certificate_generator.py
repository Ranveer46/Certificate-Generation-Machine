"""
Certificate PDF generation using ReportLab.

Ultra-premium luxury certificate design:
  - A4 landscape orientation
  - Sophisticated warm ivory / parchment background with guilloche rosette watermark
  - Multi-tier Art Deco geometric borders with ornate 45-degree corner bevels & diamond gems
  - Vector heraldic crest emblem with laurel branches and golden stars
  - Prestigious typography with bespoke decorative dividers
  - Vector embossed 32-point golden medallion seal with dual hanging satin ribbons
  - Realistic fountain-pen calligraphy signature strokes and executive signatory blocks
  - Tamper-evident verification security badge and credential ID pill
"""

import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from app.config import settings

# ---------------------------------------------------------------------------
# Curated Luxury Palette
# ---------------------------------------------------------------------------
BG_IVORY = colors.HexColor("#FCFAF6")
BG_CARD = colors.HexColor("#FFFFFF")
NAVY_DEEP = colors.HexColor("#0A192F")
NAVY_PRIMARY = colors.HexColor("#1A2B4C")
NAVY_LIGHT = colors.HexColor("#2B487A")
GOLD_DARK = colors.HexColor("#8C6B28")
GOLD_MAIN = colors.HexColor("#C59B27")
GOLD_BRIGHT = colors.HexColor("#E5C158")
GOLD_LIGHT = colors.HexColor("#F6E7B9")
GOLD_TINT = colors.HexColor("#FBF5E4")
SLATE_MUTED = colors.HexColor("#5A6B82")
TEXT_CHARCOAL = colors.HexColor("#222831")
INK_BLUE = colors.HexColor("#0D2040")
WHITE = colors.white


def _ensure_output_dir() -> Path:
    out = Path(settings.CERTIFICATES_DIR)
    out.mkdir(parents=True, exist_ok=True)
    return out


def _draw_guilloche_watermark(c: rl_canvas.Canvas, cx: float, cy: float, radius: float = 75 * mm) -> None:
    """Draw a delicate parametric rosette / guilloche security watermark in the background."""
    c.saveState()
    c.setStrokeColor(colors.HexColor("#EFE6D2"))
    c.setLineWidth(0.4)
    
    # Mathematical spirograph rosette curves
    petals = 12
    step = 4
    for r_offset in [0.7, 0.85, 1.0]:
        r_base = radius * r_offset
        path = c.beginPath()
        first = True
        for angle_deg in range(0, 361, step):
            theta = math.radians(angle_deg)
            # Hypotrochoid-like variation
            r = r_base * (1 + 0.12 * math.sin(petals * theta))
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)
        path.close()
        c.drawPath(path, stroke=1, fill=0)

    # Concentric fine rings
    for r in [25 * mm, 45 * mm, 65 * mm]:
        c.circle(cx, cy, r, stroke=1, fill=0)

    c.restoreState()


def _draw_luxury_borders(c: rl_canvas.Canvas, width: float, height: float) -> None:
    """Draw ornate multi-tier Art Deco borders with corner facets and diamond gems."""
    # Outer solid navy & gold accent frame
    m1 = 8 * mm
    c.setFillColor(NAVY_DEEP)
    # 4 corner dark corner accents
    corner_size = 35 * mm
    c.rect(0, 0, width, height, fill=0, stroke=0)

    # Outer Gold Frame
    c.setStrokeColor(GOLD_MAIN)
    c.setLineWidth(2.5)
    c.rect(m1, m1, width - 2 * m1, height - 2 * m1, stroke=1, fill=0)

    # Thin secondary inset frame
    m2 = 11.5 * mm
    c.setStrokeColor(GOLD_BRIGHT)
    c.setLineWidth(0.8)
    c.rect(m2, m2, width - 2 * m2, height - 2 * m2, stroke=1, fill=0)

    # Third delicate frame
    m3 = 14 * mm
    c.setStrokeColor(GOLD_DARK)
    c.setLineWidth(0.5)
    c.rect(m3, m3, width - 2 * m3, height - 2 * m3, stroke=1, fill=0)

    # Corner Art Deco ornaments on all 4 corners
    corners = [
        (m1, m1, 1, 1),
        (width - m1, m1, -1, 1),
        (m1, height - m1, 1, -1),
        (width - m1, height - m1, -1, -1),
    ]

    for ox, oy, dx, dy in corners:
        # Corner bracket fill
        c.setFillColor(NAVY_DEEP)
        c.setStrokeColor(GOLD_MAIN)
        c.setLineWidth(1)
        p = c.beginPath()
        p.moveTo(ox, oy)
        p.lineTo(ox + dx * 22 * mm, oy)
        p.lineTo(ox + dx * 18 * mm, oy + dy * 4 * mm)
        p.lineTo(ox + dx * 4 * mm, oy + dy * 4 * mm)
        p.lineTo(ox + dx * 4 * mm, oy + dy * 18 * mm)
        p.lineTo(ox, oy + dy * 22 * mm)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

        # Inset corner diamond gem
        gem_x = ox + dx * 9 * mm
        gem_y = oy + dy * 9 * mm
        _draw_diamond(c, gem_x, gem_y, 4 * mm, GOLD_BRIGHT, GOLD_DARK)

    # Midpoint diamond accents on borders
    _draw_diamond(c, width / 2, m1, 3.5 * mm, GOLD_BRIGHT, GOLD_MAIN)
    _draw_diamond(c, width / 2, height - m1, 3.5 * mm, GOLD_BRIGHT, GOLD_MAIN)
    _draw_diamond(c, m1, height / 2, 3.5 * mm, GOLD_BRIGHT, GOLD_MAIN)
    _draw_diamond(c, width - m1, height / 2, 3.5 * mm, GOLD_BRIGHT, GOLD_MAIN)


def _draw_diamond(
    c: rl_canvas.Canvas, cx: float, cy: float, size: float, fill_color: colors.Color, stroke_color: colors.Color
) -> None:
    """Draw a styled 4-point diamond ornament."""
    c.setFillColor(fill_color)
    c.setStrokeColor(stroke_color)
    c.setLineWidth(0.8)
    p = c.beginPath()
    p.moveTo(cx, cy + size)
    p.lineTo(cx + size * 0.7, cy)
    p.lineTo(cx, cy - size)
    p.lineTo(cx - size * 0.7, cy)
    p.close()
    c.drawPath(p, fill=1, stroke=1)


def _draw_star(c: rl_canvas.Canvas, cx: float, cy: float, r: float, color: colors.Color) -> None:
    """Draw a 5-pointed golden star."""
    c.setFillColor(color)
    c.setStrokeColor(color)
    p = c.beginPath()
    for i in range(10):
        angle = math.radians(90 + i * 36)
        radius = r if i % 2 == 0 else r * 0.45
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _draw_crest(c: rl_canvas.Canvas, cx: float, cy: float) -> None:
    """Draw a regal institutional emblem crest at the top."""
    c.saveState()
    # Shield shape
    sw, sh = 12 * mm, 14 * mm
    c.setFillColor(NAVY_PRIMARY)
    c.setStrokeColor(GOLD_MAIN)
    c.setLineWidth(1.2)
    p = c.beginPath()
    p.moveTo(cx - sw / 2, cy + sh / 2)
    p.lineTo(cx + sw / 2, cy + sh / 2)
    p.lineTo(cx + sw / 2, cy)
    p.curveTo(cx + sw / 2, cy - sh / 2, cx, cy - sh * 0.65, cx, cy - sh * 0.65)
    p.curveTo(cx, cy - sh * 0.65, cx - sw / 2, cy - sh / 2, cx - sw / 2, cy)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Inset gold shield border
    c.setStrokeColor(GOLD_BRIGHT)
    c.setLineWidth(0.6)
    p2 = c.beginPath()
    p2.moveTo(cx - sw * 0.38, cy + sh * 0.38)
    p2.lineTo(cx + sw * 0.38, cy + sh * 0.38)
    p2.lineTo(cx + sw * 0.38, cy + sh * 0.05)
    p2.curveTo(cx + sw * 0.38, cy - sh * 0.35, cx, cy - sh * 0.5, cx, cy - sh * 0.5)
    p2.curveTo(cx, cy - sh * 0.5, cx - sw * 0.38, cy - sh * 0.35, cx - sw * 0.38, cy + sh * 0.05)
    p2.close()
    c.drawPath(p2, fill=0, stroke=1)

    # 3 Gold stars inside crest
    _draw_star(c, cx, cy + 1.5 * mm, 2.4 * mm, GOLD_BRIGHT)
    _draw_star(c, cx - 3.2 * mm, cy - 2.5 * mm, 1.8 * mm, GOLD_BRIGHT)
    _draw_star(c, cx + 3.2 * mm, cy - 2.5 * mm, 1.8 * mm, GOLD_BRIGHT)

    # Flanking laurel sprig arcs
    c.setStrokeColor(GOLD_MAIN)
    c.setLineWidth(0.8)
    for flip in [-1, 1]:
        c.arc(
            cx + flip * 8 * mm - 10 * mm,
            cy - 10 * mm,
            cx + flip * 8 * mm + 10 * mm,
            cy + 10 * mm,
            startAng=220 if flip == 1 else -40,
            extent=80,
        )
        # Leaves
        for deg in [230, 255, 280] if flip == 1 else [-30, -5, 20]:
            rad = math.radians(deg)
            lx = cx + flip * 9 * mm + 8 * mm * math.cos(rad)
            ly = cy + 8 * mm * math.sin(rad)
            _draw_diamond(c, lx, ly, 1.5 * mm, GOLD_MAIN, GOLD_DARK)

    c.restoreState()


def _draw_gold_divider(c: rl_canvas.Canvas, cx: float, y: float, total_width: float = 140 * mm) -> None:
    """Draw a clean, luxury symmetrical gold divider line with center diamond."""
    half = total_width / 2
    c.setLineWidth(1)
    c.setStrokeColor(GOLD_MAIN)
    c.line(cx - half, y, cx - 8 * mm, y)
    c.line(cx + 8 * mm, y, cx + half, y)

    # Thinner flanking hairline
    c.setLineWidth(0.5)
    c.setStrokeColor(GOLD_BRIGHT)
    c.line(cx - half + 10 * mm, y - 1.2 * mm, cx - 12 * mm, y - 1.2 * mm)
    c.line(cx + 12 * mm, y - 1.2 * mm, cx + half - 10 * mm, y - 1.2 * mm)

    # Center ornaments
    _draw_diamond(c, cx, y, 2.8 * mm, GOLD_BRIGHT, GOLD_DARK)
    _draw_diamond(c, cx - 4.5 * mm, y, 1.5 * mm, GOLD_MAIN, GOLD_DARK)
    _draw_diamond(c, cx + 4.5 * mm, y, 1.5 * mm, GOLD_MAIN, GOLD_DARK)


def _draw_embossed_seal(c: rl_canvas.Canvas, cx: float, cy: float, radius: float = 24 * mm) -> None:
    """Draw a 32-point scalloped golden medallion seal with flowing ribbons."""
    c.saveState()

    # Hanging Ribbons underneath seal
    ribbon_w = 11 * mm
    ribbon_len = 32 * mm
    for sign, angle in [(-1, -22), (1, 22)]:
        c.saveState()
        c.translate(cx, cy)
        c.rotate(angle)
        # Ribbon path with notched fishtail end
        c.setFillColor(NAVY_PRIMARY)
        c.setStrokeColor(GOLD_MAIN)
        c.setLineWidth(1)
        rp = c.beginPath()
        rp.moveTo(-ribbon_w / 2, 0)
        rp.lineTo(ribbon_w / 2, 0)
        rp.lineTo(ribbon_w / 2, -ribbon_len)
        rp.lineTo(0, -ribbon_len + 6 * mm)  # fishtail notch
        rp.lineTo(-ribbon_w / 2, -ribbon_len)
        rp.close()
        c.drawPath(rp, fill=1, stroke=1)

        # Gold center stripe along ribbon
        c.setStrokeColor(GOLD_BRIGHT)
        c.setLineWidth(1.2)
        c.line(0, 0, 0, -ribbon_len + 7 * mm)
        c.restoreState()

    # 32-point Scalloped Starburst Rosette
    c.setFillColor(GOLD_MAIN)
    c.setStrokeColor(GOLD_DARK)
    c.setLineWidth(1)
    points = 32
    outer_r = radius
    inner_r = radius * 0.88
    sp = c.beginPath()
    for i in range(points * 2):
        a = math.radians(i * (360 / (points * 2)))
        r = outer_r if i % 2 == 0 else inner_r
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        if i == 0:
            sp.moveTo(x, y)
        else:
            sp.lineTo(x, y)
    sp.close()
    c.drawPath(sp, fill=1, stroke=1)

    # Embossed Concentric Inner Rings
    c.setFillColor(GOLD_BRIGHT)
    c.setStrokeColor(GOLD_DARK)
    c.setLineWidth(1.2)
    c.circle(cx, cy, radius * 0.82, fill=1, stroke=1)

    c.setFillColor(NAVY_PRIMARY)
    c.setStrokeColor(GOLD_MAIN)
    c.setLineWidth(1.5)
    c.circle(cx, cy, radius * 0.72, fill=1, stroke=1)

    # Dashed beaded security ring
    c.setStrokeColor(GOLD_BRIGHT)
    c.setLineWidth(0.8)
    c.setDash([2, 2.5], 0)
    c.circle(cx, cy, radius * 0.65, fill=0, stroke=1)
    c.setDash([], 0)

    # Seal Centerpiece: Big Star and Text
    _draw_star(c, cx, cy + 2 * mm, 6.5 * mm, GOLD_BRIGHT)

    # Small arc stars
    for offset_x in [-6 * mm, 6 * mm]:
        _draw_star(c, cx + offset_x, cy - 2 * mm, 2.5 * mm, GOLD_MAIN)

    c.setFillColor(GOLD_LIGHT)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(cx, cy - 7.5 * mm, "OFFICIAL EXCELLENCE")
    c.setFont("Helvetica", 5.5)
    c.drawCentredString(cx, cy - 10.5 * mm, "★ VERIFIED CREDENTIAL ★")

    c.restoreState()


def _draw_cursive_signature(c: rl_canvas.Canvas, cx: float, y: float) -> None:
    """Draw a natural, elegant executive cursive fountain-pen signature centered over cx."""
    c.saveState()
    c.setStrokeColor(INK_BLUE)
    c.setLineWidth(1.3)
    c.setLineCap(1)
    c.setLineJoin(1)

    p = c.beginPath()
    # Left initial capital flourish
    sx = cx - 24 * mm
    p.moveTo(sx, y + 2 * mm)
    p.curveTo(sx + 3 * mm, y + 14 * mm, sx + 8 * mm, y + 15 * mm, sx + 10 * mm, y + 6 * mm)
    p.curveTo(sx + 12 * mm, y - 1 * mm, sx + 14 * mm, y + 7 * mm, sx + 18 * mm, y + 8 * mm)
    p.curveTo(sx + 21 * mm, y + 9 * mm, sx + 23 * mm, y + 4 * mm, sx + 27 * mm, y + 7 * mm)
    p.curveTo(sx + 30 * mm, y + 10 * mm, sx + 33 * mm, y + 12 * mm, sx + 36 * mm, y + 5 * mm)
    p.curveTo(sx + 39 * mm, y, sx + 41 * mm, y + 8 * mm, sx + 45 * mm, y + 10 * mm)
    # Elegant concluding flourish underline loop
    p.curveTo(sx + 48 * mm, y + 12 * mm, sx + 46 * mm, y - 2 * mm, sx + 40 * mm, y - 2 * mm)
    p.curveTo(sx + 20 * mm, y - 3 * mm, sx + 5 * mm, y - 2 * mm, sx + 12 * mm, y)
    p.curveTo(sx + 25 * mm, y + 1 * mm, sx + 45 * mm, y + 1 * mm, sx + 50 * mm, y + 4 * mm)
    c.drawPath(p, fill=0, stroke=1)
    c.restoreState()


def _draw_director_signature(c: rl_canvas.Canvas, cx: float, y: float) -> None:
    """Draw a distinct executive cursive signature centered over cx."""
    c.saveState()
    c.setStrokeColor(INK_BLUE)
    c.setLineWidth(1.3)
    c.setLineCap(1)
    c.setLineJoin(1)

    p = c.beginPath()
    sx = cx - 22 * mm
    p.moveTo(sx, y + 5 * mm)
    p.curveTo(sx + 4 * mm, y + 15 * mm, sx + 9 * mm, y + 16 * mm, sx + 11 * mm, y + 4 * mm)
    p.curveTo(sx + 13 * mm, y - 2 * mm, sx + 17 * mm, y + 8 * mm, sx + 21 * mm, y + 9 * mm)
    p.curveTo(sx + 24 * mm, y + 10 * mm, sx + 27 * mm, y + 3 * mm, sx + 31 * mm, y + 6 * mm)
    p.curveTo(sx + 35 * mm, y + 9 * mm, sx + 38 * mm, y + 13 * mm, sx + 41 * mm, y + 4 * mm)
    # Elegant swift stroke
    p.curveTo(sx + 30 * mm, y - 3 * mm, sx + 15 * mm, y - 2 * mm, sx + 5 * mm, y - 1 * mm)
    p.curveTo(sx + 18 * mm, y, sx + 35 * mm, y + 1 * mm, sx + 45 * mm, y + 3 * mm)
    c.drawPath(p, fill=0, stroke=1)
    c.restoreState()


def generate_certificate_pdf(
    cert_id: str,
    recipient_name: str,
    recipient_email: str,
    event_name: str,
    issuer_name: str,
    issue_date: str,
) -> str:
    """
    Generate an ultra-premium PDF certificate and return the absolute file path.
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
    cx = width / 2

    c = rl_canvas.Canvas(file_path, pagesize=page_size)
    c.setTitle(f"Certificate of Excellence – {recipient_name}")
    c.setAuthor(issuer_name)
    c.setSubject(event_name)

    # 1. Background Parchment Fill
    c.setFillColor(BG_IVORY)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # 2. Guilloche Security Rosette Watermark (Center)
    _draw_guilloche_watermark(c, cx, height * 0.48, radius=70 * mm)

    # 3. Ornate Art-Deco Borders & Corners
    _draw_luxury_borders(c, width, height)

    # 4. Top Institutional Crest & Issuer Header
    top_y = height - 28.5 * mm
    _draw_crest(c, cx, top_y + 1 * mm)

    # Issuer Name (Tracked uppercase, deep navy)
    c.setFillColor(NAVY_PRIMARY)
    c.setFont("Helvetica-Bold", 17)
    issuer_clean = issuer_name.strip().upper()
    c.drawCentredString(cx, top_y - 12 * mm, issuer_clean)

    # Sub-header tagline / Institution Department
    c.setFillColor(GOLD_DARK)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(cx, top_y - 16.5 * mm, "OFFICIAL ACADEMIC & PROFESSIONAL CREDENTIAL")

    # Divider below Header
    _draw_gold_divider(c, cx, top_y - 19.5 * mm, total_width=120 * mm)

    # 5. Certificate Main Title Banner
    title_y = top_y - 30 * mm
    c.setFillColor(NAVY_DEEP)
    c.setFont("Times-Bold", 32)
    c.drawCentredString(cx, title_y, "Certificate of Completion")

    c.setFillColor(GOLD_MAIN)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(cx, title_y - 5.5 * mm, "— AND DISTINGUISHED MERIT —")

    # 6. Presentation Line
    pres_y = title_y - 14 * mm
    c.setFillColor(SLATE_MUTED)
    c.setFont("Helvetica", 11)
    c.drawCentredString(cx, pres_y, "THIS CERTIFICATE IS PROUDLY PRESENTED TO")

    # 7. Recipient Name (Centerpiece)
    name_y = pres_y - 16 * mm
    c.setFillColor(NAVY_PRIMARY)
    c.setFont("Times-BoldItalic", 38)
    c.drawCentredString(cx, name_y, recipient_name.strip())

    # Bespoke Recipient Accent Bar with Diamond Center
    name_w = min(max(c.stringWidth(recipient_name.strip(), "Times-BoldItalic", 38) + 20 * mm, 90 * mm), 180 * mm)
    _draw_gold_divider(c, cx, name_y - 4.5 * mm, total_width=name_w)

    # 8. Achievement Description Text
    desc_y = name_y - 13.5 * mm
    c.setFillColor(TEXT_CHARCOAL)
    c.setFont("Helvetica", 11)
    c.drawCentredString(cx, desc_y, "for successfully completing the rigorous curriculum and demonstrating outstanding competence in")

    # 9. Event / Program Name
    event_y = desc_y - 11.5 * mm
    c.setFillColor(NAVY_PRIMARY)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(cx, event_y, event_name.strip())

    # Date Line
    date_y = event_y - 7.5 * mm
    c.setFillColor(SLATE_MUTED)
    c.setFont("Helvetica", 10)
    c.drawCentredString(cx, date_y, f"Given on this day, {issue_date.strip()}")

    # 10. Bottom Section: Golden Medallion Seal (Left) and Signatures
    seal_x = 42 * mm
    seal_y = 43 * mm
    _draw_embossed_seal(c, seal_x, seal_y, radius=20 * mm)

    # Signatory 1 (Center-Left)
    sig1_x = 98 * mm
    sig1_y = 35 * mm
    _draw_director_signature(c, sig1_x, sig1_y + 4 * mm)
    c.setStrokeColor(GOLD_MAIN)
    c.setLineWidth(1)
    c.line(sig1_x - 30 * mm, sig1_y + 3 * mm, sig1_x + 30 * mm, sig1_y + 3 * mm)
    c.setFillColor(NAVY_PRIMARY)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(sig1_x, sig1_y - 2 * mm, "Dr. Jonathan Sterling")
    c.setFillColor(SLATE_MUTED)
    c.setFont("Helvetica", 8)
    c.drawCentredString(sig1_x, sig1_y - 6 * mm, "Director of Academic Affairs")

    # Signatory 2 (Right)
    sig2_x = width - 58 * mm
    sig2_y = 35 * mm
    _draw_cursive_signature(c, sig2_x, sig2_y + 4 * mm)
    c.setStrokeColor(GOLD_MAIN)
    c.setLineWidth(1)
    c.line(sig2_x - 30 * mm, sig2_y + 3 * mm, sig2_x + 30 * mm, sig2_y + 3 * mm)
    c.setFillColor(NAVY_PRIMARY)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(sig2_x, sig2_y - 2 * mm, "Prof. Elizabeth Bennett")
    c.setFillColor(SLATE_MUTED)
    c.setFont("Helvetica", 8)
    c.drawCentredString(sig2_x, sig2_y - 6 * mm, "Executive Board Chancellor")

    # 11. Security & Verification Footer Pill
    foot_y = 13.5 * mm
    # Clean pill background
    pill_w = 120 * mm
    pill_h = 5.5 * mm
    c.setFillColor(GOLD_TINT)
    c.setStrokeColor(GOLD_MAIN)
    c.setLineWidth(0.6)
    c.roundRect(cx - pill_w / 2, foot_y - 1.5 * mm, pill_w, pill_h, radius=2.5 * mm, fill=1, stroke=1)

    c.setFillColor(NAVY_PRIMARY)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(cx, foot_y, f"OFFICIAL VERIFICATION ID:  {cert_id}")

    # Microprint security baseline
    c.setFillColor(SLATE_MUTED)
    c.setFont("Helvetica", 6)
    c.drawCentredString(cx, foot_y - 4 * mm, "SECURE DIGITAL CREDENTIAL • ISSUED UNDER INSTITUTIONAL CHARTER • TAMPER-EVIDENT ARCHIVAL RECORD")

    c.save()
    return file_path
