"""language_agent.py — Language Module.

Creates VocabEntries, LanguageBridges, CulturalEntries. Manages Anki sync.
Full specification: doc/COMP_LANGUAGE.md
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.base_agent import BaseAgent
from agents.graph_writer import WikiWrite

WIKI_ROOT = Path(__file__).parent.parent


class LanguageAgentState(TypedDict):
    raw_event: dict
    user_profile: dict
    user_language_profile: dict
    graph_context: list
    detected_words: list[str]
    vocab_results: list[dict]
    bridge_results: list[dict]
    cultural_entry_result: dict | None
    anki_tasks: list[str]
    wiki_writes: list[WikiWrite]
    telegram_messages: list[str]


class LanguageAgent(BaseAgent):

    def process(self, state: dict) -> dict:
        """LangGraph node entry point — runs the full language workflow."""
        lang_state = LanguageAgentState(
            raw_event=state["raw_event"],
            user_profile=state.get("user_profile", {}),
            user_language_profile=state.get("user_language_profile", {}),
            graph_context=state.get("graph_context", []),
            detected_words=[],
            vocab_results=[],
            bridge_results=[],
            cultural_entry_result=None,
            anki_tasks=[],
            wiki_writes=[],
            telegram_messages=[],
        )
        result = _build_workflow(self).invoke(lang_state)
        return {
            **state,
            "agent_outputs": {**state.get("agent_outputs", {}), "language": result},
            "wiki_writes": state.get("wiki_writes", []) + result["wiki_writes"],
        }

    # -----------------------------------------------------------------------
    # Node implementations (called by LangGraph)
    # -----------------------------------------------------------------------

    def detect_words(self, state: LanguageAgentState) -> LanguageAgentState:
        """Detect foreign-language words in input (Haiku). See COMP_LANGUAGE.md §2.1."""
        raise NotImplementedError

    def create_vocab(self, state: LanguageAgentState) -> LanguageAgentState:
        """Create VocabEntry for each detected word (Sonnet). See COMP_LANGUAGE.md §2.3."""
        raise NotImplementedError

    def find_bridges(self, state: LanguageAgentState) -> LanguageAgentState:
        """Identify LanguageBridges (Sonnet). See COMP_LANGUAGE.md §3."""
        raise NotImplementedError

    def create_cultural(self, state: LanguageAgentState) -> LanguageAgentState:
        """Create CulturalEntry if triggered (Sonnet). See COMP_LANGUAGE.md §4."""
        raise NotImplementedError

    def schedule_anki(self, state: LanguageAgentState) -> LanguageAgentState:
        """Queue Anki export tasks for new elaborated VocabEntries. See COMP_LANGUAGE.md §5."""
        raise NotImplementedError

    def update_profile(self, state: LanguageAgentState) -> LanguageAgentState:
        """Increment language profile counters. See COMP_LANGUAGE.md §1.3."""
        raise NotImplementedError

    def write_entries(self, state: LanguageAgentState) -> LanguageAgentState:
        """Assemble WikiWrite objects from all results."""
        raise NotImplementedError


def _has_cultural_trigger(state: LanguageAgentState) -> str:
    hint = state["raw_event"].get("user_hint", "").lower()
    content = state["raw_event"].get("content", "").lower()
    triggers = ["kultur", "person", "ort", "madrid", "barcelona", "flamenco"]
    return "create_cultural" if any(t in hint + content for t in triggers) else "schedule_anki"


def _build_workflow(agent: LanguageAgent) -> StateGraph:
    wf = StateGraph(LanguageAgentState)
    wf.add_node("detect_words",    agent.detect_words)
    wf.add_node("create_vocab",    agent.create_vocab)
    wf.add_node("find_bridges",    agent.find_bridges)
    wf.add_node("create_cultural", agent.create_cultural)
    wf.add_node("schedule_anki",   agent.schedule_anki)
    wf.add_node("update_profile",  agent.update_profile)
    wf.add_node("write_entries",   agent.write_entries)

    wf.set_entry_point("detect_words")
    wf.add_edge("detect_words", "create_vocab")
    wf.add_edge("create_vocab", "find_bridges")
    wf.add_conditional_edges("find_bridges", _has_cultural_trigger,
                             {"create_cultural": "create_cultural",
                              "schedule_anki": "schedule_anki"})
    wf.add_edge("create_cultural", "schedule_anki")
    wf.add_edge("schedule_anki",   "update_profile")
    wf.add_edge("update_profile",  "write_entries")
    wf.add_edge("write_entries",   END)
    return wf.compile()
