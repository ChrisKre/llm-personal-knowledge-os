"""BL-15: guard tests for the axiom 2 carve-out (ENT-062, QM R10/QK-19).

Three contracts:
- ``execute_writes()`` raises ``HumanOwnedZoneError`` for writes into a
  declared human-owned zone, **before** any write of the batch is executed
  (no partial writes).
- ``assert_writable()`` is the shared zone check (one implementation,
  importable for future BL-07 auto-fixes) and tolerates backslashes and case
  differences (Windows file systems).
- ``find_zone_owner_violations()`` is the consistency detector
  "zone ⊄ owner flags" (pure function; lint integration follows with BL-07/BL-18).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agents.graph_writer import (
    HumanOwnedZoneError,
    assert_writable,
    execute_writes,
    find_zone_owner_violations,
)


def test_execute_writes_rejects_zone_write(tmp_path: Path) -> None:
    """WikiWrite into the zone → hard exception, no partial write."""
    writes = [
        {"path": "wiki/topics/tp_health_x.md", "content": "ok", "operation": "create"},
        {"path": "wiki/personal/health/02_protocol_main.md",
         "content": "böse", "operation": "update"},
    ]
    with pytest.raises(HumanOwnedZoneError):
        execute_writes(writes, wiki_root=tmp_path)
    # The valid first write must NOT have been executed (fail fast before the
    # first write — otherwise a zone violation would leave partial state).
    assert not (tmp_path / "wiki" / "topics" / "tp_health_x.md").exists()
    assert not (tmp_path / "wiki" / "personal" / "health").exists()


def test_execute_writes_outside_zone_passes(tmp_path: Path) -> None:
    writes = [{"path": "wiki/topics/tp_health_x.md", "content": "ok",
               "operation": "create"}]
    written = execute_writes(writes, wiki_root=tmp_path)
    assert written == ["wiki/topics/tp_health_x.md"]
    assert (tmp_path / "wiki" / "topics" / "tp_health_x.md").exists()


def test_assert_writable_windows_variants() -> None:
    """Backslash and case variants of the same path do not bypass the guard."""
    for evil in (
        "wiki/personal/health/x.md",
        "wiki\\personal\\health\\x.md",
        "WIKI/Personal/HEALTH/x.md",
        "./wiki/personal/health/sub/x.md",
    ):
        with pytest.raises(HumanOwnedZoneError):
            assert_writable(evil)
    # Neighbouring paths stay writable:
    assert_writable("wiki/personal/facts/pf_x.md")
    assert_writable("wiki/topics/tp_health_x.md")


def test_find_zone_owner_violations(tmp_path: Path) -> None:
    """Detector "zone ⊄ owner flags": reports missing/different flags."""
    zone = tmp_path / "wiki" / "personal" / "health"
    zone.mkdir(parents=True)
    (zone / "flagged.md").write_text(
        "---\ntype: HealthProtocol\ncreated: 2026-06-01\nowner: human\n---\n\n# ok\n",
        encoding="utf-8")
    (zone / "unflagged.md").write_text(
        "---\ntype: HealthProtocol\ncreated: 2026-06-01\n---\n\n# fehlt\n",
        encoding="utf-8")
    (zone / "no_frontmatter.md").write_text("# nur Body\n", encoding="utf-8")

    violations = find_zone_owner_violations(wiki_root=tmp_path)
    assert violations == [
        "wiki/personal/health/no_frontmatter.md",
        "wiki/personal/health/unflagged.md",
    ]


def test_default_vault_zone_has_no_violations() -> None:
    """Default vault (sample_vault, pinned by tests/conftest.py): the detector
    runs against config.VAULT_ROOT and the bundled vault has no violations."""
    assert find_zone_owner_violations() == []
