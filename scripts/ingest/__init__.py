"""Ingest package — channel configuration + ledger for clippings ingestion.

Source: BL-16 (workshop_02/backlog.md), ENT-058 (channel K2 source mount),
brief 032 (sessions/032_2026-07-04.md). Conventions follow
``scripts/migrations/__init__.py`` (backup branch, idempotency, ledger).

Why a package (brief 032 F1): the batch script ``scripts/ingest_clippings.py``
is history after its one-off run (02 §B3), but the channel configuration
(``SOURCE_DIRS``) and the ledger live on and are reused by BL-19 (the
continuous scheduled scan). Not an ``agents/`` module: stage 0 is batch
tooling, not an agent.

Contents
========
- ``SOURCE_DIRS``   — registered ingestion source mounts (ENT-058,
  SCHEMA §2). Like ``HUMAN_OWNED_ZONES`` in ``agents/graph_writer``: an
  importable single-source constant of vault-relative POSIX paths.
- ``stage0``        — deterministic inventory/dedup pass ($0, no LLM).
- ``ledger``        — ingest ledger (like ``applied.json``)
  + self-healing reconstruction from ``wiki/topics/``.

Contract constants (verbatim from ENT-058; changing them needs a PO decision,
not a style choice; brief 032, scope protection):
- ``EMPTY_CLIP_MIN_WORDS = 150``  — empty-clip filter (d).
- ``NEAR_DUPE_RATIO = 0.9``       — SequenceMatcher threshold for dedup stage 3.
"""

from __future__ import annotations

from agents.config import VAULT_ROOT

# Registered ingestion source mounts (ENT-058 / SCHEMA §2, channel K2).
# A configuration list instead of a hardwired directory: the pipeline is the
# side that adapts. BL-19 (scheduled scan) reads the same list.
SOURCE_DIRS: tuple[str, ...] = (
    "raw/sources/",
    "raw/Wiki/Clippings/",
)

# Ingest ledger: processed canonical source IDs (02 §B2 idempotency
# definition). Operational state that must not be lost (brief 032 F2); it
# lives in the vault because it lists vault sources.
LEDGER_PATH = VAULT_ROOT / "clippings_ledger.json"

# Live runs require a backup branch (pattern from scripts/migrations/).
# The branch itself is only created right before the real batch (S033);
# this is just the check (brief 032 step 3.3).
BACKUP_BRANCH = "backup/pre-clippings-batch"

# ENT-058 contract values — do NOT change without an ENT (brief 032 scope protection).
EMPTY_CLIP_MIN_WORDS = 150
NEAR_DUPE_RATIO = 0.9
