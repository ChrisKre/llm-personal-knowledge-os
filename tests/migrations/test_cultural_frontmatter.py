"""S029: tests for the CulturalEntry frontmatter migration.

Direct sibling of ``test_frontmatter_yaml.py`` (BL-03), **without** the
``anki_id`` preservation test — CulturalEntries have no Anki cards.

Mandatory checks from brief 029:

- **Format correctness:** the migrated frontmatter parses with
  ``yaml.safe_load`` without workarounds and the top-level type stays
  ``CulturalEntry``.
- **Idempotency:** a second run against the migrated state writes nothing.
  This guarantee is non-trivial: ``_normalize_legacy_fm`` would see the
  2-space continuation indents in clean output as the most common prefix and
  strip them; the migration code path has to avoid that.
- **Target state:** the migration output matches the frozen AFTER fixture
  byte for byte.
- **Body preservation:** the body content stays the same after the FM split
  (rule from briefs S026/S027; the 14-space body indent is a renderer question
  and belongs to BL-05).
- **Backup branch check:** the pre-step aborts if the branch is missing.

Fixtures: ``tests/migrations/fixtures/cultural_before/`` (broken state)
and ``cultural_after/`` (target state).
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
        f"Migration not idempotent. Second run changed: {second['changed']}"
    )


def test_backup_branch_check_aborts_when_missing(staged_repo: Path):
    """Backup branch check as a mandatory pre-step (brief 029 DoD)."""
    mod = _load_migration()
    with pytest.raises(RuntimeError, match="Backup branch"):
        mod.run(staged_repo, require_backup_branch=True, dry_run=False, update_log=False)


def test_after_fixtures_match_post_migration_output(staged_repo: Path):
    """fixtures/cultural_after/ is the frozen target state."""
    mod = _load_migration()
    mod.run(staged_repo, require_backup_branch=False, dry_run=False, update_log=False)

    migrated_dir = staged_repo / "wiki" / "language" / "culture"
    for expected in sorted(AFTER_DIR.glob("c_*.md")):
        actual = migrated_dir / expected.name
        assert actual.read_text(encoding="utf-8") == expected.read_text(encoding="utf-8"), (
            f"{expected.name}: migration output differs from the frozen target state."
        )


def test_body_content_preserved(staged_repo: Path):
    """The migration may ONLY change frontmatter; body content is preserved.

    Compares body strings via ``_split`` (raw FM/body split) instead of
    ``parse``, because the BEFORE fixture has broken FM — the migration defect
    is exactly that even ``_normalize_legacy_fm`` fails on it. Leading
    whitespace is stripped because ``render`` normalizes a fixed ``\\n\\n``
    gap between FM and body (brief S026: the body *content* is kept; spacing
    doesn't matter). The 14-space body indent in c_es_flamenco is therefore
    preserved; it is a renderer question and belongs to BL-05.
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
            f"{name}: body content was changed by the migration (forbidden)."
        )
