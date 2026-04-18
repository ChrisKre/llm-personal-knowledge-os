"""diary_agent.py — Personal Facts Engine.

Extracts PersonalFacts, scores them, finds correlations, elaborates high-score facts.
Full specification: doc/COMP_DIARY.md
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.base_agent import BaseAgent
from agents.graph_writer import WikiWrite

WIKI_ROOT = Path(__file__).parent.parent


class DiaryAgentState(TypedDict):
    raw_event: dict
    user_profile: dict
    graph_context: list
    extracted_fact: dict | None
    story_score_result: dict | None
    correlation_result: dict | None
    elaboration_result: dict | None
    wiki_writes: list[WikiWrite]
    telegram_messages: list[str]


class DiaryAgent(BaseAgent):

    def process(self, state: dict) -> dict:
        """LangGraph node entry point — runs the full diary workflow."""
        diary_state = DiaryAgentState(
            raw_event=state["raw_event"],
            user_profile=state.get("user_profile", {}),
            graph_context=state.get("graph_context", []),
            extracted_fact=None,
            story_score_result=None,
            correlation_result=None,
            elaboration_result=None,
            wiki_writes=[],
            telegram_messages=[],
        )
        result = _build_workflow(self).invoke(diary_state)
        return {
            **state,
            "agent_outputs": {**state.get("agent_outputs", {}), "diary": result},
            "wiki_writes": state.get("wiki_writes", []) + result["wiki_writes"],
        }

    # -----------------------------------------------------------------------
    # Node implementations (called by LangGraph)
    # -----------------------------------------------------------------------

    def extract_fact(self, state: DiaryAgentState) -> DiaryAgentState:
        """Extract PersonalFact fields from raw event (Haiku)."""
        # TODO: implement extraction prompt (see COMP_DIARY.md §3.2)
        raise NotImplementedError

    def score_punchline(self, state: DiaryAgentState) -> DiaryAgentState:
        """Run punchline mini-prompt before main scoring (Haiku). See COMP_DIARY.md §3.3."""
        raise NotImplementedError

    def score_main(self, state: DiaryAgentState) -> DiaryAgentState:
        """Run main story_score prompt (Sonnet). See COMP_DIARY.md §3.2."""
        raise NotImplementedError

    def find_correlations(self, state: DiaryAgentState) -> DiaryAgentState:
        """Tag-overlap filter (Haiku) + cluster analysis (Sonnet). See COMP_DIARY.md §5."""
        raise NotImplementedError

    def elaborate(self, state: DiaryAgentState) -> DiaryAgentState:
        """Elaborate fact if story_score >= 6 (Sonnet). See COMP_DIARY.md §4."""
        raise NotImplementedError

    def write_fact(self, state: DiaryAgentState) -> DiaryAgentState:
        """Assemble WikiWrite objects from all results."""
        raise NotImplementedError


def _should_elaborate(state: DiaryAgentState) -> str:
    score = (state["story_score_result"] or {}).get("gesamt", 0)
    return "elaborate" if score >= 6 else "write_fact"


def _build_workflow(agent: DiaryAgent) -> StateGraph:
    wf = StateGraph(DiaryAgentState)
    wf.add_node("extract_fact",       agent.extract_fact)
    wf.add_node("score_punchline",    agent.score_punchline)
    wf.add_node("score_main",         agent.score_main)
    wf.add_node("find_correlations",  agent.find_correlations)
    wf.add_node("elaborate",          agent.elaborate)
    wf.add_node("write_fact",         agent.write_fact)

    wf.set_entry_point("extract_fact")
    wf.add_edge("extract_fact",    "score_punchline")
    wf.add_edge("score_punchline", "score_main")
    wf.add_edge("score_main",      "find_correlations")
    wf.add_conditional_edges("find_correlations", _should_elaborate,
                             {"elaborate": "elaborate", "write_fact": "write_fact"})
    wf.add_edge("elaborate",  "write_fact")
    wf.add_edge("write_fact", END)
    return wf.compile()
