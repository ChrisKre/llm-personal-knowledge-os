"""Smoke-Test: Multi-Modal-Extraktoren-Verzeichnis existiert (BL-08 Pre-Req)."""

from pathlib import Path


def test_extractors_dir_exists():
    repo_root = Path(__file__).resolve().parents[2]
    assert (repo_root / "agents" / "extractors").is_dir()
