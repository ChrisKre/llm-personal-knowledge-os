"""Migration 2026-07-04: ``owner: human``-Flag auf die Health-Seiten (BL-15).

Quelle: Brief 031 (sessions/031_2026-07-04.md, F1) + ENT-062 Punkt 1/3.
Deterministischer Frontmatter-Patch, Direct-Master legitim (ENT-056-§4-Muster,
kein LLM-Write).

Was die Migration tut
=====================
Walkt ``wiki/personal/health/*.md``. Fuer jedes File mit ``type`` aus der
human-owned Familie (``HealthProtocol``/``HealthReview``/``DeepResearchPrompt``):

1. **Clean parse first** (S029-Lehre): ``yaml.safe_load`` auf den unveraenderten
   FM-Block. Schlaegt der Parse fehl, wird das File **nicht repariert**, sondern
   in ``skipped`` ausgewiesen (Brief F5: kaputtes FM ist PO-Eskalation, kein
   eigenmaechtiger Repair-Pfad).
2. Fuegt **eine einzige Zeile** ``owner: human`` in den FM-Block ein — textuell,
   nach der ``created:``-Zeile (sonst nach ``type:``, sonst Block-Ende). Kein
   YAML-Re-Dump: das gesamte File bleibt bis auf diese Zeile **byte-identisch**
   (schaerfer als die S029-Regel "Body byte-identisch").
3. Post-Check: neuer FM-Block parst, ``owner == "human"``, alle uebrigen
   Schluessel/Werte unveraendert. Sonst Abbruch ohne Schreiben.

Was die Migration NICHT tut
===========================
- **Files ohne Frontmatter anfassen** (``antwort_deepresearch.md``) — landet in
  ``skipped``; ob es Frontmatter bekommt, entscheidet der PO (F5).
- **Vorhandene ``owner:``-Werte ueberschreiben** — abweichender Wert ist
  Eskalation, kein Patch.
- **Body oder andere FM-Zeilen aendern.**

Pflicht-Auflagen
================
1. **Backup-Branch** ``backup/pre-owner-flag`` muss existieren, sonst Abbruch.
   ``require_backup_branch=False`` nur fuer Tests.
2. **Idempotenz:** zweiter Lauf liefert ``changed == []`` (bereits geflaggte
   Seiten werden uebersprungen).

Aufruf
======
::

    python scripts/migrations/2026-07-04_owner_flag.py --dry-run
    python scripts/migrations/2026-07-04_owner_flag.py
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

MIGRATION_NAME = "2026-07-04_owner_flag"
BACKUP_BRANCH = "backup/pre-owner-flag"
APPLIED_LOG = REPO_ROOT / "scripts" / "migrations" / "applied.json"

HEALTH_ZONE = Path("wiki") / "personal" / "health"
HUMAN_OWNED_TYPES = ("HealthProtocol", "HealthReview", "DeepResearchPrompt")

_FM_DELIM_RE = re.compile(r"^\s*---\s*$")


def _branch_exists(wiki_root: Path, branch: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        cwd=wiki_root, capture_output=True,
    )
    return result.returncode == 0


def _fm_bounds(lines: list[str]) -> tuple[int, int]:
    """Indices der beiden ``---``-Delimiter-Zeilen, (-1, -1) wenn kein FM."""
    start = end = -1
    for i, line in enumerate(lines):
        if _FM_DELIM_RE.match(line.rstrip("\r\n")):
            if start == -1:
                start = i
            else:
                end = i
                break
    return start, end


def _insert_index(fm_lines: list[str]) -> int:
    """Position der neuen Zeile innerhalb des FM-Blocks (0-basiert).

    Nach der Top-Level-``created:``-Zeile, sonst nach ``type:``, sonst
    Block-Ende. Deterministisch — Pflichtfeld-Reihenfolge aus SCHEMA §3.10
    (type, created, owner).
    """
    for anchor in ("created:", "type:"):
        for i, line in enumerate(fm_lines):
            if line.startswith(anchor):
                return i + 1
    return len(fm_lines)


def _patch_text(raw: str) -> tuple[str | None, str]:
    """Return (patched_text | None, reason). None = skip mit Reason."""
    lines = raw.splitlines(keepends=True)
    start, end = _fm_bounds(lines)
    if start == -1 or end == -1:
        return None, "no frontmatter"

    fm_lines = lines[start + 1:end]
    fm_text = "".join(fm_lines)
    # Clean parse first — kein Repair-Pfad (Brief F5 / S029).
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        return None, f"parse error: {exc.__class__.__name__} (PO-Eskalation)"
    if not isinstance(fm, dict):
        return None, f"frontmatter is {type(fm).__name__}, expected dict"
    if fm.get("type") not in HUMAN_OWNED_TYPES:
        return None, f"type={fm.get('type')!r} not human-owned"
    if fm.get("owner") == "human":
        return None, "already flagged"
    if "owner" in fm:
        return None, f"owner={fm.get('owner')!r} != 'human' (PO-Eskalation)"

    idx = _insert_index(fm_lines)
    anchor = fm_lines[idx - 1] if idx > 0 and fm_lines else ""
    eol = "\r\n" if anchor.endswith("\r\n") else "\n"
    new_fm_lines = fm_lines[:idx] + [f"owner: human{eol}"] + fm_lines[idx:]

    # Post-Check: Patch parst und aendert nichts ausser ``owner``.
    new_fm = yaml.safe_load("".join(new_fm_lines))
    expected = dict(fm, owner="human")
    if new_fm != expected:
        return None, "post-check failed: patched frontmatter drifts"

    patched = "".join(lines[:start + 1] + new_fm_lines + lines[end:])
    return patched, ""


def _update_applied_log(log_path: Path, name: str, ts: str) -> None:
    data = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else {}
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

    zone = root / HEALTH_ZONE
    for path in sorted(zone.glob("*.md")) if zone.exists() else []:
        raw = path.read_bytes().decode("utf-8")
        patched, reason = _patch_text(raw)
        rel = path.relative_to(root).as_posix()
        if patched is None:
            skipped.append(f"{rel} ({reason})")
            continue
        if not dry_run:
            path.write_bytes(patched.encode("utf-8"))
        changed.append(rel)

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
