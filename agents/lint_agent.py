"""lint_agent.py — Daily graph health checks and auto-repair.

Runs daily at 03:00 via systemd-Timer or Python schedule.
Full specification: doc/KNOWLEDGE_GRAPH.md §5
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from agents.base_agent import BaseAgent
from agents.graph_writer import WikiWrite

WIKI_ROOT = Path(__file__).parent.parent

STALE_RAW_DAYS = 7
HIGH_SCORE_UNEXERCISED_DAYS = 14
HIGH_SCORE_THRESHOLD = 7


@dataclass
class LintTask:
    symptom: str           # "orphan" | "stale_raw" | "missing_backlink" | "high_score_unexercised" | "anki_gap" | "contradiction"
    page_path: str
    priority: str          # "HIGH" | "MEDIUM" | "LOW"
    auto_fix: bool
    description: str
    fix_action: str = ""   # description of the fix to apply


@dataclass
class LintReport:
    auto_fixable: list[LintTask] = field(default_factory=list)
    needs_user: list[LintTask] = field(default_factory=list)
    summary: str = ""


class LintAgent(BaseAgent):

    def process(self, state: dict) -> dict:
        """LangGraph node entry point — runs full lint pass."""
        wiki_root = Path(state.get("wiki_root", WIKI_ROOT))
        report = self.run_lint(wiki_root)

        auto_fix_writes = self._apply_auto_fixes(report.auto_fixable, wiki_root)
        user_messages = self._format_user_tasks(report.needs_user)

        return {
            **state,
            "lint_report": report,
            "wiki_writes": state.get("wiki_writes", []) + auto_fix_writes,
            "telegram_messages": state.get("telegram_messages", []) + user_messages,
        }

    def run_lint(self, wiki_root: Path) -> LintReport:
        """Full lint pass — detect all symptoms across the graph."""
        report = LintReport()

        stale = self.scan_stale_raw(wiki_root)
        report.auto_fixable.extend([t for t in stale if t.auto_fix])
        report.needs_user.extend([t for t in stale if not t.auto_fix])

        anki_gaps = self.scan_anki_gaps(wiki_root)
        report.auto_fixable.extend([t for t in anki_gaps if t.auto_fix])
        report.needs_user.extend([t for t in anki_gaps if not t.auto_fix])

        orphans = self.scan_orphans(wiki_root)
        report.auto_fixable.extend([t for t in orphans if t.auto_fix])
        report.needs_user.extend([t for t in orphans if not t.auto_fix])

        high_score = self.scan_high_score_unexercised(wiki_root)
        report.needs_user.extend(high_score)

        n_auto = len(report.auto_fixable)
        n_user = len(report.needs_user)
        report.summary = (
            f"Lint: {n_auto} auto-fixable, {n_user} needs user — "
            f"{len(stale)} stale_raw, {len(anki_gaps)} anki_gap, "
            f"{len(orphans)} orphan, {len(high_score)} high_score_unexercised"
        )
        return report

    # -----------------------------------------------------------------------
    # Lint scanners
    # -----------------------------------------------------------------------

    def scan_stale_raw(self, wiki_root: Path, stale_days: int = STALE_RAW_DAYS) -> list[LintTask]:
        """Find PersonalFacts and VocabEntries with status:raw older than stale_days."""
        tasks: list[LintTask] = []
        cutoff = date.today() - timedelta(days=stale_days)

        wiki_dir = wiki_root / "wiki"
        if not wiki_dir.exists():
            return tasks

        for md_file in wiki_dir.rglob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
            except OSError:
                continue

            if not _frontmatter_has(text, "status", "raw"):
                continue

            created = _parse_frontmatter_date(text, "created")
            if created is None or created > cutoff:
                continue

            rel_path = str(md_file.relative_to(wiki_root)).replace("\\", "/")
            page_type = _parse_frontmatter_field(text, "type") or "Unknown"

            tasks.append(LintTask(
                symptom="stale_raw",
                page_path=rel_path,
                priority="MEDIUM",
                auto_fix=False,
                description=(
                    f"{page_type} seit {created.isoformat()} im status:raw — "
                    f"mehr als {stale_days} Tage unverarbeitet."
                ),
                fix_action="elaborieren oder auf status:archived setzen",
            ))

        return tasks

    def scan_anki_gaps(self, wiki_root: Path) -> list[LintTask]:
        """Find elaborated VocabEntries that have no anki_id yet."""
        tasks: list[LintTask] = []
        vocab_dir = wiki_root / "wiki/language/vocab"
        if not vocab_dir.exists():
            return tasks

        for md_file in vocab_dir.rglob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
            except OSError:
                continue

            if not _frontmatter_has(text, "status", "elaborated"):
                continue
            if not _frontmatter_has(text, "anki_id", "null"):
                continue

            rel_path = str(md_file.relative_to(wiki_root)).replace("\\", "/")
            word = _parse_frontmatter_field(text, "word") or md_file.stem

            tasks.append(LintTask(
                symptom="anki_gap",
                page_path=rel_path,
                priority="LOW",
                auto_fix=True,
                description=f"VocabEntry '{word}' ist elaboriert aber hat keine Anki-Karte.",
                fix_action="AnkiConnect-Export auslösen (wenn Anki läuft)",
            ))

        return tasks

    def scan_orphans(self, wiki_root: Path) -> list[LintTask]:
        """Find wiki pages with empty related: field."""
        tasks: list[LintTask] = []
        wiki_dir = wiki_root / "wiki"
        if not wiki_dir.exists():
            return tasks

        for md_file in wiki_dir.rglob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
            except OSError:
                continue

            # Only check pages that have a type field
            if not _parse_frontmatter_field(text, "type"):
                continue

            related = _parse_frontmatter_field(text, "related")
            if related is not None and related.strip() in ("[]", "", "null"):
                rel_path = str(md_file.relative_to(wiki_root)).replace("\\", "/")
                tasks.append(LintTask(
                    symptom="orphan",
                    page_path=rel_path,
                    priority="LOW",
                    auto_fix=True,
                    description="Seite hat keine related:-Links — verwaist im Graph.",
                    fix_action="3 semantisch verwandte Seiten suchen und verlinken",
                ))

        return tasks

    def scan_high_score_unexercised(
        self,
        wiki_root: Path,
        threshold: int = HIGH_SCORE_THRESHOLD,
        days: int = HIGH_SCORE_UNEXERCISED_DAYS,
    ) -> list[LintTask]:
        """Find PersonalFacts with story_score >= threshold that haven't been practiced."""
        tasks: list[LintTask] = []
        facts_dir = wiki_root / "wiki/personal/facts"
        if not facts_dir.exists():
            return tasks

        cutoff = date.today() - timedelta(days=days)

        for md_file in facts_dir.rglob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
            except OSError:
                continue

            score_str = _parse_frontmatter_field(text, "story_score")
            try:
                score = int(score_str or "0")
            except ValueError:
                continue

            if score < threshold:
                continue

            # Check practice_log: if empty list or no entries → flag
            practice_match = re.search(r"^practice_log:\s*\[\]", text, re.MULTILINE)
            if not practice_match:
                # Non-empty practice_log → already exercised
                continue

            created = _parse_frontmatter_date(text, "created")
            if created and created > cutoff:
                continue  # Too recent to flag

            rel_path = str(md_file.relative_to(wiki_root)).replace("\\", "/")
            tasks.append(LintTask(
                symptom="high_score_unexercised",
                page_path=rel_path,
                priority="MEDIUM",
                auto_fix=False,
                description=(
                    f"story_score: {score} — noch nie geübt. "
                    f"Potenzial wird verschenkt."
                ),
                fix_action="Story-Lab Übungsrunde vorschlagen",
            ))

        return tasks

    def _apply_auto_fixes(
        self, tasks: list[LintTask], wiki_root: Path
    ) -> list[WikiWrite]:
        """Apply all auto-fixable tasks and return the resulting WikiWrite objects."""
        writes: list[WikiWrite] = []
        for task in tasks:
            match task.symptom:
                case "missing_backlink":
                    # TODO: append backlink to target page
                    pass
                case "anki_gap":
                    # TODO: call AnkiConnect and write anki_id back
                    pass
                case "orphan":
                    # TODO: find 3 semantically related pages and add related: links
                    pass
        return writes

    @staticmethod
    def _format_user_tasks(tasks: list[LintTask]) -> list[str]:
        """Format non-auto-fixable tasks as Telegram messages."""
        messages = []
        for task in tasks:
            messages.append(
                f"⚠️ [{task.priority}] {task.symptom}: {task.description}\n"
                f"Seite: {task.page_path}"
            )
        return messages


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _frontmatter_has(text: str, field: str, value: str) -> bool:
    """Check if a frontmatter field contains the given value."""
    pattern = rf"^{re.escape(field)}:\s*{re.escape(value)}\s*$"
    return bool(re.search(pattern, text, re.MULTILINE | re.IGNORECASE))


def _parse_frontmatter_field(text: str, field: str) -> str | None:
    """Extract a frontmatter field value."""
    m = re.search(rf"^{re.escape(field)}:\s*(.+)$", text, re.MULTILINE)
    if m:
        return m.group(1).strip().strip('"\'')
    return None


def _parse_frontmatter_date(text: str, field: str) -> date | None:
    """Parse a YYYY-MM-DD date from a frontmatter field."""
    val = _parse_frontmatter_field(text, field)
    if not val:
        return None
    m = re.match(r"(\d{4}-\d{2}-\d{2})", val)
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None
