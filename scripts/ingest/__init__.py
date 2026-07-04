"""Ingest package — Kanal-Konfiguration + Ledger fuer die Clippings-Ingestion.

Quelle: BL-16 (workshop_02/backlog.md), ENT-058 (Kanal K2 Source-Mount),
Brief 032 (sessions/032_2026-07-04.md). Konventionen analog
``scripts/migrations/__init__.py`` (Backup-Branch, Idempotenz, Ledger).

Warum ein Package (Brief-032 F1): Das Batch-Skript ``scripts/ingest_clippings.py``
ist nach dem Einmal-Lauf Geschichte (02 §B3) — die Kanal-Konfiguration
(``SOURCE_DIRS``) und das Ledger leben laenger und werden von BL-19
(laufender Scheduled-Scan) wiederverwendet. Kein ``agents/``-Modul:
Stufe 0 ist Batch-Tooling, kein Agent.

Bestandteile
============
- ``SOURCE_DIRS``   — registrierte Source-Mounts der Ingestion (ENT-058,
  SCHEMA §2). Analog ``HUMAN_OWNED_ZONES`` in ``agents/graph_writer``:
  importierbare Single-Source-Konstante, repo-relative POSIX-Pfade.
- ``stage0``        — deterministischer Inventory-/Dedup-Pass ($0, kein LLM).
- ``ledger``        — Ingest-Ledger (versioniert, analog ``applied.json``)
  + Selbstheilungs-Rekonstruktion aus ``wiki/topics/``.

Vertrags-Konstanten (ENT-058 woertlich — Aenderung ist PO-Eskalation,
keine Stil-Freiheit; Brief 032 §Scope-Schutz):
- ``EMPTY_CLIP_MIN_WORDS = 150``  — Leer-Clip-Filter (d).
- ``NEAR_DUPE_RATIO = 0.9``       — SequenceMatcher-Schwelle Dedup Stufe 3.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Registrierte Source-Mounts der Ingestion (ENT-058 / SCHEMA §2, Kanal K2).
# Konfigurations-Liste statt hart verdrahtetem Verzeichnis — die Pipeline ist
# die anpassungsfaehige Seite. BL-19 (Scheduled-Scan) liest dieselbe Liste.
SOURCE_DIRS: tuple[str, ...] = (
    "raw/sources/",
    "raw/Wiki/Clippings/",
)

# Ingest-Ledger: verarbeitete kanonische Quell-IDs (02 §B2 Idempotenz-
# Definition). Versioniert — Betriebs-Zustand, verlustkritisch (Brief-032 F2).
LEDGER_PATH = REPO_ROOT / "scripts" / "ingest" / "clippings_ledger.json"

# Backup-Branch-Pflicht fuer Live-Laeufe (Muster scripts/migrations/).
# Der Branch selbst wird erst in S033 vor dem echten Batch angelegt —
# hier nur der Check (Brief 032 Schritt 3.3).
BACKUP_BRANCH = "backup/pre-clippings-batch"

# ENT-058-Vertragswerte — NICHT anpassen ohne ENT (Scope-Schutz Brief 032).
EMPTY_CLIP_MIN_WORDS = 150
NEAR_DUPE_RATIO = 0.9
