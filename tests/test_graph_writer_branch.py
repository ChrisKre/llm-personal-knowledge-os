"""BL-01: Smoke-Test für graph_writer-Branch-Fix (main → master).

Hintergrund: ENT-039 (Branch-Konvention master). Vor BL-01 war reject_draft()
durch hartkodiertes ``git checkout main`` ein latenter Defekt — wird akut, sobald
Lint-Live (BL-07) reject_draft() trifft.

Test-Strategie: Wegwerf-Repo mit master+draft, reject_draft() läuft durch ohne
"branch 'main' not found"-Fehler. Wird gegen die Live-Funktion ausgeführt.
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
    """Defensiver Wächter: kein ``checkout main`` im Quelltext zurücklassen."""
    src = Path(__file__).resolve().parents[1] / "agents" / "graph_writer.py"
    text = src.read_text(encoding="utf-8")
    assert "git\", \"checkout\", \"main\"" not in text
    assert "Reset draft branch to current main state" not in text
    assert "Merge draft → main" not in text
