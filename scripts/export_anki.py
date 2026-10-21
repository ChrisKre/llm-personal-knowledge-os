"""export_anki.py — VocabEntry → .apkg exporter (MVP-2 second wave, session 023).

Implements ENT-050/051/052:
  - Source: wiki/language/vocab/*.md with status: elaborated|practiced
  - Identity: anki_id = sha1("pks-vocab-" + slug)[:16], persisted in frontmatter
  - Card: front = ES word (with gender article if parsable), back = DE + example + mnemonic
  - Tags: frontmatter tags + language::es + difficulty::<CEFR>
  - Bridges are NOT exported (ENT-051)
  - Body sections are matched by their German headings (Übersetzungen, Beispielsätze,
    Eselsbrücke) as written by the language agent.

Usage:
    python scripts/export_anki.py [--out PATH] [--since YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import genanki
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / ".env")  # before agents.config (KOS_VAULT_ROOT)

from agents import frontmatter  # noqa: E402
from agents.config import VAULT_ROOT  # noqa: E402
VOCAB_DIR = VAULT_ROOT / "wiki" / "language" / "vocab"
DEFAULT_OUT = REPO_ROOT / "out" / "pks_spanisch_vokabeln.apkg"
EXPORTABLE_STATUS = {"elaborated", "practiced"}

ANKI_MODEL = genanki.Model(
    model_id=int(hashlib.sha1(b"pks-anki-model-vocab-v1").hexdigest()[:8], 16),
    name="PKS Vocab v1",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[{
        "name": "Card 1",
        "qfmt": "{{Front}}",
        "afmt": "{{FrontSide}}<hr id=\"answer\">{{Back}}",
    }],
    css=(
        ".card { font-family: sans-serif; font-size: 22px; text-align: center; }"
        ".example { font-weight: bold; margin: 0.6em 0; }"
        ".mnemonic { font-size: 18px; text-align: left; margin-top: 0.8em; "
        "color: #444; line-height: 1.4; }"
        ".backlink { font-size: 13px; margin-top: 1em; }"
        ".backlink a { color: #888; text-decoration: none; }"
    ),
)

DECK_ID = int(hashlib.sha1(b"pks-anki-deck-spanisch-vokabeln-v1").hexdigest()[:8], 16)
DECK_NAME = "PKS::Sprachen::Spanisch::Vokabeln"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

@dataclass
class VocabRecord:
    slug: str
    path: Path
    word: str
    language: str
    status: str
    difficulty: str | None
    updated: str | None
    anki_id: str | None
    tags: list[str] = field(default_factory=list)
    genus: str | None = None
    translation_de: str | None = None
    first_example: str | None = None
    mnemonic: str | None = None


_GENUS_RE = re.compile(r"^\s*-\s*\*\*Genus:\*\*\s*(.+?)\s*$", re.MULTILINE)
_HEADING_RE = re.compile(r"^\s*##\s+(.+?)\s*$", re.MULTILINE)


def _section(body: str, heading: str) -> str:
    """Return the body slice under '## <heading>' until the next ## heading."""
    matches = list(_HEADING_RE.finditer(body))
    for i, m in enumerate(matches):
        if m.group(1).strip().lower() == heading.lower():
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            return body[start:end].strip()
    return ""


def _extract_de(body: str) -> str | None:
    sec = _section(body, "Übersetzungen")
    for line in sec.splitlines():
        s = line.strip()
        if s.lower().startswith("- **de:**"):
            return s[len("- **DE:**"):].strip()
    return None


def _extract_first_example(body: str) -> str | None:
    sec = _section(body, "Beispielsätze")
    for line in sec.splitlines():
        s = line.strip()
        if s.startswith("- "):
            return s[2:].strip()
    return None


def _extract_mnemonic(body: str) -> str | None:
    sec = _section(body, "Eselsbrücke")
    cleaned = "\n".join(l.strip() for l in sec.splitlines()).strip()
    return cleaned or None


def _extract_genus(body: str) -> str | None:
    m = _GENUS_RE.search(body)
    if not m:
        return None
    val = m.group(1).strip().strip("`")
    if val in {"el", "la"}:
        return val
    return None


def _str_or_none(value: object) -> str | None:
    """Coerce a frontmatter value to a stripped string, or None if empty."""
    if value in (None, "", "null", "~"):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    s = str(value).strip()
    return s or None


def parse_vocab_file(path: Path) -> VocabRecord | None:
    try:
        fm, body = frontmatter.read(path)
    except yaml.YAMLError:
        return None
    if not fm or fm.get("type") != "VocabEntry":
        return None

    slug = path.stem
    tags_raw = fm.get("tags") or []
    if isinstance(tags_raw, str):
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    else:
        tags = [str(t).strip() for t in tags_raw if str(t).strip()]

    return VocabRecord(
        slug=slug,
        path=path,
        word=str(fm.get("word") or "").strip() or slug,
        language=str(fm.get("language") or "").strip(),
        status=str(fm.get("status") or "").strip(),
        difficulty=_str_or_none(fm.get("difficulty")),
        updated=_str_or_none(fm.get("updated")),
        anki_id=_str_or_none(fm.get("anki_id")),
        tags=tags,
        genus=_extract_genus(body),
        translation_de=_extract_de(body),
        first_example=_extract_first_example(body),
        mnemonic=_extract_mnemonic(body),
    )


# ---------------------------------------------------------------------------
# Frontmatter patch (anki_id back-write)
# ---------------------------------------------------------------------------

def patch_anki_id(path: Path, new_id: str) -> bool:
    """Set frontmatter ``anki_id`` to ``new_id``. Idempotent.

    Returns True if the file was changed. Re-runs over a file that already
    carries the correct id are no-ops.
    """
    try:
        fm, body = frontmatter.read(path)
    except yaml.YAMLError:
        return False
    if str(fm.get("anki_id") or "").strip() == new_id:
        return False
    fm["anki_id"] = new_id
    frontmatter.write(path, fm, body)
    return True


# ---------------------------------------------------------------------------
# Card rendering
# ---------------------------------------------------------------------------

def make_guid(slug: str) -> str:
    return hashlib.sha1(f"pks-vocab-{slug}".encode("utf-8")).hexdigest()[:16]


def _md_to_html(text: str) -> str:
    """Tiny markdown subset → HTML. Only what mnemonics actually use."""
    if not text:
        return ""
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    out = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", out)
    out = out.replace("\n\n", "</p><p>")
    out = out.replace("\n", "<br>")
    return f"<p>{out}</p>"


def render_front(rec: VocabRecord) -> str:
    if rec.genus in {"el", "la"}:
        return f"{rec.genus} {rec.word}"
    return rec.word


def render_back(rec: VocabRecord) -> str:
    parts: list[str] = []
    if rec.translation_de:
        parts.append(f"<div class=\"translation\">{rec.translation_de}</div>")
    if rec.first_example:
        parts.append(f"<div class=\"example\">{rec.first_example}</div>")
    if rec.mnemonic:
        parts.append(f"<div class=\"mnemonic\">{_md_to_html(rec.mnemonic)}</div>")
    backlink = (
        f"<div class=\"backlink\">"
        f"<a href=\"obsidian://open?vault=repos&amp;file=wiki/language/vocab/{rec.slug}\">"
        f"↗ Wiki: {rec.slug}</a></div>"
    )
    parts.append(backlink)
    return "".join(parts)


def render_tags(rec: VocabRecord) -> list[str]:
    """Anki tags must not contain spaces; replace with underscores."""
    out: list[str] = []
    for t in rec.tags:
        clean = re.sub(r"\s+", "_", t.strip())
        if clean:
            out.append(clean)
    if rec.language:
        out.append(f"language::{rec.language}")
    if rec.difficulty:
        out.append(f"difficulty::{rec.difficulty}")
    return out


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

@dataclass
class ExportSummary:
    exported: list[str] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)  # (slug, reason)
    patched_files: list[str] = field(default_factory=list)
    out_path: Path | None = None
    duration_s: float = 0.0


def run_export(out_path: Path, since: str | None = None) -> ExportSummary:
    summary = ExportSummary()
    t0 = time.perf_counter()

    if not VOCAB_DIR.exists():
        print(f"[ERR] vocab directory not found: {VOCAB_DIR}", file=sys.stderr)
        return summary

    records: list[VocabRecord] = []
    for md in sorted(VOCAB_DIR.glob("*.md")):
        rec = parse_vocab_file(md)
        if rec is None:
            summary.skipped.append((md.stem, "no VocabEntry frontmatter"))
            continue
        if rec.status not in EXPORTABLE_STATUS:
            summary.skipped.append((rec.slug, f"status={rec.status!r}"))
            continue
        if since and rec.updated and rec.updated < since:
            summary.skipped.append((rec.slug, f"updated<{since}"))
            continue
        if not rec.translation_de:
            summary.skipped.append((rec.slug, "no DE translation in body"))
            continue
        records.append(rec)

    deck = genanki.Deck(DECK_ID, DECK_NAME)
    for rec in records:
        guid = rec.anki_id or make_guid(rec.slug)
        if rec.anki_id is None:
            if patch_anki_id(rec.path, guid):
                summary.patched_files.append(rec.slug)
        note = genanki.Note(
            model=ANKI_MODEL,
            fields=[render_front(rec), render_back(rec)],
            tags=render_tags(rec),
            guid=guid,
        )
        deck.add_note(note)
        summary.exported.append(rec.slug)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(out_path))

    summary.out_path = out_path
    summary.duration_s = time.perf_counter() - t0
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> int:
    p = argparse.ArgumentParser(description="Export VocabEntries to an Anki .apkg package.")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT,
                   help=f"Output .apkg path (default: {DEFAULT_OUT.relative_to(REPO_ROOT)})")
    p.add_argument("--since", type=str, default=None,
                   help="Only export entries with frontmatter updated >= YYYY-MM-DD")
    args = p.parse_args()

    if args.since:
        try:
            date.fromisoformat(args.since)
        except ValueError:
            p.error("--since must be YYYY-MM-DD")

    summary = run_export(args.out, since=args.since)

    print(f"Anki export -- {date.today().isoformat()}")
    print(f"  Exported: {len(summary.exported)} cards")
    if summary.exported:
        print(f"    -> {', '.join(summary.exported)}")
    print(f"  Skipped: {len(summary.skipped)}")
    for slug, reason in summary.skipped:
        print(f"    - {slug}: {reason}")
    print(f"  Frontmatter patches (anki_id written): {len(summary.patched_files)}")
    if summary.patched_files:
        print(f"    -> {', '.join(summary.patched_files)}")
    print(f"  Run time: {summary.duration_s:.3f}s")
    if summary.out_path:
        print(f"  File: {summary.out_path}")
    return 0 if summary.exported else 1


if __name__ == "__main__":
    raise SystemExit(_cli())
