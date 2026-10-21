"""extractor.py — Format detection and dispatch.

Entry point for all raw input normalization. Every input format (URL, PDF, image,
voice, YouTube) passes through here and exits as an ExtractedContent object with
a normalized text field. The rest of the pipeline only ever sees text.

Two modes:
  Process-Now  — triggered when user provides a hint alongside the input
  Quick-Save   — triggered for bare URLs/images without a hint; stored for later
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class ExtractedContent:
    text: str                  # normalized full text — the only thing the pipeline sees
    title: str                 # human-readable title or description of the source
    source_type: str           # "text" | "url" | "pdf" | "image" | "audio" | "youtube" | "video"
    source_path: str           # path in raw/sources/ or raw/assets/ (permanent copy)
    user_hint: str = ""        # optional hint from user ("good for vocab", "#story", ...)
    language_detected: str = "de"
    mode: str = "process-now"  # "process-now" | "quick-save"

    def to_raw_event(self, wiki_root: Path) -> dict:
        """Serialize to the raw/events/ JSON schema."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        return {
            "timestamp": timestamp,
            "source": "telegram",
            "source_type": self.source_type,
            "original_ref": self.source_path,
            "language_detected": self.language_detected,
            "content": self.text,
            "user_hint": self.user_hint,
            "processed": False,
            "wiki_refs": [],
        }

    def save_event(self, wiki_root: Path) -> Path:
        """Write to raw/events/ and return the path."""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"{ts}_{self.source_type}.json"
        event_path = wiki_root / "raw" / "events" / filename
        event_path.parent.mkdir(parents=True, exist_ok=True)
        event_path.write_text(
            json.dumps(self.to_raw_event(wiki_root), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return event_path


# ---------------------------------------------------------------------------
# Main extractor class
# ---------------------------------------------------------------------------

class Extractor:
    """Format-agnostic extractor. Detects input type and dispatches to handlers.

    Usage:
        extractor = Extractor(wiki_root=Path("."), anthropic_client=client)
        content = extractor.extract(telegram_input)
    """

    def __init__(self, wiki_root: Path, anthropic_client: Any | None = None):
        self.wiki_root = wiki_root
        self.client = anthropic_client

    def extract(self, raw_input: str | Path, user_hint: str = "") -> ExtractedContent:
        """Detect input type and extract normalized text.

        Args:
            raw_input: Either a string (Telegram text/URL) or a Path (local file).
            user_hint: Optional context from user e.g. "#vocab", "gute Geschichte".

        Returns:
            ExtractedContent with normalized text and metadata.
        """
        input_type = self._detect_type(raw_input, user_hint)

        match input_type:
            case "text":
                return self._extract_text(raw_input, user_hint)
            case "url":
                return self._extract_url(raw_input, user_hint)
            case "pdf":
                return self._extract_pdf(raw_input, user_hint)
            case "image":
                return self._extract_image(raw_input, user_hint)
            case "audio":
                return self._extract_audio(raw_input, user_hint)
            case "youtube":
                return self._extract_youtube(raw_input, user_hint)
            case "video":
                return self._extract_video_audio(raw_input, user_hint)
            case _:
                raise ValueError(f"Unsupported input type: {input_type}")

    def should_process_now(self, raw_input: str | Path, user_hint: str) -> bool:
        """Return True if input should be processed immediately (not quick-saved).

        Rules (from KNOWLEDGE_GRAPH.md §0.2):
          - Any text → always process now
          - URL/image without hint → quick-save
          - URL/image with hint → process now
        """
        input_type = self._detect_type(raw_input, user_hint)
        if input_type == "text":
            return True
        return bool(user_hint.strip())

    # -----------------------------------------------------------------------
    # Type detection
    # -----------------------------------------------------------------------

    def _detect_type(self, raw_input: str | Path, user_hint: str = "") -> str:
        if isinstance(raw_input, Path):
            return self._detect_file_type(raw_input)

        text = str(raw_input).strip()

        if self._is_youtube_url(text):
            return "youtube"
        if self._is_url(text):
            return "url"
        return "text"

    def _detect_file_type(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return "pdf"
        if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}:
            return "image"
        if suffix in {".mp3", ".ogg", ".m4a", ".wav", ".flac", ".opus"}:
            return "audio"
        if suffix in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
            return "video"
        if suffix in {".md", ".txt"}:
            return "text"
        raise ValueError(f"Unrecognized file extension: {suffix}")

    @staticmethod
    def _is_url(text: str) -> bool:
        return bool(re.match(r"https?://", text))

    @staticmethod
    def _is_youtube_url(text: str) -> bool:
        return bool(re.search(r"(youtube\.com/watch|youtu\.be/)", text))

    # -----------------------------------------------------------------------
    # Handlers — implementations live in dedicated extractor modules
    # -----------------------------------------------------------------------

    def _extract_text(self, text: str, user_hint: str) -> ExtractedContent:
        """Plain text — no extraction overhead, pass through directly."""
        from agents.extractors.url_extractor import detect_language
        lang = detect_language(str(text))
        return ExtractedContent(
            text=str(text),
            title=str(text)[:80],
            source_type="text",
            source_path="",   # text inputs are not saved to raw/sources/
            user_hint=user_hint,
            language_detected=lang,
            mode="process-now",
        )

    def _extract_url(self, url: str, user_hint: str) -> ExtractedContent:
        from agents.extractors.url_extractor import extract_url
        return extract_url(str(url), user_hint, self.wiki_root)

    def _extract_pdf(self, path: Path, user_hint: str) -> ExtractedContent:
        from agents.extractors.pdf_extractor import extract_pdf
        return extract_pdf(Path(path), user_hint, self.wiki_root)

    def _extract_image(self, path: Path, user_hint: str) -> ExtractedContent:
        from agents.extractors.image_extractor import extract_image
        if self.client is None:
            raise RuntimeError("Anthropic client required for image extraction.")
        return extract_image(Path(path), user_hint, self.wiki_root, self.client)

    def _extract_audio(self, path: Path, user_hint: str) -> ExtractedContent:
        from agents.extractors.audio_extractor import extract_audio
        return extract_audio(Path(path), user_hint, self.wiki_root)

    def _extract_youtube(self, url: str, user_hint: str) -> ExtractedContent:
        from agents.extractors.youtube_extractor import extract_youtube
        return extract_youtube(str(url), user_hint, self.wiki_root)

    def _extract_video_audio(self, path: Path, user_hint: str) -> ExtractedContent:
        """Video: strip audio track, then transcribe via Whisper."""
        import subprocess
        path = Path(path)
        audio_path = path.with_suffix(".ogg")
        subprocess.run(
            ["ffmpeg", "-i", str(path), "-vn", "-acodec", "libopus", str(audio_path)],
            check=True, capture_output=True,
        )
        return self._extract_audio(audio_path, user_hint)
