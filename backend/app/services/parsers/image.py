"""Image (scanned resume) parser using OCR when available."""
from __future__ import annotations

import shutil
from io import BytesIO

from app.services.parsers.base import ParsedDocument


def parse_image(data: bytes) -> ParsedDocument:
    if shutil.which("tesseract") is None:
        return ParsedDocument(
            text="",
            confidence=0.0,
            parser="image",
            warnings=[
                "OCR is not configured (Tesseract binary not found). "
                "Please upload a text-based PDF, DOCX, or TXT version of this resume."
            ],
        )
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(BytesIO(data))
        text = pytesseract.image_to_string(image)
        if not text.strip():
            return ParsedDocument(
                text="", confidence=0.1, parser="image-ocr", warnings=["OCR found no readable text."]
            )
        return ParsedDocument(
            text=text,
            confidence=0.5,
            parser="image-ocr",
            ocr_used=True,
            warnings=["Text extracted with OCR; please verify carefully."],
        )
    except Exception as exc:  # noqa: BLE001
        return ParsedDocument(text="", confidence=0.0, parser="image", warnings=[f"OCR failed: {exc}"])
