"""main_workflow.py — LangGraph Hauptgraph des LLM-Personal-Knowledge-OS.

Verbindet alle Nodes nach ARCHITECTURE.md §5.1:
  classify → fetch_graph_context → [diary|language|...] → supervisor_review
  → write_to_graph → update_index
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

import anthropic
from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from agents import graph_reader
from agents.diary_agent import DiaryAgent
from agents.graph_reader import WikiPage
from agents.graph_writer import WikiWrite, execute_writes
from agents.supervisor import Supervisor

load_dotenv()

WIKI_ROOT = Path(__file__).parent


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class SupervisorState(TypedDict):
    raw_event: dict
    user_profile: dict
    graph_index: str
    classified_intent: str
    graph_context: list[WikiPage]
    assigned_agents: list[str]
    agent_outputs: dict
    supervisor_verdict: str
    review_notes: str
    wiki_writes: list[WikiWrite]
    telegram_messages: list[str]


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


def _update_index(state: SupervisorState) -> SupervisorState:
    """Stub: update index.md after graph writes. Full implementation later."""
    return state


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_workflow(wiki_root: Path = WIKI_ROOT):
    """Build and compile the LangGraph workflow. Call once at startup."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    supervisor = Supervisor(wiki_root=wiki_root, anthropic_client=client)
    diary     = DiaryAgent(wiki_root=wiki_root, anthropic_client=client)

    def write_node(state: SupervisorState) -> SupervisorState:
        """Execute WikiWrites unless supervisor rejected the output."""
        if state.get("supervisor_verdict") == "reject":
            return state
        writes = state.get("wiki_writes", [])
        if writes:
            execute_writes(writes, wiki_root=wiki_root)
        return state

    wf = StateGraph(SupervisorState)

    wf.add_node("classify",            supervisor.classify)
    wf.add_node("fetch_graph_context", lambda s: graph_reader.fetch_context(s, wiki_root))
    wf.add_node("diary_agent",         diary.process)
    wf.add_node("supervisor_review",   supervisor.review)
    wf.add_node("write_to_graph",      write_node)
    wf.add_node("update_index",        _update_index)

    wf.set_entry_point("classify")
    wf.add_edge("classify", "fetch_graph_context")

    # supervisor.route returns node names ("diary_agent", "language_agent", etc.)
    # Map unimplemented routes to supervisor_review until agents are built.
    wf.add_conditional_edges(
        "fetch_graph_context",
        supervisor.route,
        {
            "diary_agent":    "diary_agent",
            "language_agent": "supervisor_review",   # TODO: implement LanguageAgent
            "both":           "diary_agent",          # simplified: diary only for now
            "query_flow":     "supervisor_review",    # TODO: implement query flow
            "lint_agent":     "supervisor_review",    # TODO: implement LintAgent
        },
    )

    wf.add_edge("diary_agent",       "supervisor_review")
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
