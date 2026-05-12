"""S029: Tests fuer CulturalEntry-Frontmatter-Migration.

Direkte Schwester von ``test_frontmatter_yaml.py`` (BL-03), **ohne** den
``anki_id``-Erhaltungstest — CulturalEntries haben keine Anki-Karten.

Pflicht-Pruefungen aus Brief 029:

- **Format-Korrektheit:** das migrierte Frontmatter ist mit ``yaml.safe_load``
  ohne Workaround parsbar und der Top-Level-Type bleibt ``CulturalEntry``.
- **Idempotenz:** zweiter Lauf gegen migrierten Stand schreibt nichts. Diese
  Garantie ist nicht-trivial: ``_normalize_legacy_fm`` wuerde die 2-Space-
  Continuation-Indents im sauberen Output als haeufigsten Prefix erkennen
  und strippen — der Migration-Code-Pfad muss das umgehen.
- **Soll-Zustand:** der Migrations-Output stimmt byte-fuer-byte mit der
  eingefrorenen AFTER-Fixture ueberein.
- **Body-Erhaltung:** Body-Inhalt bleibt nach FM-Trennung gleich (Brief
  S026/S027-Regel; die 14-Space-Body-Indent ist Renderer-Frage und gehoert
  zu BL-05).
- **Backup-Branch-Check:** Pre-Step bricht ab, wenn der Branch fehlt.

Fixtures: ``tests/migrations/fixtures/cultural_before/`` (kaputter Stand)
und ``cultural_after/`` (Soll-Zustand).
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
BEFORE_DIR = Path(__file__).parent / "fixtures" / "cultural_before"
AFTER_DIR = Path(__file__).parent / "fixtures" / "cultural_after"
MIGRATION_FILE = REPO_ROOT / "scripts" / "migrations" / "2026-05-09_cultural_frontmatter.py"


def _load_migration():
    """Load the date-prefixed migration script via importlib."""
    spec = importlib.util.spec_from_file_location("migration_cultural", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def staged_repo(tmp_path: Path) -> Path:
    """Materialize a wiki/language/culture tree from BEFORE fixtures into tmp_path."""
    culture = tmp_path / "wiki" / "language" / "culture"
    culture.mkdir(parents=True)
    for src in sorted(BEFORE_DIR.glob("c_*.md")):
        shutil.copy(src, culture / src.name)
    return tmp_path


def test_format_correctness_yaml_safe_load_after_migration(staged_repo: Path):
    mod = _load_migration()
    mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)

    for f in sorted((staged_repo / "wiki/language/culture").glob("c_*.md")):
        text = f.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"{f.name}: missing frontmatter delimiter"
        fm_end = text.find("\n---\n", 4)
        assert fm_end != -1, f"{f.name}: missing closing frontmatter delimiter"
        fm_block = text[4:fm_end]
        data = yaml.safe_load(fm_block)
        assert isinstance(data, dict), f"{f.name}: frontmatter must be a mapping"
        assert data["type"] == "CulturalEntry"


def test_idempotent_second_run_changes_nothing(staged_repo: Path):
    mod = _load_migration()
    first = mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)
    assert first["changed"], "First run should have changed files (BEFORE state is broken)"

    second = mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)
    assert second["changed"] == [], (
        f"Migration nicht idempotent. Zweiter Lauf veraendert: {second['changed']}"
    )


def test_backup_branch_check_aborts_when_missing(staged_repo: Path):
    """Backup-Branch-Check als Pflicht-Pre-Step (Brief 029 DoD)."""
    mod = _load_migration()
    with pytest.raises(RuntimeError, match="Backup-Branch"):
        mod.run(staged_repo, require_backup_branch=True, dry_run=False, update_log=False)


def test_after_fixtures_match_post_migration_output(staged_repo: Path):
    """fixtures/cultural_after/ ist der eingefrorene Soll-Zustand."""
    mod = _load_migration()
    mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)

    migrated_dir = staged_repo / "wiki" / "language" / "culture"
    for expected in sorted(AFTER_DIR.glob("c_*.md")):
        actual = migrated_dir / expected.name
        assert actual.read_text(encoding="utf-8") == expected.read_text(encoding="utf-8"), (
            f"{expected.name}: Migrations-Output weicht vom eingefrorenen Soll-Zustand ab."
        )


def test_body_content_preserved(staged_repo: Path):
    """Migration darf NUR Frontmatter aendern; Body-Inhalt bleibt erhalten.

    Vergleicht Body-Strings via ``_split`` (rohe FM/Body-Trennung) statt
    ``parse``, weil die BEFORE-Fixture FM-seitig kaputt ist — der Migrations-
    Defekt ist gerade, dass selbst ``_normalize_legacy_fm`` daran scheitert.
    Fuehrendes Whitespace wird gestripped, weil ``render`` einen festen
    ``\\n\\n``-Abstand zwischen FM und Body normalisiert (Brief S026:
    Body-*Inhalt* bleibt; Spacing ist unkritisch). Die 14-Space-Body-
    Einrueckung in c_es_flamenco bleibt damit erhalten — sie ist Renderer-
    Frage und gehoert zu BL-05.
    """
    from agents.frontmatter import _split
    mod = _load_migration()

    before_bodies = {
        f.name: _split(f.read_text(encoding="utf-8"))[1].strip()
        for f in sorted(BEFORE_DIR.glob("c_*.md"))
    }
    mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)

    migrated_dir = staged_repo / "wiki" / "language" / "culture"
    for name, before_body in before_bodies.items():
        after_text = (migrated_dir / name).read_text(encoding="utf-8")
        after_body = _split(after_text)[1].strip()
        assert after_body == before_body, (
            f"{name}: Body-Inhalt wurde von der Migration veraendert (verboten)."
        )
