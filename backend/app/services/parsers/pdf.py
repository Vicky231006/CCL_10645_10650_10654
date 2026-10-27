"""PDF parser with an optional OCR fallback for scanned documents."""
from __future__ import annotations

import re
import shutil
from io import BytesIO

from app.services.parsers.base import ParsedDocument

_REPLACEMENT = "\ufffd"


def _repair_undecodable(text: str) -> str:
    """Approximate glyphs whose font lacks a Unicode mapping.

    Certain PDF fonts (common in exported resumes) map punctuation glyphs
    (apostrophes, dashes, curly quotes) to U+FFFD. We recover the most likely
    character from context so the structured resume stays readable.
    """
    if _REPLACEMENT not in text:
        return text
    text = re.sub(rf"{_REPLACEMENT}(?=s\b)", "'", text)  # possessive: DJSCE?s
    text = re.sub(rf"(?<=\s){_REPLACEMENT}(?=\s)", "-", text)  # spaced dash
    text = re.sub(rf"(?<=\s){_REPLACEMENT}(?=[A-Za-z])", '"', text)  # opening quote
    text = re.sub(rf"{_REPLACEMENT}(?=\s|$)", '"', text)  # closing quote
    return text.replace(_REPLACEMENT, "'")


def _extract_with_pypdf(data: bytes) -> tuple[str, int]:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:  # noqa: BLE001
            raise ValueError("PDF is encrypted and cannot be read.")
    pages = len(reader.pages)
    chunks = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(chunks), pages


def _extract_with_pdfminer(data: bytes) -> str:
    from pdfminer.high_level import extract_text

    return extract_text(BytesIO(data)) or ""


def _extract_link_uris(data: bytes) -> list[str]:
    """Collect hyperlink target URIs from PDF link annotations.

    Contact details are often rendered as display text ("Email", "LinkedIn")
    with the actual address only present in the link annotation.
    """
    from pypdf import PdfReader

    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:  # noqa: BLE001
                return []
        found: list[str] = []
        for page in reader.pages:
            annots = page.get("/Annots")
            if not annots:
                continue
            try:
                for annot in annots:
                    obj = annot.get_object() if hasattr(annot, "get_object") else annot
                    if not obj or obj.get("/Subtype") != "/Link":
                        continue
                    action = obj.get("/A")
                    if action is None:
                        continue
                    action = action.get_object() if hasattr(action, "get_object") else action
                    uri = action.get("/URI") if action else None
                    if uri and str(uri) not in found:
                        found.append(str(uri))
            except Exception:  # noqa: BLE001
                continue
        return found
    except Exception:  # noqa: BLE001
        return []


def _ocr_available() -> bool:
    return shutil.which("tesseract") is not None


def _ocr_pdf(data: bytes) -> tuple[str, str | None]:
    try:
        import pytesseract  # optional dependency
        from pdf2image import convert_from_bytes  # optional dependency

        images = convert_from_bytes(data)
        text = "\n".join(pytesseract.image_to_string(img) for img in images)
        return text, None
    except Exception as exc:  # noqa: BLE001
        return "", f"OCR unavailable: {exc}"


def parse_pdf(data: bytes) -> ParsedDocument:
    warnings: list[str] = []
    text = ""
    pages = 0
    try:
        text, pages = _extract_with_pypdf(data)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"pypdf extraction failed: {exc}")

    if len(text.strip()) < 40:
        try:
            alt = _extract_with_pdfminer(data)
            if len(alt.strip()) > len(text.strip()):
                text = alt
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"pdfminer extraction failed: {exc}")

    link_uris = _extract_link_uris(data)

    if _REPLACEMENT in text:
        text = _repair_undecodable(text)
        warnings.append("Some glyphs lacked a Unicode mapping; punctuation was approximated.")

    if len(text.strip()) < 40:
        # Likely a scanned/image PDF.
        if _ocr_available():
            ocr_text, err = _ocr_pdf(data)
            if ocr_text.strip():
                return ParsedDocument(
                    text=ocr_text,
                    confidence=0.55,
                    parser="pdf-ocr",
                    ocr_used=True,
                    warnings=warnings + ["Text extracted with OCR; please verify carefully."],
                )
            if err:
                warnings.append(err)
        else:
            warnings.append(
                "This PDF appears to be scanned or image-based. OCR is not configured "
                "(install Tesseract + pytesseract/pdf2image) so text could not be extracted."
            )
        return ParsedDocument(
            text=text, confidence=0.15, parser="pdf", warnings=warnings,
            notes=[f"{pages} pages"], links=link_uris,
        )

    return ParsedDocument(
        text=text, confidence=0.9, parser="pdf", warnings=warnings,
        notes=[f"{pages} pages"], links=link_uris,
    )
