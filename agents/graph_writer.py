"""graph_writer.py — WikiWrite execution and Draft→Main branch workflow."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TypedDict


class WikiWrite(TypedDict):
    path: str        # relative path from repo root, e.g. "wiki/language/vocab/v_es_madrugada.md"
    content: str     # full markdown content
    operation: str   # "create" | "update" | "append"


WIKI_ROOT = Path(__file__).parent.parent


def execute_writes(writes: list[WikiWrite], wiki_root: Path = WIKI_ROOT) -> list[str]:
    """Execute a list of WikiWrite operations on the current branch (draft).

    Returns list of written file paths.
    """
    written: list[str] = []
    for write in writes:
        path = wiki_root / write["path"]
        path.parent.mkdir(parents=True, exist_ok=True)

        match write["operation"]:
            case "create":
                path.write_text(write["content"], encoding="utf-8")
            case "update":
                path.write_text(write["content"], encoding="utf-8")
            case "append":
                existing = path.read_text(encoding="utf-8") if path.exists() else ""
                path.write_text(existing + "\n" + write["content"], encoding="utf-8")
            case _:
                raise ValueError(f"Unknown operation: {write['operation']}")

        written.append(write["path"])

    return written


def approve_draft(wiki_root: Path = WIKI_ROOT) -> bool:
    """Merge draft → main. Called via Telegram callback after user approval."""
    result = subprocess.run(
        ["git", "merge", "draft", "--no-ff", "-m", "approved by user"],
        cwd=wiki_root, capture_output=True, text=True,
    )
    return result.returncode == 0


def reject_draft(wiki_root: Path = WIKI_ROOT) -> bool:
    """Reset draft branch to current main state."""
    cmds = [
        ["git", "checkout", "main"],
        ["git", "branch", "-D", "draft"],
        ["git", "checkout", "-b", "draft"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, cwd=wiki_root, capture_output=True)
        if result.returncode != 0:
            return False
    return True


def ensure_draft_branch(wiki_root: Path = WIKI_ROOT) -> None:
    """Create draft branch if it doesn't exist."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "draft"],
        cwd=wiki_root, capture_output=True,
    )
    if result.returncode != 0:
        subprocess.run(["git", "checkout", "-b", "draft"], cwd=wiki_root, check=True)


def requires_user_approval(writes: list[WikiWrite], agent_outputs: dict) -> bool:
    """Determine if any pending write requires manual user approval.

    Rules from ARCHITECTURE.md §7:
      - PersonalFact with story_score > 7 → Yes
      - Contradiction resolution → Yes
      - Deletion/archival → always Yes
      - Everything else → No
    """
    for write in writes:
        path = write["path"]
        # Deletion or archival
        if "archived" in write.get("content", ""):
            return True
        # High-score PersonalFact (story_score > 7 in frontmatter)
        if "wiki/personal/facts/" in path:
            score = agent_outputs.get("story_score")
            if score is not None and score > 7:
                return True
    # Contradiction flagged by supervisor
    if agent_outputs.get("contradiction_detected"):
        return True
    return False
