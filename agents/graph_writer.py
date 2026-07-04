"""graph_writer.py — WikiWrite execution and Draft→Master branch workflow."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TypedDict


class WikiWrite(TypedDict):
    path: str        # relative path from repo root, e.g. "wiki/language/vocab/v_es_madrugada.md"
    content: str     # full markdown content
    operation: str   # "create" | "update" | "append"


WIKI_ROOT = Path(__file__).parent.parent

# Human-owned Zonen (SCHEMA §2, ENT-062) — Verzeichnisse, in die die KI nie
# schreibt. Single-Source: Guard (assert_writable) und Konsistenz-Detektor
# (find_zone_owner_violations) lesen beide diese Liste.
HUMAN_OWNED_ZONES: tuple[str, ...] = ("wiki/personal/health/",)


class HumanOwnedZoneError(Exception):
    """Write-Versuch in eine deklarierte human-owned Zone (Axiom-2-Carve-out)."""


def assert_writable(path: str) -> None:
    """Geteilte Zonen-Prüfung vor jedem Datei-Write (ENT-062, QK-19).

    Wird von execute_writes() aufgerufen und muss von jedem künftigen
    Write-Pfad (z.B. BL-07-Lint-Auto-Fixes) vor dem Schreiben importiert
    und aufgerufen werden — kein zweiter Zonen-Check-Codepfad.

    Raises HumanOwnedZoneError für Pfade in einer deklarierten Zone.
    Case-insensitiv (Windows-Dateisystem), Backslash-tolerant.
    """
    norm = path.replace("\\", "/").lstrip("./").casefold()
    for zone in HUMAN_OWNED_ZONES:
        if norm.startswith(zone.casefold()):
            raise HumanOwnedZoneError(
                f"'{path}' liegt in der human-owned Zone '{zone}' — "
                f"KI-Writes sind dort verboten (SCHEMA §1 Axiom 2, ENT-062)."
            )


def find_zone_owner_violations(wiki_root: Path = WIKI_ROOT) -> list[str]:
    """Konsistenz-Detektor „Zone ⊄ owner-Flags" (ENT-062 Doppel-Kennzeichnung).

    Liefert repo-relative Pfade aller Markdown-Seiten in deklarierten Zonen,
    deren Frontmatter kein ``owner: human`` trägt (fehlend, abweichend oder
    unparsbar). Pure Function — Lint-Integration folgt mit BL-07/BL-18.
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


def execute_writes(writes: list[WikiWrite], wiki_root: Path = WIKI_ROOT) -> list[str]:
    """Execute a list of WikiWrite operations on the current branch (draft).

    Returns list of written file paths.

    Raises HumanOwnedZoneError bevor irgendein Write ausgeführt wird, wenn
    auch nur ein Pfad in einer human-owned Zone liegt (kein Partial-Write).
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


def approve_draft(wiki_root: Path = WIKI_ROOT) -> bool:
    """Merge draft → master. Called via Telegram callback after user approval."""
    result = subprocess.run(
        ["git", "merge", "draft", "--no-ff", "-m", "approved by user"],
        cwd=wiki_root, capture_output=True, text=True,
    )
    return result.returncode == 0


def reject_draft(wiki_root: Path = WIKI_ROOT) -> bool:
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
