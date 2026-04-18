"""url_extractor.py — Web page extraction via requests + BeautifulSoup."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from agents.extractors.extractor import ExtractedContent

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PersonalKnowledgeOS/1.0)",
}


def extract_url(url: str, user_hint: str, wiki_root: Path) -> ExtractedContent:
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(url, headers=BROWSER_HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove nav, footer, ads before extracting text
    for tag in soup.find_all(["nav", "footer", "aside", "script", "style"]):
        tag.decompose()

    article = soup.find("article") or soup.find("main") or soup.body
    text = article.get_text(separator="\n", strip=True) if article else ""
    title = soup.title.string.strip() if soup.title else url

    # Save markdown copy to raw/sources/
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = re.sub(r"[^\w-]", "-", title[:60]).lower().strip("-")
    source_path = wiki_root / "raw" / "sources" / f"{date_str}_{slug}.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(f"# {title}\n\nSource: {url}\n\n{text}", encoding="utf-8")

    mode = "process-now" if user_hint.strip() else "quick-save"
    return ExtractedContent(
        text=text,
        title=title,
        source_type="url",
        source_path=str(source_path.relative_to(wiki_root)),
        user_hint=user_hint,
        language_detected=detect_language(text),
        mode=mode,
    )


def detect_language(text: str) -> str:
    """Heuristic language detection — German vs Spanish vs English."""
    text_lower = text.lower()
    de_markers = len(re.findall(r"\b(und|der|die|das|ist|nicht|mit|von|ein|auch)\b", text_lower))
    es_markers = len(re.findall(r"\b(que|del|los|las|una|por|con|para|como|pero)\b", text_lower))
    en_markers = len(re.findall(r"\b(the|and|that|this|with|from|have|been|they)\b", text_lower))

    scores = {"de": de_markers, "es": es_markers, "en": en_markers}
    return max(scores, key=scores.get)  # type: ignore[arg-type]
