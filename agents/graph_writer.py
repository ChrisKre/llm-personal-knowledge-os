"""graph_writer.py — WikiWrite execution and Draft→Master branch workflow."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TypedDict

from agents.config import VAULT_ROOT


class WikiWrite(TypedDict):
    path: str        # relative path from the vault root, e.g. "wiki/language/vocab/v_es_madrugada.md"
    content: str     # full markdown content
    operation: str   # "create" | "update" | "append"


# Human-owned zones (SCHEMA §2, ENT-062): directories the AI never writes to.
# Single source: the guard (assert_writable) and the consistency detector
# (find_zone_owner_violations) both read this list.
HUMAN_OWNED_ZONES: tuple[str, ...] = ("wiki/personal/health/",)


class HumanOwnedZoneError(Exception):
    """Attempt to write into a declared human-owned zone (axiom 2 carve-out)."""


def assert_writable(path: str) -> None:
    """Shared zone check before every file write (ENT-062, QK-19).

    Called by execute_writes(). Every future write path (e.g. BL-07 lint
    auto-fixes) must import and call it before writing; there is no second
    zone-check code path.

    Raises HumanOwnedZoneError for paths inside a declared zone.
    Case-insensitive (Windows file systems), tolerant of backslashes.
    """
    norm = path.replace("\\", "/").lstrip("./").casefold()
    for zone in HUMAN_OWNED_ZONES:
        if norm.startswith(zone.casefold()):
            raise HumanOwnedZoneError(
                f"'{path}' is inside the human-owned zone '{zone}' — "
                f"AI writes are forbidden there (SCHEMA §1 axiom 2, ENT-062)."
            )


def find_zone_owner_violations(wiki_root: Path = VAULT_ROOT) -> list[str]:
    """Consistency detector "zone ⊄ owner flags" (ENT-062 double marking).

    Returns vault-relative paths of all Markdown pages inside declared zones
    whose frontmatter does not carry ``owner: human`` (missing, different or
    unparsable). Pure function; lint integration follows with BL-07/BL-18.
    """
    from agents import frontmatter

    violations: list[str] = []
    for zone in HUMAN_OWNED_ZONES:
        for md in sorted((wiki_root / zone).rglob("*.md")):
            try:
                fm, _ = frontmatter.read(md)
            except Exception:
                fm = {}
            if fm.get("owner") != "human":
                violations.append(md.relative_to(wiki_root).as_posix())
    return violations


def execute_writes(writes: list[WikiWrite], wiki_root: Path = VAULT_ROOT) -> list[str]:
    """Execute a list of WikiWrite operations on the current branch (draft).

    Returns list of written file paths.

    Raises HumanOwnedZoneError before any write is executed if even one
    path is inside a human-owned zone (no partial writes).
    """
    for write in writes:
        assert_writable(write["path"])

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


def approve_draft(wiki_root: Path = VAULT_ROOT) -> bool:
    """Merge draft → master. Called via Telegram callback after user approval."""
    result = subprocess.run(
        ["git", "merge", "draft", "--no-ff", "-m", "approved by user"],
        cwd=wiki_root, capture_output=True, text=True,
    )
    return result.returncode == 0


def reject_draft(wiki_root: Path = VAULT_ROOT) -> bool:
    """Reset draft branch to current master state."""
    cmds = [
        ["git", "checkout", "master"],
        ["git", "branch", "-D", "draft"],
        ["git", "checkout", "-b", "draft"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, cwd=wiki_root, capture_output=True)
        if result.returncode != 0:
            return False
    return True


def ensure_draft_branch(wiki_root: Path = VAULT_ROOT) -> None:
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
