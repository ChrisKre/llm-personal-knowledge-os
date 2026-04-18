"""youtube_extractor.py — YouTube transcript extraction (no download, no API key)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from agents.extractors.extractor import ExtractedContent
from agents.extractors.url_extractor import detect_language

# Preferred transcript languages in order of priority
TRANSCRIPT_LANGUAGES = ["de", "es", "en"]


def extract_youtube(url: str, user_hint: str, wiki_root: Path) -> ExtractedContent:
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound

    video_id = _parse_video_id(url)
    if not video_id:
        raise ValueError(f"Could not parse YouTube video ID from: {url}")

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=TRANSCRIPT_LANGUAGES)
    except NoTranscriptFound:
        # Fall back to auto-generated in any language
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_generated_transcript(TRANSCRIPT_LANGUAGES).fetch()

    text = " ".join(entry["text"] for entry in transcript)
    title = f"YouTube: {video_id}"

    # Save transcript to raw/sources/
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    source_path = wiki_root / "raw" / "sources" / f"{date_str}_youtube-{video_id}.txt"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(f"Source: {url}\n\n{text}", encoding="utf-8")

    mode = "process-now" if user_hint.strip() else "quick-save"
    return ExtractedContent(
        text=text,
        title=title,
        source_type="youtube",
        source_path=str(source_path.relative_to(wiki_root)),
        user_hint=user_hint,
        language_detected=detect_language(text[:2000]),
        mode=mode,
    )


def _parse_video_id(url: str) -> str | None:
    patterns = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
