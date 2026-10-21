"""Migrations package — versioned wiki/schema migrations.

Convention (established in BL-03 / BL-12, workshop S025):

- **File naming:** ``YYYY-MM-DD_<short_name>.py``. The date is the day the
  migration was written (not run). Migrations are applied in lexicographic order.
- **Script interface:** every module exports
  - ``MIGRATION_NAME``  — the file name without suffix
  - ``run(wiki_root: Path, *, require_backup_branch: bool = True, dry_run: bool = False) -> dict``
    Return: ``{"changed": [paths], "skipped": [paths]}``
- **Mandatory requirements for destructive migrations** (QM requirement QK-8
  from the S025 workshop):
  1. **Backup branch:** the script checks that ``backup/pre-<short_name>``
     exists and aborts if it is missing (can only be skipped in tests via
     ``require_backup_branch=False``).
  2. **Idempotency:** a second run against the migrated state must not write
     anything (``changed == []``).
  3. **anki_id preservation:** migrations that touch VocabEntry frontmatter
     must write ``anki_id`` back byte-identically (ENT-052).
- **Run log:** ``scripts/migrations/applied.json`` is a flat mapping
  ``{"<MIGRATION_NAME>": "<iso-timestamp>"}``. Each migration appends its
  entry *after* a successful run. Existing entries are overwritten with a new
  timestamp (re-runs are allowed because migrations are idempotent).
- **How the operator runs one:**
  ``python -m scripts.migrations.<MIGRATION_NAME>`` (module run; there is no
  separate runner CLI until BL-12 phase 2 changes that).

Tests live in ``tests/migrations/``. Fixtures: ``before/`` (pre-migration
snapshot) + ``after/`` (post snapshot) + ``anki_id_snapshot.json``.
"""
