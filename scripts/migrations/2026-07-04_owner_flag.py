"""Migration 2026-07-04: ``owner: human`` flag on the health pages (BL-15).

Source: brief 031 (sessions/031_2026-07-04.md, F1) + ENT-062 points 1/3.
A deterministic frontmatter patch; committing directly to master is legitimate
(ENT-056 §4 pattern, no LLM write).

What the migration does
=======================
Walks ``wiki/personal/health/*.md``. For each file whose ``type`` belongs to
the human-owned family (``HealthProtocol``/``HealthReview``/``DeepResearchPrompt``):

1. **Clean parse first** (lesson from S029): ``yaml.safe_load`` on the
   unmodified FM block. If parsing fails, the file is **not repaired** but
   reported in ``skipped`` (brief F5: broken FM is a PO escalation, not a
   self-directed repair path).
2. Inserts **a single line** ``owner: human`` into the FM block, textually,
   after the ``created:`` line (else after ``type:``, else at the block end).
   No YAML re-dump: apart from this line the whole file stays **byte-identical**
   (stricter than the S029 rule "body byte-identical").
3. Post-check: the new FM block parses, ``owner == "human"``, all other
   keys/values are unchanged. Otherwise abort without writing.

What the migration does NOT do
==============================
- **Touch files without frontmatter** — they end up in ``skipped``; whether
  they get frontmatter is the PO's decision (F5).
- **Overwrite existing ``owner:`` values** — a different value is an
  escalation, not a patch.
- **Change the body or any other FM line.**

Mandatory requirements
======================
1. The **backup branch** ``backup/pre-owner-flag`` must exist, otherwise abort.
   ``require_backup_branch=False`` only for tests.
2. **Idempotency:** a second run returns ``changed == []`` (pages that are
   already flagged are skipped).

Usage
=====
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
    """Indices of the two ``---`` delimiter lines, (-1, -1) if there is no FM."""
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
    """Position of the new line within the FM block (0-based).

    After the top-level ``created:`` line, else after ``type:``, else at the
    block end. Deterministic; follows the required-field order from
    SCHEMA §3.10 (type, created, owner).
    """
    for anchor in ("created:", "type:"):
        for i, line in enumerate(fm_lines):
            if line.startswith(anchor):
                return i + 1
    return len(fm_lines)


def _patch_text(raw: str) -> tuple[str | None, str]:
    """Return (patched_text | None, reason). None = skip with a reason."""
    lines = raw.splitlines(keepends=True)
    start, end = _fm_bounds(lines)
    if start == -1 or end == -1:
        return None, "no frontmatter"

    fm_lines = lines[start + 1:end]
    fm_text = "".join(fm_lines)
    # Clean parse first — no repair path (brief F5 / S029).
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        return None, f"parse error: {exc.__class__.__name__} (PO escalation)"
    if not isinstance(fm, dict):
        return None, f"frontmatter is {type(fm).__name__}, expected dict"
    if fm.get("type") not in HUMAN_OWNED_TYPES:
        return None, f"type={fm.get('type')!r} not human-owned"
    if fm.get("owner") == "human":
        return None, "already flagged"
    if "owner" in fm:
        return None, f"owner={fm.get('owner')!r} != 'human' (PO escalation)"

    idx = _insert_index(fm_lines)
    anchor = fm_lines[idx - 1] if idx > 0 and fm_lines else ""
    eol = "\r\n" if anchor.endswith("\r\n") else "\n"
    new_fm_lines = fm_lines[:idx] + [f"owner: human{eol}"] + fm_lines[idx:]

    # Post-check: the patch parses and changes nothing except ``owner``.
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
    """Execute the migration. See the module docstring for invariants.

    Returns ``{"changed": [...], "skipped": [...]}``.
    """
    root = wiki_root or REPO_ROOT
    if require_backup_branch and not _branch_exists(root, BACKUP_BRANCH):
        raise RuntimeError(
            f"Backup branch '{BACKUP_BRANCH}' is missing. Create it before running: "
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
                        help="Plan only, do not write.")
    parser.add_argument("--skip-backup-check", action="store_true",
                        help="Skip the backup branch check (tests/local only).")
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
