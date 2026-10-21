"""BL-04: tests for scripts/rebuild_index.py.

Three mandatory checks from brief S027:

- **Snapshot match:** a rebuild against ``fixtures/wiki_mock/`` produces exactly
  the stored ``__snapshots__/index.md.snap``.
- **Idempotency:** a second run against an unchanged tree writes nothing
  (``changed == False``); like QM requirement QK-8 for migrations
  (brief S027: "the idempotency test is QM standard and mandatory for BL-04 too").
- **Defensive skip:** ``broken_yaml.md`` (frontmatter with unresolved ``[[[``
  and a bare ``?``) ends up in ``result["skipped"]``; the run does not abort
  (brief S027 §F2).

Fixture layout:
- ``tests/lint/fixtures/wiki_mock/`` — a small wiki tree mock (5 valid
  files + 1 broken_yaml).
- ``tests/lint/__snapshots__/index.md.snap`` — the frozen expected output.

Loading: the script lives in ``scripts/rebuild_index.py`` and is imported as a
module via ``importlib.util``.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_FILE = REPO_ROOT / "scripts" / "rebuild_index.py"
FIXTURE_WIKI = Path(__file__).parent / "fixtures" / "wiki_mock"
SNAPSHOT_FILE = Path(__file__).parent / "__snapshots__" / "index.md.snap"


def _load_module():
    spec = importlib.util.spec_from_file_location("rebuild_index", SCRIPT_FILE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_snapshot_match(tmp_path: Path) -> None:
    """Rebuild produces byte-identical output to the frozen snapshot."""
    mod = _load_module()
    index_path = tmp_path / "index.md"
    result = mod.run(wiki_dir=FIXTURE_WIKI, index_path=index_path)

    expected = SNAPSHOT_FILE.read_text(encoding="utf-8")
    assert result["rendered"] == expected
    assert index_path.read_text(encoding="utf-8") == expected
    assert result["changed"] is True


def test_idempotent(tmp_path: Path) -> None:
    """Second run against unchanged tree reports changed=False."""
    mod = _load_module()
    index_path = tmp_path / "index.md"
    first = mod.run(wiki_dir=FIXTURE_WIKI, index_path=index_path)
    second = mod.run(wiki_dir=FIXTURE_WIKI, index_path=index_path)
    assert first["changed"] is True
    assert second["changed"] is False
    assert second["rendered"] == first["rendered"]


def test_skips_broken_yaml(tmp_path: Path) -> None:
    """File with unrecoverable YAML lands in skipped, run does not abort."""
    mod = _load_module()
    index_path = tmp_path / "index.md"
    result = mod.run(wiki_dir=FIXTURE_WIKI, index_path=index_path)

    skipped_names = {p.name for p, _ in result["skipped"]}
    assert "broken_yaml.md" in skipped_names
    skipped_reasons = {p.name: r for p, r in result["skipped"]}
    assert "YAMLError" in skipped_reasons["broken_yaml.md"]


def test_dry_run_no_write(tmp_path: Path) -> None:
    """--dry-run computes the rebuild but does not touch the file."""
    mod = _load_module()
    index_path = tmp_path / "index.md"
    result = mod.run(wiki_dir=FIXTURE_WIKI, index_path=index_path, dry_run=True)
    assert result["changed"] is True
    assert not index_path.exists()


def test_section_counts(tmp_path: Path) -> None:
    """Bucket counts reflect the fixture composition."""
    mod = _load_module()
    index_path = tmp_path / "index.md"
    result = mod.run(wiki_dir=FIXTURE_WIKI, index_path=index_path)
    counts = {section: len(items) for section, items in result["entries"].items()}
    assert counts["PersonalFacts"] == 2
    assert counts["VocabEntries — ES"] == 1
    assert counts["VocabEntries — EN"] == 1
    assert counts["CulturalEntries"] == 1
    assert counts["LanguageBridges"] == 1
    assert counts["Concepts"] == 0
