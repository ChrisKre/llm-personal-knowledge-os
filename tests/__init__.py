"""Test suite for LLM-Personal-Knowledge-OS.

Convention (established in workshop S025 / BL-02):
- ``tests/migrations/`` — migration tests (idempotency, backups, anki_id preservation).
  Fixture layout: ``tests/migrations/fixtures/before/`` (snapshot before the migration),
  ``tests/migrations/fixtures/after/`` (expected result).
- ``tests/lint/`` — lint and index tests (backlink symmetry, index sync, slug dedup).
  Fixture layout per detector: ``before/`` + ``after/`` wiki mock trees.
- ``tests/render/`` — Anki render snapshot tests per profile A/B/C/D.
- ``tests/multimodal/`` — E2E tests for bot handlers (images, PDFs, SHA dedup).

Snapshots live in ``__snapshots__/`` (pytest-snapshot default) in each test folder.

Naming: ``test_<module>_<aspect>.py`` (e.g. ``test_frontmatter_yaml.py``).

Usage: ``pytest tests/`` runs all tests; ``pytest tests/migrations/`` a single folder.
"""
