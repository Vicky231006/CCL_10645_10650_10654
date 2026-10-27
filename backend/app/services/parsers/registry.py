"""Parser registry: maps canonical formats to parser callables."""
from __future__ import annotations

from collections.abc import Callable

from app.services.parsers import image, office, pdf, text_formats
from app.services.parsers.base import ParsedDocument

PARSERS: dict[str, Callable[[bytes], ParsedDocument]] = {
    "pdf": pdf.parse_pdf,
    "docx": office.parse_docx,
    "doc": office.parse_doc,
    "txt": text_formats.parse_txt,
    "md": text_formats.parse_markdown,
    "rtf": text_formats.parse_rtf,
    "odt": text_formats.parse_odt,
    "tex": text_formats.parse_tex,
    "html": text_formats.parse_html,
    "image": image.parse_image,
}


def registered_formats() -> list[str]:
    return sorted(PARSERS.keys())


def parse_document(fmt: str, data: bytes) -> ParsedDocument:
    parser = PARSERS.get(fmt)
    if parser is None:
        return ParsedDocument(
            text="",
            confidence=0.0,
            parser="unknown",
            warnings=[f"Unsupported format: {fmt!r}."],
        )
    return parser(data)
