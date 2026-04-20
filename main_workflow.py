"""main_workflow.py — LangGraph Hauptgraph des LLM-Personal-Knowledge-OS.

Verbindet alle Nodes nach ARCHITECTURE.md §5.1:
  classify → fetch_graph_context → [diary|language|...] → supervisor_review
  → write_to_graph → update_index
"""

from __future__ import annotations

import operator
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Annotated, TypedDict

import anthropic
from dotenv import load_dotenv
from langgraph.constants import Send
from langgraph.graph import END, StateGraph

from agents import graph_reader
from agents.diary_agent import DiaryAgent
from agents.graph_reader import WikiPage
from agents.graph_writer import WikiWrite, execute_writes
from agents.language_agent import LanguageAgent
from agents.supervisor import Supervisor

load_dotenv()

WIKI_ROOT = Path(__file__).parent


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def _merge_dicts(a: dict, b: dict) -> dict:
    return {**a, **b}


class SupervisorState(TypedDict):
    raw_event: dict
    user_profile: dict
    graph_index: str
    classified_intent: str
    graph_context: list[WikiPage]
    assigned_agents: list[str]
    agent_outputs: Annotated[dict, _merge_dicts]
    supervisor_verdict: str
    review_notes: str
    wiki_writes: Annotated[list[WikiWrite], operator.add]
    telegram_messages: Annotated[list[str], operator.add]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_user_profile(wiki_root: Path) -> dict:
    """Parse user_profile.md into a flat dict (best-effort, key: value lines)."""
    profile_path = wiki_root / "user_profile.md"
    if not profile_path.exists():
        return {}
    profile: dict = {}
    for line in profile_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and ": " in stripped:
            k, _, v = stripped[2:].partition(": ")
            profile[k.strip()] = v.strip()
    return profile


def _load_graph_index(wiki_root: Path) -> str:
    index_path = wiki_root / "index.md"
    if not index_path.exists():
        return "(index.md existiert noch nicht)"
    return index_path.read_text(encoding="utf-8")[:4000]


def _update_index(state: SupervisorState, wiki_root: Path = WIKI_ROOT) -> SupervisorState:  # noqa: C901
    """Append newly written pages to index.md after graph writes."""
    writes = state.get("wiki_writes", [])
    if not writes:
        return state

    index_path = wiki_root / "index.md"
    log_path = wiki_root / "log.md"

    index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""

    # Section headers in index.md mapped to path prefixes
    _SECTION_MAP = {
        "wiki/personal/facts/":       "PersonalFacts",
        "wiki/language/vocab/v_es_":  "VocabEntries — ES",
        "wiki/language/vocab/v_en_":  "VocabEntries — EN",
        "wiki/language/vocab/":       "VocabEntries — ES",   # fallback
        "wiki/language/culture/":     "CulturalEntries",
        "wiki/language/bridges/":     "LanguageBridges",
        "wiki/concepts/":             "Concepts",
        "wiki/personal/style_refs/":  "StyleProfiles",
    }

    # Build per-section additions
    additions: dict[str, list[str]] = {}
    for write in writes:
        path = write["path"]
        section = None
        for prefix, sec in _SECTION_MAP.items():
            if path.startswith(prefix):
                section = sec
                break
        if section is None:
            continue

        filename = Path(path).stem  # e.g. "pf_2026-04-18_flamenco-kurs"
        summary = _extract_summary_from_write(write)
        entry = f"- [[{filename}]] — {summary}"

        if section not in additions:
            additions[section] = []
        additions[section].append((filename, entry))

    if not additions:
        return state

    # Insert entries into the correct sections and update counts
    updated = index_text
    for section, entries in additions.items():
        section_pattern = re.compile(
            rf"(## {re.escape(section)}) \((\d+)\)", re.MULTILINE
        )
        match = section_pattern.search(updated)
        new_entries = [
            entry for filename, entry in entries
            if f"[[{filename}]]" not in updated
        ]
        if not new_entries:
            continue
        if match:
            old_count = int(match.group(2))
            new_count = old_count + len(new_entries)
            updated = updated[:match.start()] + f"{match.group(1)} ({new_count})" + updated[match.end():]
            insert_at = updated.index(f"{match.group(1)} ({new_count})") + len(f"{match.group(1)} ({new_count})")
            insert_block = "\n" + "\n".join(new_entries)
            updated = updated[:insert_at] + insert_block + updated[insert_at:]
        else:
            updated += f"\n## {section} ({len(new_entries)})\n" + "\n".join(new_entries) + "\n"

    if updated != index_text:
        index_path.write_text(updated, encoding="utf-8")

    # Append to log.md
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M")
    written_paths = ", ".join(Path(w["path"]).name for w in writes)
    log_entry = f"\n## [{ts}] ingest | {written_paths}\n"
    if log_path.exists():
        with log_path.open("a", encoding="utf-8") as f:
            f.write(log_entry)
    else:
        log_path.write_text(f"# Operationslog\n{log_entry}", encoding="utf-8")

    return state


def _extract_summary_from_write(write: WikiWrite) -> str:
    """Extract a short summary from WikiWrite content for the index."""
    content = write.get("content", "")
    path = write.get("path", "")

    # Try to find story_score in frontmatter
    score_m = re.search(r"^story_score:\s*(\d+)", content, re.MULTILINE)

    # Try first heading
    heading_m = re.search(r"^# (.+)$", content, re.MULTILINE)
    title = heading_m.group(1).strip() if heading_m else Path(path).stem

    if score_m:
        return f"{title}, story_score: {score_m.group(1)}"

    # For VocabEntries: show language
    lang_m = re.search(r"^language:\s*(\w+)", content, re.MULTILINE)
    if lang_m:
        return f"{title} [{lang_m.group(1)}]"

    return title


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_workflow(wiki_root: Path = WIKI_ROOT):
    """Build and compile the LangGraph workflow. Call once at startup.

    Provider selection (automatic):
      ANTHROPIC_API_KEY set   → Claude Haiku/Sonnet (Produktion)
      ANTHROPIC_API_KEY unset → Ollama lokal (Tests, kein API-Key nötig)
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
    else:
        import logging as _logging
        _logging.getLogger(__name__).warning(
            "ANTHROPIC_API_KEY nicht gesetzt — Ollama-Fallback aktiv. "
            "Setze OLLAMA_MODEL und stelle sicher dass `ollama serve` läuft."
        )
        client = None

    supervisor = Supervisor(wiki_root=wiki_root, anthropic_client=client)
    diary      = DiaryAgent(wiki_root=wiki_root, anthropic_client=client)
    language   = LanguageAgent(wiki_root=wiki_root, anthropic_client=client)

    def write_node(state: SupervisorState) -> dict:
        if state.get("supervisor_verdict") != "reject":
            writes = state.get("wiki_writes", [])
            if writes:
                execute_writes(writes, wiki_root=wiki_root)
        return {}

    def index_node(state: SupervisorState) -> dict:
        _update_index(state, wiki_root=wiki_root)
        return {}

    wf = StateGraph(SupervisorState)

    wf.add_node("classify",            supervisor.classify)
    wf.add_node("fetch_graph_context", lambda s: graph_reader.fetch_context(s, wiki_root))
    wf.add_node("diary_agent",         diary.process)
    wf.add_node("language_agent",      language.process)
    wf.add_node("supervisor_review",   supervisor.review)
    wf.add_node("write_to_graph",      write_node)
    wf.add_node("update_index",        index_node)

    wf.set_entry_point("classify")
    wf.add_edge("classify", "fetch_graph_context")

    _route_map = {
        "diary_agent":    "diary_agent",
        "language_agent": "language_agent",
        "query_flow":     "supervisor_review",
        "lint_agent":     "supervisor_review",
    }

    def route_after_context(state: SupervisorState):
        intent = supervisor.route(state)
        if intent == "both":
            return [Send("diary_agent", state), Send("language_agent", state)]
        return _route_map.get(intent, "supervisor_review")

    wf.add_conditional_edges("fetch_graph_context", route_after_context)

    wf.add_edge("diary_agent",       "supervisor_review")
    wf.add_edge("language_agent",    "supervisor_review")
    wf.add_edge("supervisor_review", "write_to_graph")
    wf.add_edge("write_to_graph",    "update_index")
    wf.add_edge("update_index",      END)

    return wf.compile()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

# Module-level compiled graph — built once, reused per process.
_graph = None


def _get_graph(wiki_root: Path = WIKI_ROOT):
    global _graph
    if _graph is None:
        _graph = build_workflow(wiki_root)
    return _graph


def run_ingest(raw_event: dict, wiki_root: Path = WIKI_ROOT) -> dict:
    """Process a single raw event through the full agent pipeline.

    Args:
        raw_event: Dict from ExtractedContent.to_raw_event() or raw/events/ JSON.
        wiki_root: Repo root (default: directory containing this file).

    Returns:
        Final SupervisorState dict with wiki_writes, supervisor_verdict, etc.
    """
    graph = _get_graph(wiki_root)

    initial_state = SupervisorState(
        raw_event=raw_event,
        user_profile=_load_user_profile(wiki_root),
        graph_index=_load_graph_index(wiki_root),
        classified_intent="",
        graph_context=[],
        assigned_agents=[],
        agent_outputs={},
        supervisor_verdict="",
        review_notes="",
        wiki_writes=[],
        telegram_messages=[],
    )

    return graph.invoke(initial_state)
