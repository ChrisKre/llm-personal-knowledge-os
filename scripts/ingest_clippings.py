"""ingest_clippings.py — batch ingestion of web clippings, stage 0 (BL-16).

Source: ENT-058 (channel K2 + extractor contract), 02 §B2 (stage sketch +
idempotency definition), QM R12/QK-21, brief 032. Conventions from
``scripts/migrations/`` (backup branch check, idempotency, ledger, dry run)
and ``scripts/rebuild_index.py`` (``run()`` signature, report style).

What the script does (stage 0, deterministic, $0)
=================================================
Walks ``SOURCE_DIRS`` (``scripts/ingest``) in the vault, extracts title /
canonical ID / word count per file (extractor contract (a)–(f), see
``scripts/ingest/stage0.py``), filters ledgered IDs, deduplicates in three
stages (byte / canonical ID / SequenceMatcher ≥ 0.9) and writes:

- ``out/ingest/inventory_plan.json``  — inventory plan (build artifact,
  gitignored, ENT-054 pattern)
- ``out/ingest/inventory_report.md``  — human-readable report
  (counts: usable / dupe / empty / not_a_clipping / ledgered)

What the script does NOT do
===========================
- **No LLM call** (stages 1–5 are S033/BL-17; if stage 0 contains even one
  LLM call, the scope is missed; brief 032, scope protection).
- **No write to ``wiki/``**, no draft path (``graph_writer``/ENT-059 only
  become productive with BL-17).
- **No byte in ``raw/`` is changed**; the mounts are only read.

Modes
=====
- ``--dry-run`` is the **default** and stops after stage 0: plan + report,
  no ledger writes.
- ``--live`` requires the backup branch ``backup/pre-clippings-batch`` in the
  vault repo (the check aborts otherwise; the branch itself is only created
  right before the real batch) and writes ``skipped`` ledger entries for
  definitive skips (``empty_clip``/``dupe``). Not ledgered are:
  (a) ``usable`` files — their ``merged`` entry is only written atomically by
  stage 5 (QK-17a); (b) ``not_a_clipping`` files — without a canonical ID
  there is no ledger key, so they deliberately stay visible in every report;
  (c) dupes whose ID is shared with a ``usable`` file (same ``yt:`` ID as the
  keeper — a skip entry would filter out the keeper too).
- ``--reconstruct-ledger``: self-healing from ``wiki/topics/`` (02 §B2);
  writes only together with ``--live``, otherwise prints the plan.

Usage
=====
::

    python scripts/ingest_clippings.py                        # dry run
    python scripts/ingest_clippings.py --live                 # ledger write
    python scripts/ingest_clippings.py --reconstruct-ledger   # self-healing
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / ".env")  # before agents.config (KOS_VAULT_ROOT)

from agents.config import VAULT_ROOT  # noqa: E402
from scripts.ingest import (  # noqa: E402
    BACKUP_BRANCH,
    LEDGER_PATH,
    SOURCE_DIRS,
)
from scripts.ingest.ledger import (  # noqa: E402
    load_ledger,
    make_skip_entry,
    reconstruct_ledger,
    save_ledger,
)
from scripts.ingest.stage0 import (  # noqa: E402
    ClipRecord,
    dedup,
    extract_clip,
    walk_sources,
)

OUT_DIR = REPO_ROOT / "out" / "ingest"

STATUS_ORDER = ("usable", "dupe", "empty_clip", "not_a_clipping", "ledgered")


def _branch_exists(repo_root: Path, branch: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        cwd=repo_root, capture_output=True,
    )
    return result.returncode == 0


def _counts(records: list[ClipRecord]) -> dict[str, int]:
    counts = {status: 0 for status in STATUS_ORDER}
    for rec in records:
        counts[rec.status] += 1
    counts["files"] = len(records)
    return counts


def _plan_dict(records: list[ClipRecord], counts: dict[str, int],
               mode: str, ts: str) -> dict[str, Any]:
    return {
        "generated": ts,
        "mode": mode,
        "stage": 0,
        "source_dirs": list(SOURCE_DIRS),
        "counts": counts,
        "clips": [
            {
                "path": r.path,
                "title": r.title,
                "format": r.fmt,
                "id": r.canonical_id,
                "words": r.words,
                "created": r.created,
                "status": r.status,
                "reason": r.reason,
                "dupe_of": r.dupe_of,
                "dedup_tier": r.dedup_tier,
            }
            for r in records
        ],
    }


def _report(records: list[ClipRecord], counts: dict[str, int],
            mode: str, ts: str) -> str:
    md = sum(1 for r in records if r.fmt == "md")
    html = sum(1 for r in records if r.fmt == "html")
    lines = [
        "# Inventory report — clippings ingestion stage 0",
        f"> Generated: {ts} | Mode: {mode} | Source: {', '.join(SOURCE_DIRS)}",
        "",
        f"**Total files: {counts['files']}** (md {md} / html {html})",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status in STATUS_ORDER:
        lines.append(f"| {status} | {counts[status]} |")
    lines.append("")

    def _section(title: str, rows: list[str]) -> None:
        if rows:
            lines.append(f"## {title}")
            lines.extend(rows)
            lines.append("")

    _section("Dupes", [
        f"- `{r.path}` → keeper `{r.dupe_of}` (stage: {r.dedup_tier})"
        for r in records if r.status == "dupe"])
    _section("Empty clips (empty_clip)", [
        f"- `{r.path}` — {r.reason}"
        for r in records if r.status == "empty_clip"])
    _section("Not a clipping (not_a_clipping, QM R12)", [
        f"- `{r.path}` — {r.reason}"
        for r in records if r.status == "not_a_clipping"])
    _section("Already processed (ledgered)", [
        f"- `{r.path}` — {r.reason}"
        for r in records if r.status == "ledgered"])
    _section("No-frontmatter fallback (sha1: ID)", [
        f"- `{r.path}` → `{r.canonical_id}` ({r.status})"
        for r in records
        if r.canonical_id and r.canonical_id.startswith("sha1:")])
    return "\n".join(lines).rstrip() + "\n"


def run(
    repo_root: Path = VAULT_ROOT,
    *,
    dry_run: bool = True,
    require_backup_branch: bool = True,
    ledger_path: Path | None = None,
    out_dir: Path | None = None,
    source_dirs: tuple[str, ...] = SOURCE_DIRS,
) -> dict[str, Any]:
    """Run stage 0. Return keys: ``records``, ``counts``, ``plan``,
    ``report`` (str), ``plan_path``/``report_path``, ``ledger_written``
    (list of new ledger IDs), ``nothing_to_do``.
    """
    ledger_path = ledger_path or LEDGER_PATH
    out_dir = out_dir or OUT_DIR
    mode = "dry-run" if dry_run else "live"

    if not dry_run and require_backup_branch and \
            not _branch_exists(repo_root, BACKUP_BRANCH):
        raise RuntimeError(
            f"Backup branch '{BACKUP_BRANCH}' is missing. Create it before a live run: "
            f"git branch {BACKUP_BRANCH}"
        )

    ledger = load_ledger(ledger_path)
    records = [extract_clip(p, repo_root)
               for p in walk_sources(repo_root, source_dirs)]

    # Idempotency (02 §B2): filter ledgered IDs first, before dedup,
    # so an already processed keeper does not compete again.
    for rec in records:
        if rec.canonical_id and rec.canonical_id in ledger:
            rec.status = "ledgered"
            rec.reason = (
                f"in ledger: {ledger[rec.canonical_id].get('status')} "
                f"({ledger[rec.canonical_id].get('reason', '')})".strip()
            )

    dedup(records)

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    counts = _counts(records)
    plan = _plan_dict(records, counts, mode, ts)
    report = _report(records, counts, mode, ts)

    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = out_dir / "inventory_plan.json"
    report_path = out_dir / "inventory_report.md"
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8", newline="\n")
    report_path.write_text(report, encoding="utf-8", newline="\n")

    # Live: skipped entries for definitive skips (see the module docstring).
    ledger_written: list[str] = []
    if not dry_run:
        usable_ids = {r.canonical_id for r in records if r.status == "usable"}
        for rec in records:
            if rec.status not in ("empty_clip", "dupe"):
                continue
            cid = rec.canonical_id
            if not cid or cid in ledger or cid in usable_ids:
                continue
            ledger[cid] = make_skip_entry(f"{rec.status}: {rec.reason}", ts)
            ledger_written.append(cid)
        if ledger_written:
            save_ledger(ledger, ledger_path)

    nothing_to_do = not any(
        r.status in ("usable", "dupe", "empty_clip") for r in records)

    return {
        "records": records,
        "counts": counts,
        "plan": plan,
        "report": report,
        "plan_path": plan_path,
        "report_path": report_path,
        "ledger_written": ledger_written,
        "nothing_to_do": nothing_to_do,
    }


def _cli() -> int:
    # The Windows console is cp1252; the report contains UTF-8 (→, umlauts).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(
        description="Clippings batch stage 0: inventory/dedup/ledger ($0).")
    p.add_argument("--dry-run", action="store_true", default=True,
                   help="Default: plan + report, no ledger writes.")
    p.add_argument("--live", action="store_true",
                   help="Write the ledger; requires the backup branch "
                        f"'{BACKUP_BRANCH}'.")
    p.add_argument("--skip-backup-check", action="store_true",
                   help="Skip the backup branch check (tests/local only).")
    p.add_argument("--reconstruct-ledger", action="store_true",
                   help="Self-healing: rebuild the ledger from wiki/topics/ "
                        "(writes only with --live).")
    args = p.parse_args()
    dry_run = not args.live

    if args.reconstruct_ledger:
        entries = reconstruct_ledger(VAULT_ROOT)
        print(f"[reconstruct-ledger] {len(entries)} IDs from wiki/topics/")
        for sid, entry in sorted(entries.items()):
            print(f"  {sid} → {entry['topic_pages']}")
        if dry_run:
            print("  (dry run — nothing written; use --live to write)")
        else:
            save_ledger(entries)
            print(f"  written: {LEDGER_PATH}")
        return 0

    try:
        result = run(
            dry_run=dry_run,
            require_backup_branch=not args.skip_backup_check,
        )
    except RuntimeError as exc:
        print(f"[ABORT] {exc}", file=sys.stderr)
        return 2

    print(result["report"])
    print(f"Plan:   {result['plan_path'].relative_to(REPO_ROOT)}")
    print(f"Report: {result['report_path'].relative_to(REPO_ROOT)}")
    if not dry_run:
        print(f"Ledger: {len(result['ledger_written'])} new skipped entries")
    if result["nothing_to_do"]:
        print("nothing to do — all clips ledgered or no input.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
