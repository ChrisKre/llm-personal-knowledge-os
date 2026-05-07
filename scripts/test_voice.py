"""test_voice.py — MVP-2 Voice-Ingest Trocken-Test.

Generiert (oder nimmt) Audio-Files, transkribiert via faster-whisper und
fuehrt sie durch die Ingest-Pipeline (Dry-Run by default).

Usage:
    python scripts/test_voice.py --generate          # synth DE+ES+Mix samples
    python scripts/test_voice.py --file PATH         # use existing audio file
    python scripts/test_voice.py --generate --write  # also write wiki files
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")


SAMPLES = [
    ("de_short",
     "Heute war ein wirklich schoener Tag. Ich habe lange in der Sonne gesessen und Kaffee getrunken.",
     "de"),
    ("es_short",
     "Hoy aprendi una palabra nueva en espanol: madrugada. Significa la hora antes del amanecer.",
     "es"),
    ("mix_long",
     "Heute habe ich eine spanische Vokabel gelernt. Das Wort ist ensimismado, das bedeutet in sich versunken. "
     "Ich finde solche Woerter besonders schoen, weil sie ein Gefuehl ausdruecken, das im Deutschen nur umstaendlich "
     "zu beschreiben waere. Eine richtige Bruecke zwischen den Sprachen.",
     "de"),
]


def _generate_samples(out_dir: Path) -> list[tuple[str, Path, str]]:
    """Use gTTS to synthesize sample audio files. Returns list of (name, path, expected_lang)."""
    from gtts import gTTS

    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for name, text, lang in SAMPLES:
        target = out_dir / f"{name}.mp3"
        if not target.exists():
            print(f"  Generiere {target.name} ({lang}) via gTTS...")
            tts_lang = "es" if name.startswith("es_") else "de"
            tts = gTTS(text=text, lang=tts_lang)
            tts.save(str(target))
        else:
            print(f"  Vorhanden: {target.name}")
        results.append((name, target, lang))
    return results


def _print_section(title: str) -> None:
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}")


def _run_extract(path: Path) -> tuple[float, object]:
    """Run audio_extractor on path, return (latency_seconds, ExtractedContent)."""
    from agents.extractors.audio_extractor import extract_audio
    t0 = time.perf_counter()
    extracted = extract_audio(path, user_hint="", wiki_root=REPO_ROOT)
    t1 = time.perf_counter()
    return (t1 - t0), extracted


def _run_pipeline(extracted, write: bool) -> dict:
    """Run extracted content through run_ingest. Dry-run unless write=True."""
    if not write:
        import agents.graph_writer as _gw
        import main_workflow as _mw
        def _dry(writes, wiki_root=None):
            print(f"      [DRY-RUN] execute_writes() wuerde {len(writes)} Datei(en) schreiben.")
        _gw.execute_writes = _dry
        _mw.execute_writes = _dry
        # Verhindert Ghost-Eintraege im index.md (Dry-Run-Befund Session 021).
        _mw._update_index = lambda s, wiki_root=None: None

    from main_workflow import run_ingest
    raw_event = extracted.to_raw_event(REPO_ROOT)
    return run_ingest(raw_event)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true", help="Generate gTTS samples in /tmp")
    parser.add_argument("--file", type=str, help="Use existing audio file (single-file test)")
    parser.add_argument("--write", action="store_true", help="Actually write wiki files (default: dry-run)")
    parser.add_argument("--no-pipeline", action="store_true", help="Only extract; skip run_ingest")
    args = parser.parse_args()

    if not args.generate and not args.file:
        parser.error("--generate or --file required")

    if args.file:
        path = Path(args.file)
        if not path.is_file():
            sys.exit(f"Not a file: {path}")
        targets = [(path.stem, path, "?")]
    else:
        sample_dir = REPO_ROOT / "raw" / "assets" / "_test_voice"
        targets = _generate_samples(sample_dir)

    for name, path, expected_lang in targets:
        _print_section(f"SAMPLE: {name}  ({path.name})")
        latency, extracted = _run_extract(path)
        print(f"  Latency:           {latency:.2f}s")
        print(f"  language_detected: {extracted.language_detected!r}  (expected: {expected_lang})")
        print(f"  source_type:       {extracted.source_type}")
        print(f"  source_path:       {extracted.source_path}")
        print(f"  Transcript:        {extracted.text[:200]}")

        match_marker = "OK" if extracted.language_detected == expected_lang else "MISMATCH"
        print(f"  Lang-Match:        [{match_marker}]")

        if args.no_pipeline:
            continue

        print("\n  -> run_ingest...")
        try:
            t0 = time.perf_counter()
            final = _run_pipeline(extracted, args.write)
            t1 = time.perf_counter()
            print(f"  Pipeline-Latency:  {t1 - t0:.2f}s")
            print(f"  Intent:            {final.get('classified_intent', '?')}")
            print(f"  Verdict:           {final.get('supervisor_verdict', '?')}")
            writes = final.get("wiki_writes", [])
            print(f"  Wiki-Writes:       {len(writes)}")
            for w in writes:
                print(f"    - {w.get('path', '?')}")
        except Exception as exc:
            print(f"  ERROR: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
