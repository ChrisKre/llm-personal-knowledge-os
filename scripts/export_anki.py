"""export_anki.py — VocabEntry → .apkg Exporter (MVP-2-Zweitwelle, Session 023).

Implementiert ENT-050/051/052:
  - Quelle: wiki/language/vocab/*.md mit status: elaborated|practiced
  - Identität: anki_id = sha1("pks-vocab-" + slug)[:16], in Frontmatter persistiert
  - Karte: Front=ES-Wort (mit Genus-Präfix wenn parsbar), Back=DE + Beispiel + Eselsbrücke
  - Tags: Frontmatter-Tags + language::es + difficulty::<CEFR>
  - Bridges werden NICHT exportiert (ENT-051)

Aufruf:
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

REPO_ROOT = Path(__file__).resolve().parent.parent
VOCAB_DIR = REPO_ROOT / "wiki" / "language" / "vocab"
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


_FM_DELIM_RE = re.compile(r"^\s*---\s*$")


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_block, body) — both as raw strings.

    Robust against the leading-whitespace dedent-bug in legacy vocab files
    (each line may carry up to ~16 spaces of indent).
    """
    lines = text.splitlines()
    start = end = -1
    for i, line in enumerate(lines):
        if _FM_DELIM_RE.match(line):
            if start == -1:
                start = i
            else:
                end = i
                break
    if start == -1 or end == -1:
        return "", text
    fm = "\n".join(lines[start + 1:end])
    body = "\n".join(lines[end + 1:])
    return fm, body


_TAGS_RE = re.compile(r"^\s*tags:\s*\[([^\]]*)\]\s*$")
_KV_RE = re.compile(r"^\s*([a-zA-Z_][\w]*)\s*:\s*(.*?)\s*$")


_WANTED_KEYS = {"type", "created", "updated", "status", "word", "language",
                "difficulty", "anki_id"}


def _parse_frontmatter(fm: str) -> dict:
    """Pull the top-level scalar fields we care about out of the frontmatter.

    Skips yaml.safe_load because legacy files have inconsistent indent that
    pyyaml refuses. First occurrence wins — guards against nested duplicates
    like 'type: ?' under cross_language_bridges shadowing 'type: VocabEntry'.
    """
    out: dict = {}
    for raw_line in fm.splitlines():
        m_tags = _TAGS_RE.match(raw_line)
        if m_tags and "tags" not in out:
            tags_inner = m_tags.group(1).strip()
            tags = [t.strip().strip('"').strip("'") for t in tags_inner.split(",") if t.strip()]
            out["tags"] = tags
            continue
        m_kv = _KV_RE.match(raw_line)
        if not m_kv:
            continue
        key = m_kv.group(1)
        if key in _WANTED_KEYS and key not in out:
            val = m_kv.group(2).strip().strip('"').strip("'")
            out[key] = val
    return out


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


def parse_vocab_file(path: Path) -> VocabRecord | None:
    text = path.read_text(encoding="utf-8")
    fm_block, body = _split_frontmatter(text)
    if not fm_block:
        return None
    fm = _parse_frontmatter(fm_block)
    if fm.get("type") != "VocabEntry":
        return None
    slug = path.stem
    anki_id = fm.get("anki_id")
    if anki_id in (None, "", "null", "~"):
        anki_id = None
    return VocabRecord(
        slug=slug,
        path=path,
        word=fm.get("word", "").strip() or slug,
        language=fm.get("language", "").strip(),
        status=fm.get("status", "").strip(),
        difficulty=(fm.get("difficulty") or None),
        updated=(fm.get("updated") or None),
        anki_id=anki_id,
        tags=fm.get("tags", []),
        genus=_extract_genus(body),
        translation_de=_extract_de(body),
        first_example=_extract_first_example(body),
        mnemonic=_extract_mnemonic(body),
    )


# ---------------------------------------------------------------------------
# Frontmatter patch (anki_id back-write)
# ---------------------------------------------------------------------------

_ANKI_ID_LINE_RE = re.compile(r"^(\s*)anki_id\s*:\s*.*$", re.MULTILINE)


def patch_anki_id(path: Path, new_id: str) -> bool:
    """Set frontmatter anki_id to new_id. Idempotent.

    Returns True if the file was changed. Preserves indentation so
    re-runs over a file already carrying the correct id are no-ops.
    """
    text = path.read_text(encoding="utf-8")
    m = _ANKI_ID_LINE_RE.search(text)
    if not m:
        return False
    new_line = f"{m.group(1)}anki_id: {new_id}"
    new_text = text[:m.start()] + new_line + text[m.end():]
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
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
        print(f"[ERR] Vocab-Verzeichnis nicht gefunden: {VOCAB_DIR}", file=sys.stderr)
        return summary

    records: list[VocabRecord] = []
    for md in sorted(VOCAB_DIR.glob("*.md")):
        rec = parse_vocab_file(md)
        if rec is None:
            summary.skipped.append((md.stem, "kein VocabEntry-Frontmatter"))
            continue
        if rec.status not in EXPORTABLE_STATUS:
            summary.skipped.append((rec.slug, f"status={rec.status!r}"))
            continue
        if since and rec.updated and rec.updated < since:
            summary.skipped.append((rec.slug, f"updated<{since}"))
            continue
        if not rec.translation_de:
            summary.skipped.append((rec.slug, "keine DE-Übersetzung im Body"))
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

    print(f"Anki-Export -- {date.today().isoformat()}")
    print(f"  Exportiert: {len(summary.exported)} Karten")
    if summary.exported:
        print(f"    -> {', '.join(summary.exported)}")
    print(f"  Uebersprungen: {len(summary.skipped)}")
    for slug, reason in summary.skipped:
        print(f"    - {slug}: {reason}")
    print(f"  Frontmatter-Patches (anki_id geschrieben): {len(summary.patched_files)}")
    if summary.patched_files:
        print(f"    -> {', '.join(summary.patched_files)}")
    print(f"  Lauf-Zeit: {summary.duration_s:.3f}s")
    if summary.out_path:
        print(f"  Datei: {summary.out_path}")
    return 0 if summary.exported else 1


if __name__ == "__main__":
    raise SystemExit(_cli())
