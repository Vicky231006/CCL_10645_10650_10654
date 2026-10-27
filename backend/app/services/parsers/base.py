"""Base types and format detection for the parser registry."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    """Raw parse output before structuring into the resume model."""

    text: str
    confidence: float = 0.5
    parser: str = "unknown"
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    ocr_used: bool = False
    links: list[str] = field(default_factory=list)


# extension -> canonical format id
EXTENSION_FORMATS: dict[str, str] = {
    "pdf": "pdf",
    "docx": "docx",
    "doc": "doc",
    "txt": "txt",
    "text": "txt",
    "md": "md",
    "markdown": "md",
    "rtf": "rtf",
    "odt": "odt",
    "tex": "tex",
    "latex": "tex",
    "html": "html",
    "htm": "html",
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "webp": "image",
}

CONTENT_TYPE_FORMATS: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
    "text/plain": "txt",
    "text/markdown": "md",
    "application/rtf": "rtf",
    "text/rtf": "rtf",
    "application/vnd.oasis.opendocument.text": "odt",
    "application/x-tex": "tex",
    "text/html": "html",
    "image/png": "image",
    "image/jpeg": "image",
    "image/webp": "image",
}

# magic-byte signatures used to verify actual file type
SIGNATURES: list[tuple[bytes, str]] = [
    (b"%PDF-", "pdf"),
    (b"PK\x03\x04", "zip"),  # could be docx/odt
    (b"{\\rtf", "rtf"),
    (b"\x89PNG\r\n\x1a\n", "image"),
    (b"\xff\xd8\xff", "image"),
    (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "ole"),  # legacy doc
]


def extension_of(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def detect_format(filename: str, content_type: str | None, data: bytes) -> str:
    """Determine the canonical format using extension, content-type, then magic bytes."""
    ext = extension_of(filename)
    fmt = EXTENSION_FORMATS.get(ext)
    if fmt:
        return fmt
    if content_type and content_type.split(";")[0].strip() in CONTENT_TYPE_FORMATS:
        return CONTENT_TYPE_FORMATS[content_type.split(";")[0].strip()]
    for sig, kind in SIGNATURES:
        if data.startswith(sig):
            if kind == "zip":
                # inspect - docx vs odt
                if b"word/document.xml" in data[:4000]:
                    return "docx"
                if b"mimetype" in data[:200]:
                    return "odt"
                return "docx"
            if kind == "ole":
                return "doc"
            return kind
    if data[:512].decode("utf-8", errors="ignore").isprintable():
        return "txt"
    return "unknown"
