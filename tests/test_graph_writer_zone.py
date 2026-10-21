"""BL-15: Guard-Tests für den Axiom-2-Carve-out (ENT-062, QM R10/QK-19).

Drei Verträge:
- ``execute_writes()`` wirft ``HumanOwnedZoneError`` für Writes in eine
  deklarierte human-owned Zone — und zwar **bevor** irgendein Write des
  Batches ausgeführt wird (kein Partial-Write).
- ``assert_writable()`` ist die geteilte Zonen-Prüfung (eine Implementierung,
  importierbar für künftige BL-07-Auto-Fixes) und ist Backslash-/Case-tolerant
  (Windows-Dateisystem).
- ``find_zone_owner_violations()`` ist der Konsistenz-Detektor
  „Zone ⊄ owner-Flags" (Pure Function, Lint-Integration folgt mit BL-07/BL-18).
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
    """WikiWrite in die Zone → harte Exception, kein Partial-Write."""
    writes = [
        {"path": "wiki/topics/tp_health_x.md", "content": "ok", "operation": "create"},
        {"path": "wiki/personal/health/02_protocol_main.md",
         "content": "böse", "operation": "update"},
    ]
    with pytest.raises(HumanOwnedZoneError):
        execute_writes(writes, wiki_root=tmp_path)
    # Der valide erste Write darf NICHT ausgeführt worden sein (fail fast
    # vor dem ersten Write — sonst hinterließe ein Zonen-Verstoß Teilzustand).
    assert not (tmp_path / "wiki" / "topics" / "tp_health_x.md").exists()
    assert not (tmp_path / "wiki" / "personal" / "health").exists()


def test_execute_writes_outside_zone_passes(tmp_path: Path) -> None:
    writes = [{"path": "wiki/topics/tp_health_x.md", "content": "ok",
               "operation": "create"}]
    written = execute_writes(writes, wiki_root=tmp_path)
    assert written == ["wiki/topics/tp_health_x.md"]
    assert (tmp_path / "wiki" / "topics" / "tp_health_x.md").exists()


def test_assert_writable_windows_variants() -> None:
    """Backslash- und Case-Varianten desselben Pfads umgehen den Guard nicht."""
    for evil in (
        "wiki/personal/health/x.md",
        "wiki\\personal\\health\\x.md",
        "WIKI/Personal/HEALTH/x.md",
        "./wiki/personal/health/sub/x.md",
    ):
        with pytest.raises(HumanOwnedZoneError):
            assert_writable(evil)
    # Nachbarn bleiben schreibbar:
    assert_writable("wiki/personal/facts/pf_x.md")
    assert_writable("wiki/topics/tp_health_x.md")


def test_find_zone_owner_violations(tmp_path: Path) -> None:
    """Detektor „Zone ⊄ owner-Flags": meldet fehlende/abweichende Flags."""
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
