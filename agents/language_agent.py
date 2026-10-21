"""language_agent.py — Language Module.

Creates VocabEntries, LanguageBridges, CulturalEntries. Manages Anki sync.
Full specification: doc/COMP_LANGUAGE.md
"""

from __future__ import annotations

import re
from datetime import date
from textwrap import dedent
from typing import TypedDict

from langgraph.graph import END, StateGraph

from agents.base_agent import BaseAgent
from agents.frontmatter import render as render_frontmatter
from agents.graph_writer import WikiWrite


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_DETECT_WORDS_PROMPT = """\
Identify all non-German words in the following text.
The user's native language is German. They are learning Spanish and English.

Text:
---
{content}
---

User hint: {user_hint}

List each foreign word with its likely language.
Only include words that appear directly in the text — no guessing.
Ignore proper nouns (names, cities) unless they are vocabulary items.

Respond in this exact format (one word per line):
word: [word] | lang: [es/en/fr/...]

If no foreign words are found, respond with: NONE
"""

_CREATE_VOCAB_PROMPT = """\
Create a complete VocabEntry for a personal language learning dictionary.

Word: {word}
Language: {language}
User context: {user_context}
Graph context (existing related pages):
{graph_context}

User's known languages: German (native), Spanish (learning), English (learning)

Tasks:
1. Provide translations into all known languages.
2. Write 3 example sentences at A-level, B-level, C-level or idiomatic.
3. Write a mnemonic that connects to German or the user's known experiences.
   If graph_context contains a PersonalFact with this word: use that moment as the mnemonic.
4. Identify cross-language bridges:
   - cognate (similar word, similar meaning in another language)?
   - faux-ami (similar word, different meaning)?
   - concept-gap (concept exists in target language, no German equivalent)?
   - structural-parallel (similar grammatical structure)?
5. Determine CEFR difficulty level (A1–C2).

Respond in this exact format:
translations_de: [German translation]
translations_en: [English translation]
grammar_type: [Nomen | Verb | Adjektiv | Adverb | Phrase | ...]
grammar_gender: [el | la | — ]
grammar_note: [short conjugation or gender note]
example_a: [A-level example sentence]
example_b: [B-level example sentence]
example_c: [C-level example sentence or idiomatic usage]
mnemonic: [mnemonic, ideally tied to user context]
bridge_lang: [de/en/...] | bridge_type: [cognate/faux-ami/concept-gap/structural-parallel] | bridge_note: [1 sentence]
difficulty: [A1/A2/B1/B2/C1/C2]
tags: [comma-separated tags]

If no bridge found, write: bridge_lang: none
"""

_FIND_BRIDGES_PROMPT = """\
Analyze a linguistic connection between two words/concepts.

Word A: {word_a} ({language_a}) — meaning: {meaning_a}
Word B: {word_b} ({language_b}) — meaning: {meaning_b}
Suspected bridge type: {bridge_type}

Tasks:
1. Confirm or correct the bridge type.
2. Formulate the learning insight in 1-2 sentences.
3. Give a concrete contrast example.

Respond:
bridge_type: [cognate | faux-ami | concept-gap | structural-parallel]
confirmed: [true | false]
insight: [1-2 sentences — the key takeaway for the learner]
example_a: [{language_a}: sentence]
example_b: [{language_b}: sentence]
example_comment: [what makes the difference/similarity clear?]
"""

_CREATE_CULTURAL_PROMPT = """\
Create a CulturalEntry for a personal knowledge system.

Entity: {name}
Type: {entity_type}
Reason for creation: {trigger_context}
Graph context: {graph_context}
User interests: KI/Tech, Gesundheit, Musik, Fotografie, Esport (CS2), Krypto, Spanisch lernen

Tasks:
1. Write a concise summary (3-5 sentences).
2. Explain why this entity is relevant for THIS user — based on graph context and interests.
3. Identify 2-3 cross-cultural links if sensible.
4. Suggest 3-5 tags.

Respond:
summary: [3-5 sentences]
why_relevant: [1-2 sentences, personalized]
cross_link_1: [wiki-ref] | cross_note_1: [1 sentence]
cross_link_2: [wiki-ref] | cross_note_2: [1 sentence]
tags: [comma-separated tags]
"""


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

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
            "agent_outputs":     {"language": result},
            "wiki_writes":       result["wiki_writes"],
            "telegram_messages": result["telegram_messages"],
        }

    # -----------------------------------------------------------------------
    # Node: detect_words
    # -----------------------------------------------------------------------

    def detect_words(self, state: LanguageAgentState) -> LanguageAgentState:
        """Detect foreign-language words in input (Haiku). See COMP_LANGUAGE.md §2.1."""
        raw_event = state["raw_event"]
        content = raw_event.get("content", "")
        user_hint = raw_event.get("user_hint", "")

        if not content.strip():
            return {**state, "detected_words": []}

        prompt = _DETECT_WORDS_PROMPT.format(
            content=content[:1000],
            user_hint=user_hint or "none",
        )
        response = self._haiku(prompt)

        words: list[str] = []
        if response.strip().upper() != "NONE":
            for line in response.splitlines():
                kv = _parse_kv_simple(line)
                word = kv.get("word", "").strip()
                lang = kv.get("lang", "").strip()
                if word and lang and lang != "de":
                    words.append(f"{word}|{lang}")

        return {**state, "detected_words": words}

    # -----------------------------------------------------------------------
    # Node: create_vocab
    # -----------------------------------------------------------------------

    def create_vocab(self, state: LanguageAgentState) -> LanguageAgentState:
        """Create VocabEntry for each detected word (Sonnet). See COMP_LANGUAGE.md §2.3."""
        graph_context = state.get("graph_context", [])
        raw_event = state["raw_event"]
        user_context = raw_event.get("content", "")[:300]

        context_summary = "\n".join(
            f"- {getattr(p, 'title', '?')}: {getattr(p, 'summary', '')[:80]}"
            for p in graph_context[:5]
        ) or "(leerer Graph)"

        vocab_results: list[dict] = []
        for word_lang in state["detected_words"]:
            if "|" not in word_lang:
                continue
            word, lang = word_lang.split("|", 1)

            prompt = _CREATE_VOCAB_PROMPT.format(
                word=word,
                language=lang,
                user_context=user_context,
                graph_context=context_summary,
            )
            response = self._sonnet(prompt)
            parsed = _parse_kv_multivalue(response)
            parsed["word"] = word
            parsed["language"] = lang
            vocab_results.append(parsed)

        return {**state, "vocab_results": vocab_results}

    # -----------------------------------------------------------------------
    # Node: find_bridges
    # -----------------------------------------------------------------------

    def find_bridges(self, state: LanguageAgentState) -> LanguageAgentState:
        """Identify LanguageBridges from vocab results (Sonnet). See COMP_LANGUAGE.md §3."""
        bridge_results: list[dict] = []

        for vocab in state["vocab_results"]:
            bridge_lang = vocab.get("bridge_lang", "none")
            if not bridge_lang or bridge_lang.lower() == "none":
                continue

            bridge_type = vocab.get("bridge_type", "cognate")
            word = vocab.get("word", "")
            lang = vocab.get("language", "")
            meaning_a = vocab.get("translations_de", "")
            meaning_b = vocab.get("translations_en", meaning_a)

            if bridge_lang == "de":
                word_b = vocab.get("translations_de", "")
                meaning_b = meaning_a
                meaning_a = word
            else:
                word_b = vocab.get(f"translations_{bridge_lang}", "")

            prompt = _FIND_BRIDGES_PROMPT.format(
                word_a=word,
                language_a=lang,
                meaning_a=meaning_a,
                word_b=word_b or word,
                language_b=bridge_lang,
                meaning_b=meaning_b,
                bridge_type=bridge_type,
            )
            response = self._sonnet(prompt)
            parsed = _parse_kv_multivalue(response)
            if parsed.get("confirmed", "").lower() == "true":
                parsed["source_word"] = word
                parsed["source_lang"] = lang
                parsed["target_lang"] = bridge_lang
                bridge_results.append(parsed)

        return {**state, "bridge_results": bridge_results}

    # -----------------------------------------------------------------------
    # Node: create_cultural
    # -----------------------------------------------------------------------

    def create_cultural(self, state: LanguageAgentState) -> LanguageAgentState:
        """Create CulturalEntry if triggered (Sonnet). See COMP_LANGUAGE.md §4."""
        raw_event = state["raw_event"]
        content = raw_event.get("content", "")
        hint = raw_event.get("user_hint", "")
        graph_context = state.get("graph_context", [])

        # Extract entity name from hint or content
        entity_name = _extract_cultural_entity(hint + " " + content)
        if not entity_name:
            return {**state, "cultural_entry_result": None}

        entity_type = _guess_entity_type(entity_name, content)
        context_summary = "\n".join(
            f"- {getattr(p, 'title', '?')}: {getattr(p, 'summary', '')[:80]}"
            for p in graph_context[:4]
        ) or "(leerer Graph)"

        prompt = _CREATE_CULTURAL_PROMPT.format(
            name=entity_name,
            entity_type=entity_type,
            trigger_context=content[:400],
            graph_context=context_summary,
        )
        response = self._sonnet(prompt)
        parsed = _parse_kv_multivalue(response)
        parsed["name"] = entity_name
        parsed["entity_type"] = entity_type

        return {**state, "cultural_entry_result": parsed}

    # -----------------------------------------------------------------------
    # Node: schedule_anki
    # -----------------------------------------------------------------------

    def schedule_anki(self, state: LanguageAgentState) -> LanguageAgentState:
        """Queue Anki export tasks for new elaborated VocabEntries. See COMP_LANGUAGE.md §5."""
        anki_tasks: list[str] = []
        for vocab in state["vocab_results"]:
            word = vocab.get("word", "")
            lang = vocab.get("language", "")
            if word and lang:
                slug = _slugify(word)
                path = f"wiki/language/vocab/v_{lang}_{slug}.md"
                anki_tasks.append(path)
        return {**state, "anki_tasks": anki_tasks}

    # -----------------------------------------------------------------------
    # Node: update_profile
    # -----------------------------------------------------------------------

    def update_profile(self, state: LanguageAgentState) -> LanguageAgentState:
        """Increment language profile counters. See COMP_LANGUAGE.md §1.3."""
        vocab_count = len(state["vocab_results"])
        bridge_count = len(state["bridge_results"])
        cultural_count = 1 if state.get("cultural_entry_result") else 0

        if vocab_count == 0 and bridge_count == 0 and cultural_count == 0:
            return state

        profile_path = self.wiki_root / "wiki/language/user_language_profile.md"
        if not profile_path.exists():
            return state

        text = profile_path.read_text(encoding="utf-8")

        def _increment(field: str, delta: int, src: str) -> str:
            m = re.search(rf"^({re.escape(field)}:\s*)(\d+)", src, re.MULTILINE)
            if m:
                new_val = int(m.group(2)) + delta
                return src[:m.start()] + f"{m.group(1)}{new_val}" + src[m.end():]
            return src

        if vocab_count:
            text = _increment("total_vocab_entries", vocab_count, text)
        if bridge_count:
            text = _increment("bridges_created", bridge_count, text)
        if cultural_count:
            text = _increment("cultural_entries", cultural_count, text)

        # Update last activity for languages that got new vocab
        langs_updated = {v.get("language", "") for v in state["vocab_results"] if v.get("language")}
        today = date.today().isoformat()
        for lang in langs_updated:
            text = re.sub(
                rf"(\| {lang.title()}\s*\| {lang}\s*\| \S+\s*\| \d+\s*\|)\s*[^\n]*",
                lambda m, t=today: m.group(0).rsplit("|", 1)[0] + f"| {t}",
                text,
            )

        profile_path.write_text(text, encoding="utf-8")
        return state

    # -----------------------------------------------------------------------
    # Node: write_entries
    # -----------------------------------------------------------------------

    def write_entries(self, state: LanguageAgentState) -> LanguageAgentState:
        """Assemble WikiWrite objects from all results."""
        wiki_writes: list[WikiWrite] = list(state.get("wiki_writes", []))
        telegram_messages: list[str] = list(state.get("telegram_messages", []))
        today = date.today().isoformat()

        # VocabEntries
        for vocab in state["vocab_results"]:
            word = vocab.get("word", "")
            lang = vocab.get("language", "")
            if not word or not lang:
                continue

            slug = _slugify(word)
            path = f"wiki/language/vocab/v_{lang}_{slug}.md"

            bridge_lang = vocab.get("bridge_lang", "none")
            if bridge_lang and bridge_lang.lower() != "none":
                bridges: list[dict] = [{
                    "lang": bridge_lang,
                    "type": vocab.get("bridge_type", "?"),
                    "note": vocab.get("bridge_note", ""),
                }]
            else:
                bridges = []

            tags_raw = vocab.get("tags", "")
            if isinstance(tags_raw, str):
                tags_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
            else:
                tags_list = list(tags_raw)

            frontmatter = {
                "type": "VocabEntry",
                "created": today,
                "updated": today,
                "status": "elaborated",
                "word": word,
                "language": lang,
                "difficulty": vocab.get("difficulty", "?"),
                "anki_id": None,
                "tags": tags_list,
                "sources": [],
                "related": [],
                "cross_language_bridges": bridges,
                "usage_stats": {
                    "impuls_count": 0,
                    "last_impuls": None,
                    "codemix_used": 0,
                },
            }

            examples = "\n".join([
                f"- {vocab.get('example_a', '')}",
                f"- {vocab.get('example_b', '')}",
                f"- {vocab.get('example_c', '')}",
            ])

            body = (
                f"# {word}\n\n"
                f"## Übersetzungen\n"
                f"- **DE:** {vocab.get('translations_de', '')}\n"
                f"- **EN:** {vocab.get('translations_en', '')}\n\n"
                f"## Grammatik\n"
                f"- **Typ:** {vocab.get('grammar_type', '')}\n"
                f"- **Genus:** {vocab.get('grammar_gender', '—')}\n"
                f"- **Hinweis:** {vocab.get('grammar_note', '')}\n\n"
                f"## Beispielsätze\n"
                f"{examples}\n\n"
                f"## Eselsbrücke\n"
                f"{vocab.get('mnemonic', '')}\n"
            )

            content = render_frontmatter(frontmatter, body)
            wiki_writes.append(WikiWrite(path=path, content=content, operation="create"))

        # LanguageBridges
        for bridge in state["bridge_results"]:
            src_word = bridge.get("source_word", "")
            src_lang = bridge.get("source_lang", "")
            tgt_lang = bridge.get("target_lang", "")
            b_type = bridge.get("bridge_type", "cognate")
            slug = _slugify(f"{src_word}")
            path = f"wiki/language/bridges/lb_{src_lang}-{tgt_lang}_{slug}.md"

            content = dedent(f"""\
                ---
                type: LanguageBridge
                created: {today}
                updated: {today}
                status: elaborated
                bridge_type: {b_type}
                languages: [{src_lang}, {tgt_lang}]
                tags: [{src_lang}, {tgt_lang}, {b_type}]
                sources: []
                related: []
                ---

                # Bridge: {src_word} ({src_lang} ↔ {tgt_lang})

                ## Typ
                {b_type}

                ## Kernaussage
                {bridge.get('insight', '')}

                ## Kontrastbeispiel
                - **{src_lang}:** {bridge.get('example_a', '')}
                - **{tgt_lang}:** {bridge.get('example_b', '')}
                - *{bridge.get('example_comment', '')}*
                """)

            wiki_writes.append(WikiWrite(path=path, content=content, operation="create"))

        # CulturalEntry
        cultural = state.get("cultural_entry_result")
        if cultural and cultural.get("name"):
            name = cultural["name"]
            e_type = cultural.get("entity_type", "cultural-concept")
            slug = _slugify(name)
            lang_code = _detect_cultural_lang(state)
            path = f"wiki/language/culture/c_{lang_code}_{slug}.md"

            cross_links = ""
            for i in (1, 2):
                link = cultural.get(f"cross_link_{i}", "")
                note = cultural.get(f"cross_note_{i}", "")
                if link and link.lower() not in ("none", "null", ""):
                    cross_links += f"  - entry: [[{link}]]\n    note: \"{note}\"\n"
            if not cross_links:
                cross_links = "  []"

            content = dedent(f"""\
                ---
                type: CulturalEntry
                created: {today}
                updated: {today}
                status: elaborated
                name: "{name}"
                entry_type: {e_type}
                language_context: [{lang_code}]
                tags: [{cultural.get('tags', '')}]
                sources: []
                related: []
                cross_cultural_links:
                {cross_links}
                ---

                # {name}

                ## Zusammenfassung
                {cultural.get('summary', '')}

                ## Relevanz
                {cultural.get('why_relevant', '')}
                """)

            wiki_writes.append(WikiWrite(path=path, content=content, operation="create"))

            telegram_messages.append(
                f"🌍 CulturalEntry erstellt: {name}\n"
                f"Typ: {e_type} | Tags: {cultural.get('tags', '')}"
            )

        if wiki_writes:
            items = ", ".join(
                w["path"].split("/")[-1] for w in wiki_writes
            )
            telegram_messages.append(f"📚 Language: {len(wiki_writes)} Seiten erstellt\n{items}")

        return {**state, "wiki_writes": wiki_writes, "telegram_messages": telegram_messages}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_kv_simple(line: str) -> dict:
    """Parse 'key: value | key2: value2' from a single line."""
    result: dict = {}
    for part in line.split(" | "):
        if ": " in part:
            k, _, v = part.partition(": ")
            result[k.strip().lower()] = v.strip()
    return result


def _parse_kv_multivalue(text: str) -> dict:
    """Parse multi-line 'key: value' and 'key: val | sub_key: sub_val' LLM output."""
    result: dict = {}
    for line in text.splitlines():
        if ": " not in line:
            continue
        k, _, v = line.partition(": ")
        k = k.strip().lower().replace(" ", "_").replace("-", "_")
        v = v.strip()
        if " | " in v:
            parts = v.split(" | ")
            result[k] = parts[0].strip()
            for part in parts[1:]:
                if ": " in part:
                    pk, _, pv = part.partition(": ")
                    result[f"{k}_{pk.strip().lower()}"] = pv.strip()
        elif k not in result:
            result[k] = v
    return result


def _slugify(text: str) -> str:
    """Convert text to lowercase kebab-case for filenames."""
    text = text.lower().strip()
    text = re.sub(
        r"[äöüß]",
        lambda m: {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}[m.group()],
        text,
    )
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:50]


_CULTURAL_TRIGGERS = {
    "flamenco", "madrid", "barcelona", "sevilla", "valencia", "mexico",
    "argentina", "colombia", "cuba", "tango", "salsa", "mariachi",
    "pablo picasso", "frida kahlo", "gabriel garcia marquez",
    "día de los muertos", "semana santa",
}


def _extract_cultural_entity(text: str) -> str:
    """Extract a likely cultural entity name from text. Heuristic, no LLM cost."""
    text_lower = text.lower()
    for trigger in _CULTURAL_TRIGGERS:
        if trigger in text_lower:
            return trigger.title()
    return ""


def _guess_entity_type(name: str, context: str) -> str:
    """Heuristic entity type classification."""
    context_lower = context.lower()
    cities = {"madrid", "barcelona", "sevilla", "valencia", "mexico", "buenos aires", "havana"}
    if name.lower() in cities:
        return "place"
    if any(w in context_lower for w in ["künstler", "autor", "musiker", "maler", "sänger", "artist"]):
        return "person"
    if any(w in context_lower for w in ["festival", "event", "feier", "kurs"]):
        return "event"
    return "cultural-concept"


def _detect_cultural_lang(state: LanguageAgentState) -> str:
    """Infer language code for CulturalEntry from detected words or language profile."""
    # 1. Use the most common language from detected_words
    lang_counts: dict[str, int] = {}
    for word_lang in state.get("detected_words", []):
        if "|" in word_lang:
            _, lang = word_lang.split("|", 1)
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    if lang_counts:
        return max(lang_counts, key=lambda k: lang_counts[k])

    # 2. Fall back to primary_learning_language from user_language_profile
    profile = state.get("user_language_profile", {})
    primary = profile.get("primary_learning_language", "")
    if primary:
        # Accept both "es" and "Spanish" forms
        mapping = {"spanish": "es", "english": "en", "french": "fr", "german": "de"}
        return mapping.get(primary.lower(), primary.lower()[:2])

    return "es"  # last resort default


def _has_cultural_trigger(state: LanguageAgentState) -> str:
    hint = state["raw_event"].get("user_hint", "").lower()
    content = state["raw_event"].get("content", "").lower()
    combined = hint + " " + content
    triggers = list(_CULTURAL_TRIGGERS) + ["kultur", "person", "ort"]
    return "create_cultural" if any(t in combined for t in triggers) else "schedule_anki"


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
    wf.add_conditional_edges(
        "find_bridges",
        _has_cultural_trigger,
        {"create_cultural": "create_cultural", "schedule_anki": "schedule_anki"},
    )
    wf.add_edge("create_cultural", "schedule_anki")
    wf.add_edge("schedule_anki",   "update_profile")
    wf.add_edge("update_profile",  "write_entries")
    wf.add_edge("write_entries",   END)
    return wf.compile()
