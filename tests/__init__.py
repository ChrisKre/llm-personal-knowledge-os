"""Test suite for LLM-Personal-Knowledge-OS.

Konvention (etabliert in Workshop S025 / BL-02):
- ``tests/migrations/`` — Migrations-Tests (Idempotenz, Backups, anki_id-Erhaltung).
  Fixture-Layout: ``tests/migrations/fixtures/before/`` (Snapshot vor Migration),
  ``tests/migrations/fixtures/after/`` (erwartetes Ergebnis).
- ``tests/lint/`` — Lint-Auto-Fix-Tests (Backlink-Symmetrie, Index-Sync, Slug-Dedup).
  Fixture-Layout pro Detektor: ``before/`` + ``after/`` Wiki-Mock-Trees.
- ``tests/render/`` — Anki-Render-Snapshot-Tests pro Profil A/B/C/D.
- ``tests/multimodal/`` — E2E-Tests für Bot-Handler (Bilder, PDFs, SHA-Dedup).

Snapshot-Ablage: ``__snapshots__/`` (pytest-snapshot-Default) im jeweiligen Test-Ordner.

Naming: ``test_<modul>_<aspekt>.py`` (z.B. ``test_frontmatter_yaml.py``).

Aufruf: ``pytest tests/`` läuft alle Tests; ``pytest tests/migrations/`` einzeln.
"""
