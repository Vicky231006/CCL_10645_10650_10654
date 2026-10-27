"""Export dispatcher."""
from __future__ import annotations

from app.schemas.resume import ResumeContent
from app.services.exports.docx import render_docx
from app.services.exports.latex import render_latex
from app.services.exports.pdf import render_pdf
from app.services.exports.text import render_text

CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "latex": "application/x-tex",
    "tex": "application/x-tex",
    "txt": "text/plain",
}

EXTENSIONS = {"pdf": "pdf", "docx": "docx", "latex": "tex", "tex": "tex", "txt": "txt"}


def export_resume(content: ResumeContent, fmt: str, page_size: str = "A4") -> tuple[bytes, str, str]:
    fmt = fmt.lower()
    if fmt == "pdf":
        return render_pdf(content, page_size), "pdf", CONTENT_TYPES["pdf"]
    if fmt == "docx":
        return render_docx(content, page_size), "docx", CONTENT_TYPES["docx"]
    if fmt in ("latex", "tex"):
        return render_latex(content).encode("utf-8"), "tex", CONTENT_TYPES["latex"]
    if fmt == "txt":
        return render_text(content).encode("utf-8"), "txt", CONTENT_TYPES["txt"]
    raise ValueError(f"Unsupported export format: {fmt}")
