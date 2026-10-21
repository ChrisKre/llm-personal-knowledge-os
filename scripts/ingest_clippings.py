"""ingest_clippings.py — Batch-Ingestion der Clippings, Stufe 0 (BL-16).

Quelle: ENT-058 (Kanal K2 + Extractor-Vertrag), 02 §B2 (Stufen-Skizze +
Idempotenz-Definition), QM R12/QK-21, Brief 032. Konventionen aus
``scripts/migrations/`` (Backup-Branch-Check, Idempotenz, Ledger, dry-run)
und ``scripts/rebuild_index.py`` (``run()``-Signatur, Report-Stil).

Was das Skript tut (Stufe 0, deterministisch, $0)
=================================================
Walkt ``SOURCE_DIRS`` (``scripts/ingest``), extrahiert pro File Titel/
kanonische ID/Wortzahl (Extractor-Vertrag (a)–(f), siehe
``scripts/ingest/stage0.py``), filtert geledgerte IDs, dedupliziert
dreistufig (byte / kanonische ID / SequenceMatcher ≥ 0,9) und schreibt:

- ``out/ingest/inventory_plan.json``  — Inventory-Plan (Build-Artefakt,
  gitignored, ENT-054-Pattern)
- ``out/ingest/inventory_report.md``  — menschenlesbarer Report
  (Zaehlung nutzbar / dupe / empty / not_a_clipping / ledgered)

Was das Skript NICHT tut
========================
- **Kein LLM-Call** (Stufe 1–5 sind S033/BL-17 — enthaelt Stufe 0 auch nur
  einen LLM-Call, ist der Scope verfehlt; Brief 032 §Scope-Schutz).
- **Kein Write in ``wiki/``**, kein Draft-Pfad (``graph_writer``/ENT-059
  werden erst mit BL-17 produktiv).
- **Kein Byte in ``raw/`` veraendert** — Mounts werden nur gelesen.

Betriebs-Modi
=============
- ``--dry-run`` ist **Default** und endet nach Stufe 0: Plan + Report,
  keine Ledger-Schreibe.
- ``--live`` verlangt den Backup-Branch ``backup/pre-clippings-batch``
  (Check bricht sonst ab; den Branch selbst legt erst S033 vor dem echten
  Batch an) und schreibt ``skipped``-Ledger-Eintraege fuer definitive
  Skips (``empty_clip``/``dupe``). Nicht geledgert werden:
  (a) ``usable``-Files — deren ``merged``-Eintrag schreibt erst Stufe 5
  atomar (QK-17a); (b) ``not_a_clipping``-Files — ohne kanonische ID kein
  Ledger-Key, sie bleiben bewusst in jedem Report sichtbar; (c) Dupes,
  deren ID ein ``usable``-File teilt (DupeClip-Paar: gleiche ``yt:``-ID wie
  der Keeper — ein Skip-Eintrag wuerde den Keeper mitfiltern).
- ``--reconstruct-ledger``: Selbstheilung aus ``wiki/topics/`` (02 §B2);
  schreibt nur zusammen mit ``--live``, sonst Plan-Ausgabe.

Aufruf
======
::

    python scripts/ingest_clippings.py                        # dry-run
    python scripts/ingest_clippings.py --live                 # Ledger-Write
    python scripts/ingest_clippings.py --reconstruct-ledger   # Selbstheilung
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
        "# Inventory-Report — Clippings-Ingestion Stufe 0",
        f"> Erzeugt: {ts} | Modus: {mode} | Quelle: {', '.join(SOURCE_DIRS)}",
        "",
        f"**Files gesamt: {counts['files']}** (md {md} / html {html})",
        "",
        "| Status | Anzahl |",
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
        f"- `{r.path}` → Keeper `{r.dupe_of}` (Stufe: {r.dedup_tier})"
        for r in records if r.status == "dupe"])
    _section("Leer-Clips (empty_clip)", [
        f"- `{r.path}` — {r.reason}"
        for r in records if r.status == "empty_clip"])
    _section("Kein Clipping (not_a_clipping, QM R12)", [
        f"- `{r.path}` — {r.reason}"
        for r in records if r.status == "not_a_clipping"])
    _section("Bereits verarbeitet (ledgered)", [
        f"- `{r.path}` — {r.reason}"
        for r in records if r.status == "ledgered"])
    _section("No-Frontmatter-Fallback (sha1:-ID)", [
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
    """Stufe 0 ausfuehren. Return-Keys: ``records``, ``counts``, ``plan``,
    ``report`` (str), ``plan_path``/``report_path``, ``ledger_written``
    (Liste neuer Ledger-IDs), ``nothing_to_do``.
    """
    ledger_path = ledger_path or LEDGER_PATH
    out_dir = out_dir or OUT_DIR
    mode = "dry-run" if dry_run else "live"

    if not dry_run and require_backup_branch and \
            not _branch_exists(repo_root, BACKUP_BRANCH):
        raise RuntimeError(
            f"Backup-Branch '{BACKUP_BRANCH}' fehlt. Vor Live-Lauf erzeugen: "
            f"git branch {BACKUP_BRANCH}"
        )

    ledger = load_ledger(ledger_path)
    records = [extract_clip(p, repo_root)
               for p in walk_sources(repo_root, source_dirs)]

    # Idempotenz (02 §B2): geledgerte IDs zuerst filtern — vor Dedup,
    # damit ein bereits verarbeiteter Keeper nicht erneut antritt.
    for rec in records:
        if rec.canonical_id and rec.canonical_id in ledger:
            rec.status = "ledgered"
            rec.reason = (
                f"im Ledger: {ledger[rec.canonical_id].get('status')} "
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

    # Live: skipped-Eintraege fuer definitive Skips (Modul-Docstring).
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
    # Windows-Konsole ist cp1252 — Report enthaelt UTF-8 (→, Umlaute).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(
        description="Clippings-Batch Stufe 0: Inventory/Dedup/Ledger ($0).")
    p.add_argument("--dry-run", action="store_true", default=True,
                   help="Default: Plan + Report, keine Ledger-Schreibe.")
    p.add_argument("--live", action="store_true",
                   help="Ledger-Write; verlangt Backup-Branch "
                        f"'{BACKUP_BRANCH}'.")
    p.add_argument("--skip-backup-check", action="store_true",
                   help="Backup-Branch-Check ueberspringen (nur Tests/Local).")
    p.add_argument("--reconstruct-ledger", action="store_true",
                   help="Selbstheilung: Ledger aus wiki/topics/ rekonstruieren "
                        "(schreibt nur mit --live).")
    args = p.parse_args()
    dry_run = not args.live

    if args.reconstruct_ledger:
        entries = reconstruct_ledger(VAULT_ROOT)
        print(f"[reconstruct-ledger] {len(entries)} IDs aus wiki/topics/")
        for sid, entry in sorted(entries.items()):
            print(f"  {sid} → {entry['topic_pages']}")
        if dry_run:
            print("  (dry-run — nichts geschrieben; --live zum Schreiben)")
        else:
            save_ledger(entries)
            print(f"  geschrieben: {LEDGER_PATH}")
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
        print(f"Ledger: {len(result['ledger_written'])} neue skipped-Eintraege")
    if result["nothing_to_do"]:
        print("nothing to do — alle Clips geledgert oder kein Input.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
