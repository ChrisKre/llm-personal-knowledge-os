"""Migration 2026-05-09: CulturalEntry frontmatter repair.

Source: brief 029 (sessions/029_2026-05-09.md), escalation 1 from S027.
Direct sibling of BL-03 — same script skeleton, **without** the ``anki_id``
snapshot (CulturalEntries have no Anki cards).

What the migration does
=======================
Walks ``wiki/language/culture/c_*.md``. For each file:

1. ``_split`` separates frontmatter and body.
2. ``agents.frontmatter._normalize_legacy_fm`` dedents and repairs
   ``key: ?`` (BL-03 path).
3. **Migration-local repair paths:**
   - Triple-bracket strip: ``[[[X]]]`` -> ``"[[X]]"`` (an Obsidian defect;
     without quotes YAML would read ``[[X]]`` as a nested flow list).
   - Re-indent for list items that fell out of their block: the first
     ``- `` line under a ``key:`` opener sets the item indent; following
     ``- `` items snap to it, continuation ``key:`` lines to item indent + 2.
4. ``yaml.safe_load`` parses the repaired YAML.
5. ``render(fm, body)`` writes the file back (body byte-identical after the
   FM split; property order preserved via ``sort_keys=False``).

What the migration does NOT do
==============================
- **Change body content.** Even indented body text is preserved (rule from
  briefs S026/S027; body indentation is a renderer question and belongs to
  BL-05 or a separate body-indent migration).
- **Touch anki_id.** CulturalEntries have no Anki cards; the snapshot step
  from QK-8 is explicitly dropped.
- **Extend agents.frontmatter.** The triple-bracket strip and the popped-list
  re-indent live **here**, not in the central API (brief 029, scope
  protection point 2). If the defect pattern shows up a second time, an API
  extension is an architect escalation to the PO.
- **Touch other entry types.** Only ``wiki/language/culture/c_*.md``.

Mandatory requirements
======================
1. The **backup branch** ``backup/pre-cultural-frontmatter-migration`` must
   exist, otherwise the script aborts. ``require_backup_branch=False`` only
   for tests.
2. **Idempotency:** a second run returns ``changed == []``.

Usage
=====
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
    """Convert ``[[[X]]]`` into the quoted wikilink ``"[[X]]"``.

    A bare ``[[X]]`` would be a YAML flow list of lists (parses to ``[['X']]``),
    hence double quotes rather than single quotes; the raw wikilink form
    contains no double quotes, so no escaping is needed.
    """
    return _TRIPLE_BRACKET_RE.sub(r'"[[\1]]"', fm_text)


def _repair_popped_list(fm_text: str) -> str:
    """Re-anchor list items that popped out of their parent block.

    Heuristic:
    - A ``key:`` opener (a line with only ``key:`` and no value) starts a
      block with parent indent = its leading whitespace.
    - The first ``- `` line under the opener defines the item indent.
    - Following ``- `` items are snapped to the item indent.
    - Continuation ``key:`` lines (mapping keys without a ``- `` prefix)
      are snapped to item indent + 2.
    - The block ends at an empty line OR a new top-level ``key:`` line with
      indent <= parent indent.

    On already clean YAML (post-render output) the function is a fixed
    point: the first ``- `` line sets item indent = its leading whitespace,
    and the following lines overwrite themselves with the same indent.
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

        # Block end: empty line.
        if in_block and not stripped:
            in_block = False
            out.append(raw)
            continue

        # Block end / new top-level key.
        if in_block and leading <= parent_indent and _KV_RE.match(raw):
            in_block = False
            # if the new key is itself a block opener, re-activate right away
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
                # The first item sets the anchor.
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
    """Full repair path: dedent + bare ? + triple-bracket strip + re-indent."""
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

    for path in _culture_files(root):
        original = path.read_text(encoding="utf-8")
        fm_raw, body, _ = _split(original)
        if not fm_raw:
            skipped.append(f"{path.relative_to(root)} (no frontmatter)")
            continue

        # BL-03 pattern: try a clean parse first (idempotency on files that are
        # already migrated). Only if that fails, use the migration repair path,
        # because _normalize_legacy_fm would see the 2-space continuation
        # indents in clean output as the most common prefix and strip them,
        # which breaks block mappings under list items.
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
