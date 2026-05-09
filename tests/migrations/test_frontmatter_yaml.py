"""BL-03: Tests fuer Frontmatter-YAML-Migration.

Drei Pflicht-Pruefungen aus QM-Auflage QK-8 (Workshop S025):

- **Format-Korrektheit:** das migrierte Frontmatter ist mit ``yaml.safe_load``
  ohne Workaround parsbar.
- **anki_id-Erhaltung:** kein einziger Wert aendert sich vor/nach Migration
  (ENT-052; SRS-State-Erhaltung).
- **Idempotenz:** zweiter Lauf gegen migrierten Stand schreibt nichts.

Fixtures: ``tests/migrations/fixtures/before/`` (Snapshot der 7 Vocab-Files vor
Migration) und ``fixtures/after/`` (Soll-Zustand nach Migration).
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
BEFORE_DIR = Path(__file__).parent / "fixtures" / "before"
AFTER_DIR = Path(__file__).parent / "fixtures" / "after"
SNAPSHOT_FILE = Path(__file__).parent / "anki_id_snapshot.json"
MIGRATION_FILE = REPO_ROOT / "scripts" / "migrations" / "2026-05-09_frontmatter_yaml.py"


def _load_migration():
    """Load the date-prefixed migration script via importlib.

    Filename starts with a digit, so a normal ``import`` would fail.
    """
    spec = importlib.util.spec_from_file_location("migration_2026_05_09", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def staged_repo(tmp_path: Path) -> Path:
    """Materialize a wiki/language/vocab tree from BEFORE fixtures into tmp_path."""
    vocab = tmp_path / "wiki" / "language" / "vocab"
    vocab.mkdir(parents=True)
    for src in sorted(BEFORE_DIR.glob("v_*.md")):
        shutil.copy(src, vocab / src.name)
    return tmp_path


def test_format_correctness_yaml_safe_load_after_migration(staged_repo: Path):
    mod = _load_migration()
    mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)

    for f in sorted((staged_repo / "wiki/language/vocab").glob("v_*.md")):
        text = f.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"{f.name}: missing frontmatter delimiter"
        fm_end = text.find("\n---\n", 4)
        assert fm_end != -1, f"{f.name}: missing closing frontmatter delimiter"
        fm_block = text[4:fm_end]
        data = yaml.safe_load(fm_block)
        assert isinstance(data, dict), f"{f.name}: frontmatter must be a mapping"
        assert data["type"] == "VocabEntry"


def test_anki_id_preservation(staged_repo: Path):
    mod = _load_migration()
    snap = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))

    result = mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)

    assert result["anki_ids"] == snap["pre"], (
        "anki_ids veraendert! pre vs result siehe Diff."
    )
    assert snap["pre"] == snap["post"], (
        "anki_id-Snapshot inkonsistent (pre != post). Migration nicht akzeptierbar."
    )


def test_idempotent_second_run_changes_nothing(staged_repo: Path):
    mod = _load_migration()
    first = mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)
    assert first["changed"], "First run should have changed files (BEFORE state is broken)"

    second = mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)
    assert second["changed"] == [], (
        f"Migration nicht idempotent. Zweiter Lauf veraendert: {second['changed']}"
    )


def test_backup_branch_check_aborts_when_missing(staged_repo: Path):
    """Backup-Branch-Check als Pflicht-Pre-Step (QK-8.1).

    ``staged_repo`` ist kein Git-Repo, also schlaegt der Branch-Check fehl,
    wenn ``require_backup_branch=True``.
    """
    mod = _load_migration()
    with pytest.raises(RuntimeError, match="Backup-Branch"):
        mod.run(staged_repo, require_backup_branch=True, dry_run=False, update_log=False)


def test_after_fixtures_match_post_migration_output(staged_repo: Path):
    """fixtures/after/ ist der eingefrorene Soll-Zustand fuer die 7 Vocab-Files."""
    mod = _load_migration()
    mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)

    migrated_dir = staged_repo / "wiki" / "language" / "vocab"
    for expected in sorted(AFTER_DIR.glob("v_*.md")):
        actual = migrated_dir / expected.name
        assert actual.read_text(encoding="utf-8") == expected.read_text(encoding="utf-8"), (
            f"{expected.name}: Migrations-Output weicht vom eingefrorenen Soll-Zustand ab."
        )


def test_body_content_preserved(staged_repo: Path):
    """Migration darf NUR Frontmatter aendern; Body-Inhalt bleibt erhalten.

    Vergleicht Body-Strings via ``agents.frontmatter.parse`` (handhabt sowohl
    den indentierten Legacy-Delimiter als auch den sauberen Post-Migrations-
    Delimiter). Fuehrendes Whitespace wird gestripped, weil ``render`` einen
    festen ``\\n\\n``-Abstand zwischen FM und Body normalisiert (Brief S026:
    Body-*Inhalt* bleibt; Spacing ist unkritisch).
    """
    from agents.frontmatter import parse as fm_parse
    mod = _load_migration()

    before_bodies = {
        f.name: fm_parse(f.read_text(encoding="utf-8"))[1].strip()
        for f in sorted(BEFORE_DIR.glob("v_*.md"))
    }
    mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)

    migrated_dir = staged_repo / "wiki" / "language" / "vocab"
    for name, before_body in before_bodies.items():
        after_text = (migrated_dir / name).read_text(encoding="utf-8")
        after_body = fm_parse(after_text)[1].strip()
        assert after_body == before_body, (
            f"{name}: Body-Inhalt wurde von der Migration veraendert (verboten)."
        )
