"""BL-01: smoke test for the graph_writer branch fix (main → master).

Background: ENT-039 (branch convention: master). Before BL-01, reject_draft()
had a latent defect from a hardcoded ``git checkout main``; it becomes acute as
soon as live lint (BL-07) calls reject_draft().

Test strategy: a throwaway repo with master + draft; reject_draft() runs
without a "branch 'main' not found" error. Runs against the live function.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from agents.graph_writer import reject_draft


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


def test_reject_draft_uses_master_branch(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()

    _run(["git", "init", "-q", "-b", "master"], repo)
    _run(["git", "-c", "user.email=t@t.t", "-c", "user.name=t",
          "commit", "--allow-empty", "-m", "init"], repo)
    _run(["git", "checkout", "-q", "-b", "draft"], repo)

    assert reject_draft(repo) is True

    head = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo, capture_output=True, text=True, check=True,
    )
    assert head.stdout.strip() == "draft"


def test_reject_draft_source_has_no_legacy_main_ref():
    """Defensive guard: no ``checkout main`` may remain in the source."""
    src = Path(__file__).resolve().parents[1] / "agents" / "graph_writer.py"
    text = src.read_text(encoding="utf-8")
    assert "git\", \"checkout\", \"main\"" not in text
    assert "Reset draft branch to current main state" not in text
    assert "Merge draft → main" not in text
