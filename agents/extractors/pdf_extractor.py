"""pdf_extractor.py — PDF text extraction via pdfplumber."""

from __future__ import annotations

from pathlib import Path

from agents.extractors.extractor import ExtractedContent
from agents.extractors.url_extractor import detect_language


def extract_pdf(path: Path, user_hint: str, wiki_root: Path) -> ExtractedContent:
    import pdfplumber

    pages_text: list[str] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            pages_text.append(f"--- Seite {i} ---\n{page_text}")

    text = "\n\n".join(pages_text)
    title = path.stem.replace("-", " ").replace("_", " ").title()

    # PDF is already in raw/sources/ (user placed it there)
    source_path = str(path.relative_to(wiki_root)) if path.is_relative_to(wiki_root) else str(path)

    return ExtractedContent(
        text=text,
        title=title,
        source_type="pdf",
        source_path=source_path,
        user_hint=user_hint,
        language_detected=detect_language(text[:2000]),
        mode="process-now" if user_hint.strip() else "quick-save",
    )
