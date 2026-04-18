"""image_extractor.py — Image description + OCR via Claude Vision."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.extractors.extractor import ExtractedContent
from agents.extractors.url_extractor import detect_language

VISION_PROMPT = """\
Analysiere dieses Bild.
- Falls es überwiegend Text enthält (Screenshot, Whiteboard, Dokument):
  extrahiere den vollständigen Text möglichst originalgetreu.
- Falls es überwiegend visuell ist (Foto, Szene, Kunstwerk):
  beschreibe den Inhalt detailliert.
- Falls beides zutrifft: Text zuerst, dann visuelle Beschreibung.
Nutzer-Hinweis: '{user_hint}'"""


def extract_image(path: Path, user_hint: str, wiki_root: Path, client: Any) -> ExtractedContent:
    with open(path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    suffix = path.suffix.lower().lstrip(".")
    media_type_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                      "gif": "image/gif", "webp": "image/webp"}
    media_type = media_type_map.get(suffix, "image/jpeg")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64",
                 "media_type": media_type, "data": image_data}},
                {"type": "text", "text": VISION_PROMPT.format(user_hint=user_hint)},
            ],
        }],
    )
    text = response.content[0].text

    # Save permanent copy if not already in wiki_root
    if not path.is_relative_to(wiki_root):
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        dest = wiki_root / "raw" / "assets" / f"{date_str}_{path.name}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
        source_path = str(dest.relative_to(wiki_root))
    else:
        source_path = str(path.relative_to(wiki_root))

    return ExtractedContent(
        text=text,
        title=f"Bild: {path.stem}",
        source_type="image",
        source_path=source_path,
        user_hint=user_hint,
        language_detected=detect_language(text),
        mode="process-now" if user_hint.strip() else "quick-save",
    )
