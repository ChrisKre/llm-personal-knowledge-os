"""lint_agent.py — Daily graph health checks and auto-repair.

Runs daily at 03:00 via systemd-Timer or Python schedule.
Full specification: doc/KNOWLEDGE_GRAPH.md §5
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
        # TODO: implement full lint pass (see KNOWLEDGE_GRAPH.md §5.1)
        # Steps:
        #   all_pages = load_all_pages(wiki_root)
        #   link_graph = build_link_graph(all_pages)
        #   for each page: check_orphan, check_stale_raw, check_missing_backlinks,
        #                  check_score_vs_status, check_anki_gap
        #   + check_contradictions(all_pages)   ← Haiku candidates + Sonnet analysis
        raise NotImplementedError

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
