"""agents.config: VAULT_ROOT resolution and its use as the default data root."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agents import config

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def reload_config(monkeypatch: pytest.MonkeyPatch):
    """Reload agents.config under a patched env, then restore the original."""
    yield lambda: importlib.reload(config)
    monkeypatch.undo()
    importlib.reload(config)


def test_vault_root_honours_env(monkeypatch, reload_config, tmp_path: Path) -> None:
    monkeypatch.setenv("KOS_VAULT_ROOT", str(tmp_path))
    assert reload_config().VAULT_ROOT == tmp_path.resolve()


def test_vault_root_defaults_to_sample_vault(monkeypatch, reload_config) -> None:
    monkeypatch.delenv("KOS_VAULT_ROOT", raising=False)
    cfg = reload_config()
    assert cfg.VAULT_ROOT == REPO_ROOT / "sample_vault"
    assert cfg.REPO_ROOT == REPO_ROOT


def test_empty_env_falls_back_to_sample_vault(monkeypatch, reload_config) -> None:
    """An empty ``KOS_VAULT_ROOT=`` line in .env must not resolve to the cwd."""
    monkeypatch.setenv("KOS_VAULT_ROOT", "")
    assert reload_config().VAULT_ROOT == REPO_ROOT / "sample_vault"


def test_sample_vault_exists() -> None:
    assert (REPO_ROOT / "sample_vault" / "wiki").is_dir()
    assert (REPO_ROOT / "sample_vault" / "index.md").is_file()


def test_data_paths_follow_vault_root(tmp_path: Path) -> None:
    """Module-level data paths in agents and scripts derive from VAULT_ROOT.

    Runs in a fresh interpreter so import-time constants see the patched env.
    """
    code = (
        "import importlib.util, sys\n"
        "sys.path.insert(0, '.')\n"
        "from agents import graph_reader, graph_writer\n"
        "from scripts.ingest import LEDGER_PATH\n"
        "s = importlib.util.spec_from_file_location('ri', 'scripts/rebuild_index.py')\n"
        "ri = importlib.util.module_from_spec(s); s.loader.exec_module(ri)\n"
        "print(graph_reader.INDEX_PATH)\n"
        "print(graph_reader.SQLITE_PATH)\n"
        "print(ri.INDEX_PATH)\n"
        "print(ri.WIKI_DIR)\n"
        "print(LEDGER_PATH)\n"
        "print(graph_writer.execute_writes.__defaults__[0])\n"
    )
    env = {**os.environ, "KOS_VAULT_ROOT": str(tmp_path)}
    out = subprocess.run([sys.executable, "-c", code], cwd=REPO_ROOT, env=env,
                         capture_output=True, text=True, check=True).stdout
    vault = tmp_path.resolve()
    assert [Path(line) for line in out.splitlines()] == [
        vault / "index.md",
        vault / "wiki_index.db",
        vault / "index.md",
        vault / "wiki",
        vault / "clippings_ledger.json",
        vault,
    ]
