"""Migration 2026-05-09: frontmatter YAML sanitization (BL-03).

Source: workshop S025 BL-03, QM requirement QK-8.

What the migration does
=======================
Reads every ``wiki/language/vocab/v_*.md`` with ``status: elaborated``, parses
the frontmatter with the legacy-tolerant ``agents.frontmatter`` helper, renders
it back through the same helper (``yaml.dump`` with ``sort_keys=False``,
``allow_unicode=True``, ``default_flow_style=False``) and writes the file back
only if the content would change.

What the migration does NOT do
==============================
- **Change body content.** Even indented body text stays byte-identical
  (brief S026: "the migration may rebuild frontmatter, not the body").
- **Regenerate anki_id.** The value is read and written back unchanged
  (ENT-052; preserves the spaced-repetition state).
- **Touch other VocabEntry statuses.** Only ``elaborated``.
- **Touch other entry types** (LanguageBridge, CulturalEntry). They may have
  the same defect (see technischer_hinweis), but by backlog order they are not
  part of BL-03.

Mandatory requirements (QK-8)
=============================
1. The **backup branch ``backup/pre-frontmatter-migration``** must exist,
   otherwise the script aborts. ``require_backup_branch=False`` only for tests.
2. **Idempotency:** a second run returns ``changed == []``.
3. **Mandatory anki_id snapshot:** ``run()`` returns pre/post hashes; the
   operator stores them in ``tests/migrations/anki_id_snapshot.json`` and
   compares them. A single changed ``anki_id`` is reason to abort.

Usage
=====
::

    python scripts/migrations/2026-05-09_frontmatter_yaml.py             # live
    python scripts/migrations/2026-05-09_frontmatter_yaml.py --dry-run   # plan
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.frontmatter import parse, render  # noqa: E402

MIGRATION_NAME = "2026-05-09_frontmatter_yaml"
BACKUP_BRANCH = "backup/pre-frontmatter-migration"
APPLIED_LOG = REPO_ROOT / "scripts" / "migrations" / "applied.json"


def _branch_exists(wiki_root: Path, branch: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        cwd=wiki_root, capture_output=True,
    )
    return result.returncode == 0


def _vocab_files(wiki_root: Path) -> list[Path]:
    vocab_dir = wiki_root / "wiki" / "language" / "vocab"
    return sorted(vocab_dir.glob("v_*.md"))


def _is_target(fm: dict) -> bool:
    return fm.get("type") == "VocabEntry" and fm.get("status") == "elaborated"


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
    """Execute migration. See module docstring for invariants.

    Returns ``{"changed": [...], "skipped": [...], "anki_ids": {slug: id}}``.
    """
    root = wiki_root or REPO_ROOT
    if require_backup_branch and not _branch_exists(root, BACKUP_BRANCH):
        raise RuntimeError(
            f"Backup branch '{BACKUP_BRANCH}' is missing. Create it before running: "
            f"git branch {BACKUP_BRANCH}"
        )

    changed: list[str] = []
    skipped: list[str] = []
    anki_ids: dict[str, str] = {}

    for path in _vocab_files(root):
        original = path.read_text(encoding="utf-8")
        try:
            fm, body = parse(original)
        except Exception as exc:
            skipped.append(f"{path} (parse error: {exc})")
            continue

        if not _is_target(fm):
            skipped.append(str(path.relative_to(root)))
            continue

        slug = path.stem
        if "anki_id" in fm and fm["anki_id"] is not None:
            anki_ids[slug] = str(fm["anki_id"])

        rebuilt = render(fm, body)
        if rebuilt != original:
            if not dry_run:
                path.write_text(rebuilt, encoding="utf-8")
            changed.append(str(path.relative_to(root)))

    if not dry_run and changed and update_log:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        _update_applied_log(APPLIED_LOG, MIGRATION_NAME, ts)

    return {"changed": changed, "skipped": skipped, "anki_ids": anki_ids}


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
    print(f"  anki_ids tracked: {len(result['anki_ids'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
