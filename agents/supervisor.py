"""supervisor.py — Routing, classification and review layer.

The supervisor is NOT a regular LLM agent. It is the orchestration and evaluation
layer: it routes inputs to agents, combines their outputs, and decides whether
graph writes are approved.

Three stages (from ARCHITECTURE.md §3.3):
  1. classify  — what is this input? (Haiku)
  2. route     — which agent(s) handle it? (pure logic, no LLM)
  3. review    — is the agent output consistent and correct? (Haiku/Sonnet)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.base_agent import BaseAgent

WIKI_ROOT = Path(__file__).parent.parent

CLASSIFY_PROMPT = """\
Classify the following input from a user's personal knowledge system.

Input:
---
{content}
---

User hint (if any): {user_hint}

Classify into exactly one of these intents:
- vocab        → a foreign-language word or expression the user wants to learn
- personal_fact → a personal experience, observation, or story the user is sharing
- both         → contains both a personal experience AND a foreign-language element
- query        → a question to the knowledge graph
- lint         → a maintenance/cleanup request

Answer with exactly one word (the intent label).
"""

REVIEW_PROMPT = """\
You are reviewing LLM agent outputs before they are written to a personal knowledge graph.

User profile summary:
{user_profile_summary}

Graph context (relevant existing pages):
{graph_context_summary}

Agent outputs to review:
{agent_outputs_summary}

Check:
1. Is the story_score consistent with similar facts in graph context?
2. Are relevant cross-references from graph context included?
3. Are there contradictions with existing wiki pages?
4. Is sensitivity tier correctly assigned?

Answer:
verdict: accept | revise | reject
issues: [list of specific issues, or "none"]
"""


class Supervisor(BaseAgent):

    def process(self, state: dict) -> dict:
        raise NotImplementedError("Use classify(), route(), and review() directly.")

    def classify(self, state: dict) -> dict:
        """Stage 1: classify the intent of the raw event."""
        raw_event = state.get("raw_event", {})
        content = raw_event.get("content", "")
        user_hint = raw_event.get("user_hint", "")

        if not content:
            return {**state, "classified_intent": "lint"}

        prompt = CLASSIFY_PROMPT.format(content=content[:500], user_hint=user_hint)
        intent = self._haiku(prompt).strip().lower()

        # Normalize to known intents
        if intent not in {"vocab", "personal_fact", "both", "query", "lint"}:
            intent = "both"  # safe fallback

        return {**state, "classified_intent": intent}

    @staticmethod
    def route(state: dict) -> str:
        """Stage 2: pure routing logic based on classified_intent.

        Returns the next node name for LangGraph conditional edges.
        """
        intent = state.get("classified_intent", "both")
        routing = {
            "vocab":         "language_agent",
            "personal_fact": "diary_agent",
            "both":          "both",          # LangGraph handles parallel dispatch
            "query":         "query_flow",
            "lint":          "lint_agent",
        }
        return routing.get(intent, "both")

    def review(self, state: dict) -> dict:
        """Stage 3: review agent outputs before writing to graph."""
        agent_outputs = state.get("agent_outputs", {})
        user_profile = state.get("user_profile", {})
        graph_context = state.get("graph_context", [])

        # Build concise summaries for the review prompt
        profile_summary = self._summarize_profile(user_profile)
        context_summary = self._summarize_context(graph_context)
        outputs_summary = self._summarize_outputs(agent_outputs)

        prompt = REVIEW_PROMPT.format(
            user_profile_summary=profile_summary,
            graph_context_summary=context_summary,
            agent_outputs_summary=outputs_summary,
        )
        review_text = self._haiku(prompt)

        verdict = "accept"
        for line in review_text.splitlines():
            if line.lower().startswith("verdict:"):
                verdict = line.split(":", 1)[1].strip().lower()
                break

        return {**state, "supervisor_verdict": verdict, "review_notes": review_text}

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _summarize_profile(profile: dict) -> str:
        if not profile:
            return "(no profile loaded)"
        lines = [f"- {k}: {v}" for k, v in list(profile.items())[:10]]
        return "\n".join(lines)

    @staticmethod
    def _summarize_context(context: list) -> str:
        if not context:
            return "(empty graph context)"
        return "\n".join(
            f"- [{p.page_type}] {p.title}: {p.summary[:80]}"
            for p in context[:5]
        )

    @staticmethod
    def _summarize_outputs(outputs: dict) -> str:
        if not outputs:
            return "(no agent outputs)"
        lines = []
        for agent, result in outputs.items():
            if isinstance(result, dict):
                lines.append(f"{agent}: {list(result.keys())}")
            else:
                lines.append(f"{agent}: {str(result)[:100]}")
        return "\n".join(lines)
