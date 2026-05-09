"""Migrations package — versionierte Wiki/Schema-Migrationen.

Konvention (etabliert in BL-03 / BL-12, Workshop S025):

- **Datei-Naming:** ``YYYY-MM-DD_<short_name>.py``. Datum = Tag des Schreibens
  (nicht des Laufs). Reihenfolge der Anwendung lexikographisch.
- **Skript-Schnittstelle:** jedes Modul exportiert
  - ``MIGRATION_NAME``  — entspricht dem Filename ohne Suffix
  - ``run(wiki_root: Path, *, require_backup_branch: bool = True, dry_run: bool = False) -> dict``
    Return: ``{"changed": [paths], "skipped": [paths]}``
- **Pflicht-Auflagen fuer destruktive Migrationen** (QM-Auflage QK-8 aus
  S025-Workshop):
  1. **Backup-Branch:** das Skript prueft die Existenz von
     ``backup/pre-<short_name>`` und bricht ab, wenn der Branch fehlt
     (ueberspringbar nur fuer Tests via ``require_backup_branch=False``).
  2. **Idempotenz:** zweiter Lauf gegen migrierten Stand darf keine Schreibvorgaenge
     produzieren (``changed == []``).
  3. **anki_id-Erhaltung:** Migrationen, die VocabEntry-Frontmatter anfassen,
     muessen ``anki_id`` byte-identisch zurueckschreiben (ENT-052).
- **Lauf-Log:** ``scripts/migrations/applied.json`` ist ein flaches Mapping
  ``{"<MIGRATION_NAME>": "<iso-timestamp>"}``. Jede Migration appended ihren
  Eintrag *nach* erfolgreichem Lauf. Schon vorhandene Eintraege werden mit
  neuem Timestamp ueberschrieben (Re-Lauf-Erlaubnis bei Idempotenz).
- **Aufruf-Pfad fuer den Operator:**
  ``python -m scripts.migrations.<MIGRATION_NAME>`` (Module-Run, keine separate
  Runner-CLI bis BL-12-Phase-2 das aendert).

Tests liegen in ``tests/migrations/``. Fixtures: ``before/`` (Pre-Migrations-
Snapshot) + ``after/`` (Post-Snapshot) + ``anki_id_snapshot.json``.
"""
