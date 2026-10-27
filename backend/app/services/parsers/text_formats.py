"""Text-based format parsers: txt, md, rtf, tex, html, odt."""
from __future__ import annotations

import re
import zipfile
from io import BytesIO

from app.services.parsers.base import ParsedDocument


def parse_txt(data: bytes) -> ParsedDocument:
    for enc in ("utf-8", "utf-16", "cp1252", "latin-1"):
        try:
            text = data.decode(enc)
            return ParsedDocument(text=text, confidence=0.9, parser="txt")
        except UnicodeDecodeError:
            continue
    return ParsedDocument(
        text=data.decode("utf-8", errors="replace"),
        confidence=0.6,
        parser="txt",
        warnings=["Encoding not recognised; decoded with replacements."],
    )


def parse_markdown(data: bytes) -> ParsedDocument:
    text = parse_txt(data).text
    # strip common markdown syntax for cleaner structuring
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"[*_`]", "", text)
    text = re.sub(r"^\s*[-*+]\s+", "• ", text, flags=re.MULTILINE)
    return ParsedDocument(text=text, confidence=0.85, parser="md")


def parse_rtf(data: bytes) -> ParsedDocument:
    try:
        from striprtf.striprtf import rtf_to_text

        raw = data.decode("latin-1", errors="replace")
        text = rtf_to_text(raw, errors="ignore")
        return ParsedDocument(text=text, confidence=0.8, parser="rtf")
    except Exception as exc:  # noqa: BLE001
        return ParsedDocument(
            text="",
            confidence=0.0,
            parser="rtf",
            warnings=[f"RTF parse failed: {exc}"],
        )


_TEX_CMD_RE = re.compile(r"\\[a-zA-Z]+\*?")
_LATEX_SPECIAL = {
    r"\&": "&", r"\%": "%", r"\$": "$", r"\#": "#", r"\_": "_",
    r"\{": "{", r"\}": "}", r"\textbackslash": "\\", "~": " ",
}


def parse_tex(data: bytes) -> ParsedDocument:
    """Extract readable text from LaTeX source WITHOUT executing anything."""
    raw = parse_txt(data).text
    # remove comments
    raw = re.sub(r"(?<!\\)%.*", "", raw)
    # capture \textbf{...}, \item, section headings
    raw = re.sub(r"\\item\s*", "\n• ", raw)
    raw = re.sub(r"\\(section|subsection|textbf|textit|emph)\*?\{([^{}]*)\}", r"\2", raw)
    raw = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", raw)
    raw = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", "", raw)
    for k, v in _LATEX_SPECIAL.items():
        raw = raw.replace(k, v)
    raw = re.sub(r"[{}]", "", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return ParsedDocument(text=raw.strip(), confidence=0.75, parser="tex")


def parse_html(data: bytes) -> ParsedDocument:
    try:
        from bs4 import BeautifulSoup

        # lxml is a safe HTML parser; we never execute scripts.
        soup = BeautifulSoup(data, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return ParsedDocument(text=text.strip(), confidence=0.8, parser="html")
    except Exception as exc:  # noqa: BLE001
        return ParsedDocument(text="", confidence=0.0, parser="html", warnings=[f"HTML parse failed: {exc}"])


def parse_odt(data: bytes) -> ParsedDocument:
    try:
        from odf import teletype
        from odf import text as odf_text
        from odf.opendocument import load

        doc = load(BytesIO(data))
        lines: list[str] = []
        for para in doc.getElementsByType(odf_text.P):
            value = teletype.extractText(para).strip()
            if value:
                lines.append(value)
        return ParsedDocument(text="\n".join(lines), confidence=0.8, parser="odt")
    except Exception as exc:  # noqa: BLE001
        return ParsedDocument(text="", confidence=0.0, parser="odt", warnings=[f"ODT parse failed: {exc}"])


def is_zip(data: bytes) -> bool:
    return data.startswith(b"PK\x03\x04") and zipfile.is_zipfile(BytesIO(data))
