"""Migration 2026-05-09: CulturalEntry-Frontmatter-Reparatur.

Quelle: Brief 029 (sessions/029_2026-05-09.md), Eskalation 1 aus S027.
Direkte Schwester von BL-03 — gleiches Skript-Skelett, **ohne**
``anki_id``-Snapshot (CulturalEntries haben keine Anki-Karten).

Was die Migration tut
=====================
Walkt ``wiki/language/culture/c_*.md``. Fuer jedes File:

1. ``_split`` trennt Frontmatter und Body.
2. ``agents.frontmatter._normalize_legacy_fm`` dedented + repariert
   ``key: ?`` (BL-03-Pfad).
3. **Migration-lokale Repair-Pfade:**
   - Triple-Bracket-Strip: ``[[[X]]]`` -> ``"[[X]]"`` (Obsidian-Defekt;
     ohne Quotes wuerde YAML ``[[X]]`` als verschachtelte Flow-Liste lesen).
   - Re-Indent fuer aus-dem-Block-gefallene Listen-Eintraege: erste
     ``- ``-Zeile unter einem ``key:``-Opener setzt den Item-Indent;
     nachfolgende ``- ``-Items snappen darauf, Continuation-``key:``-Zeilen
     auf Item-Indent + 2.
4. ``yaml.safe_load`` parst das reparierte YAML.
5. ``render(fm, body)`` schreibt das File zurueck (Body byte-identisch nach
   FM-Trennung; Property-Reihenfolge erhalten via ``sort_keys=False``).

Was die Migration NICHT tut
===========================
- **Body-Inhalt aendern.** Auch eingerueckter Body-Text bleibt erhalten
  (Brief S026/S027-Regel; die Body-Indentation ist Renderer-Frage und
  gehoert zu BL-05 oder einer separaten Body-Indent-Migration).
- **anki_id anfassen.** CulturalEntries haben keine Anki-Karten; der
  Snapshot-Schritt aus QK-8 entfaellt explizit.
- **agents.frontmatter erweitern.** Triple-Bracket-Strip + Popped-List-
  Re-Indent leben **hier**, nicht in der zentralen API (Brief 029
  Scope-Schutz Punkt 2). Tritt das Defekt-Muster ein zweites Mal auf,
  ist eine API-Erweiterung Architekt-Eskalation an PO.
- **Andere Entry-Typen anfassen.** Nur ``wiki/language/culture/c_*.md``.

Pflicht-Auflagen
================
1. **Backup-Branch** ``backup/pre-cultural-frontmatter-migration`` muss
   existieren, sonst bricht das Skript ab. ``require_backup_branch=False``
   nur fuer Tests.
2. **Idempotenz:** zweiter Lauf liefert ``changed == []``.

Aufruf
======
::

    python scripts/migrations/2026-05-09_cultural_frontmatter.py
    python scripts/migrations/2026-05-09_cultural_frontmatter.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402
from agents.frontmatter import _normalize_legacy_fm, _split, render  # noqa: E402

MIGRATION_NAME = "2026-05-09_cultural_frontmatter"
BACKUP_BRANCH = "backup/pre-cultural-frontmatter-migration"
APPLIED_LOG = REPO_ROOT / "scripts" / "migrations" / "applied.json"


_TRIPLE_BRACKET_RE = re.compile(r"\[\[\[([^\[\]]+?)\]\]\]")
_KEY_OPENER_RE = re.compile(r"^\s*[A-Za-z_][\w-]*:\s*$")
_KV_RE = re.compile(r"^\s*[A-Za-z_][\w-]*:")
_LIST_ITEM_RE = re.compile(r"^\s*- ")


def _branch_exists(wiki_root: Path, branch: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        cwd=wiki_root, capture_output=True,
    )
    return result.returncode == 0


def _culture_files(wiki_root: Path) -> list[Path]:
    culture_dir = wiki_root / "wiki" / "language" / "culture"
    if not culture_dir.exists():
        return []
    return sorted(culture_dir.glob("c_*.md"))


def _strip_triple_brackets(fm_text: str) -> str:
    """Konvertiere ``[[[X]]]`` in den quoted Wikilink ``"[[X]]"``.

    Reines ``[[X]]`` waere YAML-flow-list-of-list (parst zu ``[['X']]``),
    deshalb Double-Quotes statt Single-Quotes — die rohe Wikilink-Form
    enthaelt keine Double-Quotes, also kein Escape noetig.
    """
    return _TRIPLE_BRACKET_RE.sub(r'"[[\1]]"', fm_text)


def _repair_popped_list(fm_text: str) -> str:
    """Re-anker Listen-Eintraege, die aus ihrem Parent-Block gepoppt sind.

    Heuristik:
    - Ein ``key:``-Opener (Zeile = nur ``key:`` ohne Wert) startet einen Block
      mit Parent-Indent = Leading-Whitespace.
    - Die erste ``- ``-Zeile unter dem Opener definiert den Item-Indent.
    - Nachfolgende ``- ``-Items werden auf den Item-Indent gesnappt.
    - Continuation-``key:``-Zeilen (Mapping-Schluessel ohne ``- ``-Prefix)
      werden auf Item-Indent + 2 gesnappt.
    - Block endet bei: Leerzeile ODER neue Top-Level-``key:``-Zeile mit
      Indent <= Parent-Indent.

    Auf bereits sauberem YAML (Post-render-Output) ist die Funktion
    fixpunkt-stabil: erste ``- ``-Zeile setzt Item-Indent = Leading, und
    nachfolgende Zeilen ueberschreiben sich selbst mit identischem Indent.
    """
    lines = fm_text.splitlines()
    out: list[str] = []
    in_block = False
    parent_indent = -1
    item_indent: int | None = None

    for raw in lines:
        stripped_left = raw.lstrip(" ")
        stripped = stripped_left.rstrip()
        leading = len(raw) - len(stripped_left)

        # Block end: leere Zeile.
        if in_block and not stripped:
            in_block = False
            out.append(raw)
            continue

        # Block end / new top-level key.
        if in_block and leading <= parent_indent and _KV_RE.match(raw):
            in_block = False
            # falls der neue Key selbst wieder Block-Opener ist, sofort re-aktivieren
            if _KEY_OPENER_RE.match(raw):
                in_block = True
                parent_indent = leading
                item_indent = None
            out.append(raw)
            continue

        if not in_block and _KEY_OPENER_RE.match(raw):
            in_block = True
            parent_indent = leading
            item_indent = None
            out.append(raw)
            continue

        if in_block and _LIST_ITEM_RE.match(raw):
            if item_indent is None:
                # Erstes Item legt den Anker fest.
                item_indent = leading
            out.append(" " * item_indent + stripped_left)
            continue

        if (
            in_block
            and item_indent is not None
            and _KV_RE.match(raw)
            and not _LIST_ITEM_RE.match(raw)
        ):
            out.append(" " * (item_indent + 2) + stripped_left)
            continue

        out.append(raw)

    return "\n".join(out)


def _repair_culture_fm(fm_raw: str) -> str:
    """Voller Repair-Pfad: dedent + bare-? + Triple-Bracket-Strip + Re-Indent."""
    norm = _normalize_legacy_fm(fm_raw)
    norm = _strip_triple_brackets(norm)
    norm = _repair_popped_list(norm)
    return norm


def _update_applied_log(log_path: Path, name: str, ts: str) -> None:
    if log_path.exists():
        data = json.loads(log_path.read_text(encoding="utf-8"))
    else:
        data = {}
    data[name] = ts
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run(
    wiki_root: Path | None = None,
    *,
    require_backup_branch: bool = True,
    dry_run: bool = False,
    update_log: bool = True,
) -> dict:
    """Execute migration. Siehe Modul-Docstring fuer Invarianten.

    Returns ``{"changed": [...], "skipped": [...]}``.
    """
    root = wiki_root or REPO_ROOT
    if require_backup_branch and not _branch_exists(root, BACKUP_BRANCH):
        raise RuntimeError(
            f"Backup-Branch '{BACKUP_BRANCH}' fehlt. Vor Lauf erzeugen: "
            f"git branch {BACKUP_BRANCH}"
        )

    changed: list[str] = []
    skipped: list[str] = []

    for path in _culture_files(root):
        original = path.read_text(encoding="utf-8")
        fm_raw, body, _ = _split(original)
        if not fm_raw:
            skipped.append(f"{path.relative_to(root)} (no frontmatter)")
            continue

        # BL-03-Pattern: erst sauberen Parse versuchen (Idempotenz auf bereits
        # migrierten Files). Nur wenn das fehlschlaegt, den Migration-Repair-Pfad
        # zuenden — denn _normalize_legacy_fm wuerde die 2-Space-Continuation-
        # Indents im sauberen Output als haeufigsten Prefix erkennen und strippen,
        # was Block-Mappings unter Listen-Items aufbricht.
        fm = None
        try:
            fm = yaml.safe_load(fm_raw)
        except yaml.YAMLError:
            fm = None
        if not isinstance(fm, dict):
            repaired = _repair_culture_fm(fm_raw)
            try:
                fm = yaml.safe_load(repaired)
            except yaml.YAMLError as exc:
                skipped.append(
                    f"{path.relative_to(root)} (parse error: {exc.__class__.__name__})"
                )
                continue
            if not isinstance(fm, dict):
                skipped.append(
                    f"{path.relative_to(root)} (frontmatter is {type(fm).__name__}, expected dict)"
                )
                continue
        if fm.get("type") != "CulturalEntry":
            skipped.append(str(path.relative_to(root)))
            continue

        rebuilt = render(fm, body)
        if rebuilt != original:
            if not dry_run:
                path.write_text(rebuilt, encoding="utf-8")
            changed.append(str(path.relative_to(root)))

    if not dry_run and changed and update_log:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        _update_applied_log(APPLIED_LOG, MIGRATION_NAME, ts)

    return {"changed": changed, "skipped": skipped}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="Nur planen, nicht schreiben.")
    parser.add_argument("--skip-backup-check", action="store_true",
                        help="Pre-Backup-Check ueberspringen (nur Tests/Local).")
    args = parser.parse_args(argv)

    try:
        result = run(
            require_backup_branch=not args.skip_backup_check,
            dry_run=args.dry_run,
        )
    except RuntimeError as exc:
        print(f"[ABORT] {exc}", file=sys.stderr)
        return 2

    print(f"[{MIGRATION_NAME}] mode={'dry-run' if args.dry_run else 'live'}")
    print(f"  changed: {len(result['changed'])}")
    for p in result["changed"]:
        print(f"    M {p}")
    print(f"  skipped: {len(result['skipped'])}")
    for p in result["skipped"]:
        print(f"    - {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
