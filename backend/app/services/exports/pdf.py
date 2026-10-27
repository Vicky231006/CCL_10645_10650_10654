"""PDF export using reportlab (pure-Python, no external binaries required).

Renders a faithful, ATS-conscious rendition of the Jake's Resume structure:
single column, centred name, contact line, ruled section headings, role/date rows.
"""
from __future__ import annotations

from io import BytesIO

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.resume import ResumeContent
from app.services.exports.links import ensure_url, link_label, mailto

PAGE_SIZES = {"A4": A4, "LETTER": LETTER}
LINK_COLOR = "#1a4d8f"


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=20, alignment=TA_CENTER, leading=23),
        "contact": ParagraphStyle("contact", fontName="Helvetica", fontSize=9, alignment=TA_CENTER, leading=12),
        "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=11, spaceBefore=8, spaceAfter=1),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=12.5),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.5, leading=12.5, leftIndent=10,
                                 bulletIndent=1, alignment=TA_JUSTIFY),
        "entry": ParagraphStyle("entry", fontName="Helvetica-Bold", fontSize=9.5, leading=12.5),
        "date": ParagraphStyle("date", fontName="Helvetica", fontSize=9.5, leading=12.5, alignment=2),
        "sub": ParagraphStyle("sub", fontName="Helvetica-Oblique", fontSize=9.5, leading=12.5),
    }


def _esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _href(url: str) -> str:
    return _esc(url).replace('"', "&quot;")


def _alink(url: str, text: str) -> str:
    """Render a clickable, embedded hyperlink (label text, not a raw URL)."""
    return f'<a href="{_href(url)}" color="{LINK_COLOR}">{_esc(text)}</a>'


def _section_heading(styles: dict, title: str):
    return [
        Spacer(1, 4),
        Paragraph(title.upper(), styles["section"]),
        HRFlowable(width="100%", thickness=0.8, color="#333333", spaceBefore=1, spaceAfter=3),
    ]


def _bullets(styles: dict, bullets: list[str]):
    return [Paragraph(_esc(b), styles["bullet"], bulletText="•") for b in bullets if b]


def _two_col_row(styles: dict, left: str, right: str):
    data = [[Paragraph(left, styles["entry"]), Paragraph(_esc(right), styles["date"])]]
    table = Table(data, colWidths=["78%", "22%"])
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                               ("TOPPADDING", (0, 0), (-1, -1), 0),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    return table


def render_pdf(content: ResumeContent, page_size: str = "A4") -> bytes:
    buffer = BytesIO()
    pagesize = PAGE_SIZES.get(page_size.upper(), A4)
    doc = SimpleDocTemplate(
        buffer, pagesize=pagesize, topMargin=12 * mm, bottomMargin=12 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm, title=content.contact.name or "Resume",
    )
    styles = _styles()
    story: list = []

    contact = content.contact
    if contact.name:
        story.append(Paragraph(_esc(contact.name), styles["name"]))
    if contact.headline:
        story.append(Paragraph(_esc(contact.headline), styles["contact"]))
    line_items: list[str] = []
    if contact.email:
        line_items.append(_alink(mailto(contact.email), contact.email))
    if contact.phone:
        line_items.append(_esc(contact.phone))
    if contact.location:
        line_items.append(_esc(contact.location))
    for link in contact.links:
        if not link.url:
            continue
        curl = ensure_url(link.url)
        text = link.label or link_label(link.url)
        line_items.append(_alink(curl, text) if curl else _esc(text))
    if line_items:
        story.append(Paragraph(" • ".join(line_items), styles["contact"]))

    order = content.section_order or ["summary", "experience", "projects", "education", "skills",
                                      "certifications", "achievements"]
    visibility = content.section_visibility or {}

    for section in order:
        if visibility.get(section) is False:
            continue
        if section == "summary" and content.summary:
            story += _section_heading(styles, "Summary")
            story.append(Paragraph(_esc(content.summary), styles["body"]))
        elif section == "experience" and content.experience:
            story += _section_heading(styles, "Experience")
            for exp in content.experience:
                left = f"{_esc(exp.role)}" + (f" — {_esc(exp.company)}" if exp.company else "")
                story.append(_two_col_row(styles, left, f"{exp.start} – {exp.end}".strip(" –")))
                if exp.location:
                    story.append(Paragraph(_esc(exp.location), styles["sub"]))
                story += _bullets(styles, exp.bullets)
        elif section == "projects" and content.projects:
            story += _section_heading(styles, "Projects")
            for proj in content.projects:
                left = f"{_esc(proj.name)}"
                if proj.tech:
                    left += f" <font size=8>| {_esc(', '.join(proj.tech))}</font>"
                if proj.link:
                    purl = ensure_url(proj.link)
                    if purl:
                        left += f' <font size=8>| {_alink(purl, link_label(proj.link))}</font>'
                    else:
                        left += f' <font size=8>| {_esc(proj.link)}</font>'
                story.append(Paragraph(left, styles["entry"]))
                story += _bullets(styles, proj.bullets)
        elif section == "education" and content.education:
            story += _section_heading(styles, "Education")
            for ed in content.education:
                left = f"{_esc(ed.institution)}" + (f" — {_esc(ed.degree)}" if ed.degree else "")
                story.append(_two_col_row(styles, left, f"{ed.start} – {ed.end}".strip(" –")))
                story += _bullets(styles, ed.details)
        elif section == "skills" and content.skills:
            story += _section_heading(styles, "Skills")
            for group in content.skills:
                if not group.items:
                    continue
                label = f"<b>{_esc(group.category)}:</b> " if group.category and group.category != "Skills" else ""
                story.append(Paragraph(label + _esc(", ".join(group.items)), styles["body"]))
        elif section == "certifications" and content.certifications:
            story += _section_heading(styles, "Certifications")
            story += _bullets(styles, content.certifications)
        elif section == "achievements" and content.achievements:
            story += _section_heading(styles, "Achievements")
            story += _bullets(styles, content.achievements)

    doc.build(story)
    return buffer.getvalue()
