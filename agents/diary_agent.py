"""diary_agent.py — Personal Facts Engine.

Extracts PersonalFacts, scores them, finds correlations, elaborates high-score facts.
Full specification: doc/COMP_DIARY.md
"""

from __future__ import annotations

import re
from datetime import date
from textwrap import dedent
from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.base_agent import BaseAgent
from agents.graph_writer import WikiWrite

TAG_OVERLAP_THRESHOLD = 2
CONCEPT_THRESHOLD = 3


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Prompts  (from COMP_DIARY.md §3.2, §3.3, §4.3, §5.2, §5.3)
# ---------------------------------------------------------------------------

_EXTRACT_PROMPT = """\
Extract a PersonalFact from the following user input.
The user is building a personal knowledge graph for storytelling and social conversations.

Input:
---
{content}
---

User hint: {user_hint}
Today's date: {today}

Extract these fields. If a field cannot be determined, use a sensible default.

Respond in this exact format (one field per line):
title: [Short memorable title, max 8 words — will become part of the filename]
date: [YYYY-MM-DD — date of the event, use today if event happened today]
context_when: [When did this happen? Time period or situation]
context_where: [Where did this happen? City, place, or context]
context_with: [With whom? Or "alleine" if unclear]
core_fact: [The raw fact in 1-2 sentences. Concrete, no embellishment.]
tags: [comma-separated, 3-6 lowercase tags, e.g. spanisch, tanzen, lernen, musik]
sensitivity: [public | sensitive | private]
"""

_PUNCHLINE_PROMPT = """\
Analyse whether this personal moment has a punchline or twist.

Personal fact:
---
{core_fact}
---

Question 1: What does a listener expect at the end of this story — based on how it starts?
Question 2: What happens instead? Is there an expectation break, irony, or self-revelation?

Score:
2 — Real expectation break. The ending is surprising, ironic, or self-revealing.
1 — Slight twist. Small irony or unexpected detail, but outcome basically foreseeable.
0 — No expectation break. The event ends as it began.

Respond in this exact format:
score: [0/1/2]
reason: [1 sentence — what exactly is the twist, or why it is missing]
potential: [If score < 2: how could a punchline be developed? 1 concrete sentence. If score is 2: "stark"]
"""

_SCORE_MAIN_PROMPT = """\
Rate this personal moment on its storytelling potential.
Context: The user wants to become more interesting in social conversations.

Personal Fact:
---
{core_fact}

Context: {context}
---

Punchline pre-assessment: {punchline_summary}

Rate on four dimensions. Justify each score in one sentence after a pipe.

Format for each dimension: field: [score] | reason: [1 sentence]

1. ueberraschung: [0-3] | reason: [...]
   (0=foreseeable | 1=slightly unexpected | 2=surprising | 3=stunning)
   Question: "Could a listener have predicted this ending?"

2. anschlussfaehigkeit: [0-3] | reason: [...]
   (0=very niche | 1=understandable | 2=universal | 3="I know that feeling!")
   Question: "Can someone who doesn't know the user empathize?"

3. sensorik: [0-2] | reason: [...]
   (0=abstract | 1=one concrete image | 2=vivid details, you are there)
   Question: "Can the listener picture the scene?"

4. pointe: [use the punchline score from the pre-assessment] | reason: [from pre-assessment]

Then add:
gesamt: [sum of all four scores]
narrative_hook: [1-2 sentences — what makes this moment potentially worth telling?]
"""

_CORRELATIONS_PROMPT = """\
Analyse whether several personal moments of a user share a common pattern.

New fact: {new_fact}

Related facts (by tag overlap):
{candidates}

Questions:
1. What connects these moments thematically? (1 sentence)
2. Is there an overarching theme or development emerging?
3. Has the user's attitude or reaction changed across the facts?

If 3+ facts share the same core theme: suggest a Concept page title.
Format suggestion: "Mein [Thema]-Weg" or "[Thema] als roter Faden"

Respond:
verbindung: [1 sentence]
entwicklung: [1 sentence, or "noch nicht erkennbar"]
concept_title: [suggestion or null]
concept_summary: [2-3 sentences if concept_title is not null, else null]
"""

_ELABORATE_PROMPT = """\
Elaborate a personal moment into a tellable story.

Related knowledge from graph:
{graph_context_summary}

Personal Fact (raw):
---
title: {title}
core_fact: {core_fact}
context: {context}
story_score: {story_score}
punchline_potential: {punchline_potential}
---

Tasks:
1. Write an "ausarbeitung" in 3-5 sentences — the story as the user would tell it to a friend.
   Natural language, not essay style. German preferred.
2. Sharpen the narrative_hook: 1-2 sentences naming the core interesting element.
3. Suggest social_context: when and for whom is this story suitable?
4. If punchline_potential exists: build the punchline into the ausarbeitung.
5. Find 2-3 meaningful related links from graph context (wiki paths, or "none").

Respond:
ausarbeitung: [3-5 sentences]
narrative_hook: [1-2 sentences]
social_context_when: [situation description]
social_context_mood: [locker | tiefgründig | humorvoll | gemischt]
related: [wiki paths separated by newlines, or "none"]
story_score_revision: [revised score if elaboration strengthened punchline, else null]
"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class DiaryAgent(BaseAgent):

    def process(self, state: dict) -> dict:
        """LangGraph node entry point — runs the full diary sub-workflow."""
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
            "agent_outputs":     {"diary": result},
            "wiki_writes":       result["wiki_writes"],
            "telegram_messages": result["telegram_messages"],
        }

    # -----------------------------------------------------------------------
    # Node: extract_fact
    # -----------------------------------------------------------------------

    def extract_fact(self, state: DiaryAgentState) -> DiaryAgentState:
        """Extract PersonalFact fields from raw event content (Haiku)."""
        raw_event = state["raw_event"]
        content   = raw_event.get("content", "")
        user_hint = raw_event.get("user_hint", "")

        prompt = _EXTRACT_PROMPT.format(
            content=content[:1200],
            user_hint=user_hint or "none",
            today=date.today().isoformat(),
        )
        response = self._haiku(prompt)
        extracted = _parse_kv(response)
        extracted["raw_content"]   = content
        extracted["source_event"]  = raw_event.get("timestamp", date.today().isoformat())

        return {**state, "extracted_fact": extracted}

    # -----------------------------------------------------------------------
    # Node: score_punchline
    # -----------------------------------------------------------------------

    def score_punchline(self, state: DiaryAgentState) -> DiaryAgentState:
        """Run punchline mini-prompt (Haiku). Result feeds into score_main."""
        fact      = state["extracted_fact"] or {}
        core_fact = fact.get("core_fact", fact.get("raw_content", ""))

        prompt   = _PUNCHLINE_PROMPT.format(core_fact=core_fact[:800])
        response = self._haiku(prompt)
        punchline = _parse_kv(response)

        return {**state, "story_score_result": {"punchline": punchline}}

    # -----------------------------------------------------------------------
    # Node: score_main
    # -----------------------------------------------------------------------

    def score_main(self, state: DiaryAgentState) -> DiaryAgentState:
        """Run main story_score prompt (Sonnet). Combines all four dimensions."""
        fact      = state["extracted_fact"] or {}
        punchline = (state.get("story_score_result") or {}).get("punchline", {})

        context = (
            f"When: {fact.get('context_when', '?')} | "
            f"Where: {fact.get('context_where', '?')} | "
            f"With: {fact.get('context_with', '?')}"
        )
        punchline_summary = (
            f"score: {punchline.get('score', '?')} — {punchline.get('reason', '')}"
        )

        prompt   = _SCORE_MAIN_PROMPT.format(
            core_fact=fact.get("core_fact", "")[:800],
            context=context,
            punchline_summary=punchline_summary,
        )
        response = self._sonnet(prompt)
        scores   = _parse_kv(response)

        # Normalize numeric fields to int
        for field in ("ueberraschung", "anschlussfaehigkeit", "sensorik", "pointe", "gesamt"):
            raw = str(scores.get(field, "0")).split("|")[0].strip()
            try:
                scores[field] = int(raw)
            except ValueError:
                scores[field] = 0

        # Carry punchline potential for elaboration
        scores["punchline_potential"] = punchline.get("potential", "")

        return {**state, "story_score_result": scores}

    # -----------------------------------------------------------------------
    # Node: find_correlations
    # -----------------------------------------------------------------------

    def find_correlations(self, state: DiaryAgentState) -> DiaryAgentState:
        """Tag-overlap filter (cheap) + Sonnet cluster analysis (only if candidates found)."""
        fact         = state["extracted_fact"] or {}
        graph_context = state.get("graph_context", [])
        fact_tags    = {t.strip().lower() for t in fact.get("tags", "").split(",") if t.strip()}

        candidates = [
            p for p in graph_context
            if getattr(p, "page_type", "") == "PersonalFact"
            and len(fact_tags & {t.lower() for t in getattr(p, "tags", [])}) >= TAG_OVERLAP_THRESHOLD
        ]

        if not candidates:
            return {**state, "correlation_result": {"related_facts": [], "concept_suggestion": None}}

        candidates_text = "\n".join(
            f"- {p.title}: {getattr(p, 'summary', '')[:120]}" for p in candidates[:5]
        )
        new_fact_text = f"{fact.get('title', '')}: {fact.get('core_fact', '')[:200]}"

        prompt   = _CORRELATIONS_PROMPT.format(
            new_fact=new_fact_text,
            candidates=candidates_text,
        )
        # Haiku if only 1 candidate, Sonnet for richer cluster analysis
        response = self._sonnet(prompt) if len(candidates) >= 2 else self._haiku(prompt)
        corr     = _parse_kv(response)

        concept_suggestion = None
        if (
            len(candidates) >= CONCEPT_THRESHOLD
            and corr.get("concept_title") not in (None, "null", "", "none")
        ):
            concept_suggestion = {
                "title":         corr.get("concept_title"),
                "summary":       corr.get("concept_summary"),
                "related_facts": [getattr(p, "path", "") for p in candidates],
            }

        return {
            **state,
            "correlation_result": {
                "related_facts":    [getattr(p, "path", "") for p in candidates],
                "verbindung":       corr.get("verbindung", ""),
                "concept_suggestion": concept_suggestion,
            },
        }

    # -----------------------------------------------------------------------
    # Node: elaborate
    # -----------------------------------------------------------------------

    def elaborate(self, state: DiaryAgentState) -> DiaryAgentState:
        """Elaborate the fact into a tellable story (Sonnet)."""
        fact          = state["extracted_fact"] or {}
        scores        = state["story_score_result"] or {}
        graph_context = state.get("graph_context", [])

        context_summary = "\n".join(
            f"- {p.title}: {getattr(p, 'summary', '')[:80]}" for p in graph_context[:5]
        ) or "(Leerer Graph — erste Facts)"

        context = (
            f"When: {fact.get('context_when', '?')} | "
            f"Where: {fact.get('context_where', '?')} | "
            f"With: {fact.get('context_with', '?')}"
        )

        prompt    = _ELABORATE_PROMPT.format(
            graph_context_summary=context_summary,
            title=fact.get("title", ""),
            core_fact=fact.get("core_fact", "")[:800],
            context=context,
            story_score=scores.get("gesamt", 0),
            punchline_potential=scores.get("punchline_potential", ""),
        )
        response   = self._sonnet(prompt)
        elaboration = _parse_kv(response)

        return {**state, "elaboration_result": elaboration}

    # -----------------------------------------------------------------------
    # Node: write_fact
    # -----------------------------------------------------------------------

    def write_fact(self, state: DiaryAgentState) -> DiaryAgentState:
        """Assemble WikiWrite objects from extracted_fact + scores + elaboration."""
        fact        = state["extracted_fact"] or {}
        scores      = state["story_score_result"] or {}
        elaboration = state.get("elaboration_result") or {}
        correlation = state.get("correlation_result") or {}

        title_slug  = _slugify(fact.get("title", "untitled"))
        fact_date   = fact.get("date", date.today().isoformat())
        filename    = f"pf_{fact_date}_{title_slug}.md"
        path        = f"wiki/personal/facts/{filename}"

        score_total = scores.get("gesamt", 0)
        status      = "elaborated" if elaboration else "raw"

        # Build related list
        corr_related = correlation.get("related_facts", [])
        elab_related = [
            r.strip()
            for r in elaboration.get("related", "").splitlines()
            if r.strip() and r.strip().lower() != "none"
        ]
        all_related = list(dict.fromkeys(corr_related + elab_related))  # deduplicated, ordered

        if all_related:
            related_yaml = "\n".join(f"  - {r}" for r in all_related)
            related_field = f"related:\n{related_yaml}"
        else:
            related_field = "related: []"

        sc_when = elaboration.get("social_context_when", "")
        sc_mood = elaboration.get("social_context_mood", "locker")

        score_lines = "\n".join([
            f"- Überraschungsmoment (0–3): {scores.get('ueberraschung', '?')} — {scores.get('ueberraschung_reason', '')}",
            f"- Anschlussfähigkeit (0–3): {scores.get('anschlussfaehigkeit', '?')} — {scores.get('anschlussfaehigkeit_reason', '')}",
            f"- Sensorische Details (0–2): {scores.get('sensorik', '?')} — {scores.get('sensorik_reason', '')}",
            f"- Pointe/Wendung (0–2): {scores.get('pointe', '?')} — {scores.get('pointe_reason', '')}",
            f"- **Gesamt:** {score_total}/10",
        ])

        source_ts  = fact.get("source_event", "")
        source_ref = f"raw/events/{source_ts}_text.json" if source_ts else ""

        narrative_hook = scores.get("narrative_hook", elaboration.get("narrative_hook", ""))
        ausarbeitung   = elaboration.get("ausarbeitung", "[Leer — status: raw]")
        verbindung     = correlation.get("verbindung", "[Noch keine Korrelationen gefunden]")

        content = dedent(f"""\
            ---
            type: PersonalFact
            created: {date.today().isoformat()}
            updated: {date.today().isoformat()}
            status: {status}
            sensitivity: {fact.get('sensitivity', 'public')}
            story_score: {score_total}
            tags: [{fact.get('tags', '')}]
            sources: [{source_ref}]
            {related_field}
            social_context:
              when: "{sc_when}"
              audience: "gemischt"
              mood: "{sc_mood}"
            practice_log: []
            ---

            # {fact.get('title', 'Untitled')}

            ## Kern-Fakt
            {fact.get('core_fact', '')}

            ## Kontext
            - **Wann:** {fact.get('context_when', '')}
            - **Wo:** {fact.get('context_where', '')}
            - **Mit wem:** {fact.get('context_with', '')}

            ## Narrative Hook
            {narrative_hook}

            ## Score-Begründung
            {score_lines}

            ## Social Context
            {sc_when or '[Noch nicht befüllt — wird beim Elaboration-Schritt gesetzt]'}

            ## Korrelationen im Graph
            {verbindung}

            ## Ausarbeitung
            {ausarbeitung}

            ## Übungsnotizen
            """)

        wiki_writes: list[WikiWrite] = [
            WikiWrite(path=path, content=content, operation="create"),
        ]

        # Telegram notification if concept page suggestion exists
        telegram_messages = list(state.get("telegram_messages", []))
        concept = correlation.get("concept_suggestion")
        if concept and concept.get("title"):
            telegram_messages.append(
                f"🔗 Muster erkannt\n\n"
                f"Vorschlag: \"{concept['title']}\"\n"
                f"{concept.get('summary', '')}\n\n"
                f"(Concept-Seite noch nicht implementiert — kommt in einer späteren Session)"
            )

        return {**state, "wiki_writes": wiki_writes, "telegram_messages": telegram_messages}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_kv(text: str) -> dict:
    """Parse 'key: value' and 'key: value | sub_key: sub_value' lines from LLM output."""
    result: dict = {}
    for line in text.splitlines():
        if ": " not in line:
            continue
        k, _, v = line.partition(": ")
        k = k.strip().lower().replace(" ", "_").replace("-", "_")
        v = v.strip()
        if " | " in v and k not in result:
            parts = v.split(" | ")
            result[k] = parts[0].strip()
            for part in parts[1:]:
                if ": " in part:
                    pk, _, pv = part.partition(": ")
                    result[f"{k}_{pk.strip()}"] = pv.strip()
        elif k not in result:
            result[k] = v
    return result


def _slugify(text: str) -> str:
    """Convert text to lowercase kebab-case suitable for filenames."""
    text = text.lower().strip()
    text = re.sub(
        r"[äöüß]",
        lambda m: {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}[m.group()],
        text,
    )
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:50]


def _should_elaborate(state: DiaryAgentState) -> str:
    score = (state["story_score_result"] or {}).get("gesamt", 0)
    return "elaborate" if score >= 6 else "write_fact"


def _build_workflow(agent: DiaryAgent) -> StateGraph:
    wf = StateGraph(DiaryAgentState)
    wf.add_node("extract_fact",      agent.extract_fact)
    wf.add_node("score_punchline",   agent.score_punchline)
    wf.add_node("score_main",        agent.score_main)
    wf.add_node("find_correlations", agent.find_correlations)
    wf.add_node("elaborate",         agent.elaborate)
    wf.add_node("write_fact",        agent.write_fact)

    wf.set_entry_point("extract_fact")
    wf.add_edge("extract_fact",    "score_punchline")
    wf.add_edge("score_punchline", "score_main")
    wf.add_edge("score_main",      "find_correlations")
    wf.add_conditional_edges(
        "find_correlations",
        _should_elaborate,
        {"elaborate": "elaborate", "write_fact": "write_fact"},
    )
    wf.add_edge("elaborate",  "write_fact")
    wf.add_edge("write_fact", END)
    return wf.compile()
