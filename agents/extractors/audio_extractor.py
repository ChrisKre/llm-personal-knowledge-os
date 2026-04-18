"""audio_extractor.py — Voice message transcription via faster-whisper (local, free)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agents.extractors.extractor import ExtractedContent

# Model is loaded once at module level to avoid repeated startup cost.
# "small" balances speed vs. accuracy for clear speech.
_whisper_model = None


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    return _whisper_model


def extract_audio(path: Path, user_hint: str, wiki_root: Path) -> ExtractedContent:
    model = _get_model()
    segments, info = model.transcribe(str(path), beam_size=5)
    text = " ".join(s.text.strip() for s in segments)

    # Save permanent copy in raw/assets/ if coming from outside wiki_root
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
        title=f"Sprachnachricht: {path.stem}",
        source_type="audio",
        source_path=source_path,
        user_hint=user_hint,
        language_detected=info.language,
        mode="process-now",  # voice messages are always processed immediately
    )


def transcribe_with_segments(path: Path):
    """Return (text, segments) — segments carry timing data for Story-Lab analysis."""
    model = _get_model()
    segments_iter, info = model.transcribe(str(path), beam_size=5, word_timestamps=False)
    segments = list(segments_iter)
    text = " ".join(s.text.strip() for s in segments)
    return text, segments, info
