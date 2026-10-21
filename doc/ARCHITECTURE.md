# ARCHITECTURE.md: System architecture of llm-personal-knowledge-os
> Version: 0.2 (English edition, 2026-10) | Status: DRAFT | German original: [de/ARCHITECTURE.md](de/ARCHITECTURE.md)
>
> This document describes the **target design**. Where the current code differs, a *Status* note says so.

---

## 1. Overview

The system has **two separate "graphs"**, and the distinction matters:

| Term | What it is | Who writes it | Where it lives |
|---|---|---|---|
| **Knowledge graph** | The Markdown wiki: the user's persistent memory | LLM agents | `wiki/` in the vault (file system) |
| **Agent graph** | The LangGraph state machine: orchestration | Python code | RAM (per run) |

**The knowledge graph is the system's only persistent state.** The agent graph is ephemeral: it starts for one task and ends with it. Everything that matters ends up in the knowledge graph.

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER CONTEXT                            │
│  Telegram · file drop into raw/ · (more input channels)         │
│  Input types: text · URL · image · PDF · voice · YouTube        │
│  Optional: context hint ("good for vocab", #story, ...)         │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         EXTRACTOR                               │
│  Format detection → type-specific extraction                    │
│  URL→BeautifulSoup · PDF→pdfplumber · image→Claude Vision       │
│  voice→faster-whisper · YouTube→youtube-transcript-api          │
│  Result: normalized text (same schema whatever came in)         │
│  Stores: original → raw/sources|assets/ (permanent)             │
└────────────────────────┬────────────────────────────────────────┘
                         │ ExtractedContent (JSON)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        raw/events/                              │
│                 [IMMUTABLE, append only]                        │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              SUPERVISOR, stage 1: classification                │
│  Reads: user_profile.md (compressed user signature)             │
│  Decides: intent? which agent? which model?                     │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GRAPH CONTEXT MATCH                          │
│  Request → extract key terms                                    │
│  → search index.md / SQLite                                     │
│  → load the top-N relevant wiki pages                           │
│  Result: graph_context (relevant pages as context)              │
└────────────────────────┬────────────────────────────────────────┘
                         │ graph_context in state
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 SUPERVISOR, stage 2: routing                    │
│  Hands task + graph_context to the agents                       │
└──────┬──────────────┬──────────────┬──────────────┬────────────┘
       ▼              ▼              ▼              ▼
  [Ingestion]    [Language]      [Diary]         [Lint]
   (no GC)      (GC: related    (GC: similar    (no GC)
                 vocab,          facts, topics,
                 bridges)        patterns)
       └──────────────┴──────────────┴──────────────┘
                         │ WikiWrite objects
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│             SUPERVISOR, stage 3: review and approval            │
│  Checks agent output against user_profile + graph_context       │
│  Approves the write or sends it back for revision               │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      KNOWLEDGE GRAPH                            │
│               wiki/ (Markdown files)                            │
│          index.md · log.md · user_profile.md                    │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OBSIDIAN                                 │
│                 [read-only for the user]                        │
└─────────────────────────────────────────────────────────────────┘
```

*Status:* "Ingestion" is implemented as `Supervisor.classify`, not as a separate agent. The lint agent exists (`agents/lint_agent.py`) but is not yet a node in the pipeline (see [ROADMAP](../ROADMAP.md)).

---

## 2. The knowledge graph

### 2.1 What the graph is

The knowledge graph is **not a database schema** and **not an index**. It is a compiled, interlinked set of Markdown files that represents the user's knowledge and personality.

Three properties matter:

1. **Compiled, not retrieved.** Knowledge is processed once and turned into structure. At read time nothing is searched for from scratch; it is read.
2. **Lives in its links.** A VocabEntry page on its own is worth little. Its value comes from links to CulturalEntries, PersonalFacts and Concepts that give it meaning.
3. **Grows and heals.** New input extends the graph. The lint agent detects and repairs structural weaknesses.

### 2.2 Navigation entry points

Three special files help LLMs navigate the graph (examples from the fictional [`sample_vault/`](../sample_vault/)):

**`index.md`**: content-oriented, generated by [`scripts/rebuild_index.py`](../scripts/rebuild_index.py)
```markdown
## PersonalFacts (3)
- [[pf_2026-03-22_first-burnt-socarrat]] — pf_2026-03-22_first-burnt-socarrat (story_score: 7)
- [[pf_2026-04-18_paella-cooking-class]] — pf_2026-04-18_paella-cooking-class (story_score: 6)
...

## VocabEntries — ES (4)
- [[v_es_socarrat]] — socarrat
...
```

**`log.md`**: chronological, append-only
```markdown
## [2026-03-22T21:40:00] ingest | PersonalFact created: pf_2026-03-22_first-burnt-socarrat (story_score 7)
## [2026-03-22T21:40:30] ingest | VocabEntry created: v_es_socarrat
## [2026-04-02T22:05:00] practice | Story practiced: pf_2026-03-22_first-burnt-socarrat
```

**`user_profile.md`**: the user model (the supervisor's core knowledge)
```markdown
# User profile
## Language profile
- Primary language: de
- Active target languages: es, en
- Observed input distribution: 60% de, 30% es, 10% en (last 30 days)

## Interest clusters
- Spanish cooking (high)
- Storytelling (medium)

## PersonalFacts profile
- Average story_score: 6.0
- Unpracticed facts with score > 7: 1
```

### 2.3 Graph operations

There are exactly **three basic operations** on the graph.

#### INGEST
New raw input arrives → graph context is fetched → input is processed → graph is extended.

```
RawEvent read
    → supervisor classifies (language? PersonalFact? both?)       [Haiku]
    → graph context match: key terms → load top-N relevant pages
    → responsible agent processes WITH graph_context              [Sonnet]
    → 1–N new or updated wiki pages
    → index.md update
    → log.md entry
    → user_profile.md updated if needed
```

**The key effect:** no input is judged in isolation, only in the context of everything the graph already knows. A `story_score` is therefore not an absolute number. It measures the value of a new fact *relative to what the graph already contains*.

#### QUERY
The user asks a question → the graph is read → the answer is (optionally) written back.

```
Question read
    → supervisor reads index.md
    → relevant pages are loaded (no embedding lookup, index scan only)
    → Sonnet synthesizes an answer with source links
    → optional: answer saved as a new Concept page
    → log.md entry
```

*Status:* the `query` intent is classified but currently routed straight to review; there is no dedicated query flow yet.

#### LINT
Periodically (daily) → check graph health → repair weaknesses.

```
Lint agent scans all wiki pages
    → checks the symptoms (see SCHEMA.md §8)
    → creates a fix task per symptom
    → applies fixes that can be automated
    → flags the rest for the user
    → log.md entry with the lint report
```

---

## 3. Supervisor

### 3.1 Role

The supervisor is **not an LLM agent in the classic sense**. It is a **routing and review layer**: it orchestrates, evaluates and prioritizes, always with the user as the yardstick.

**Supervisor principle:** *"What would help the user most right now?"*

### 3.2 Supervisor state (per run)

```python
class SupervisorState(TypedDict):
    raw_event: RawEvent           # the current input
    user_profile: dict            # loaded from user_profile.md (compressed, ~3000 tokens)
    graph_index: str              # contents of index.md (navigation aid)
    classified_intent: str        # "vocab" | "personal_fact" | "both" | "query" | "lint"
    graph_context: list[WikiPage] # relevant wiki pages for this specific input
    assigned_agents: list[str]    # which agents are activated
    agent_outputs: dict           # the agents' results
    supervisor_verdict: str       # "accept" | "revise" | "reject"
    wiki_writes: list[WikiWrite]  # pages to write
```

The real definition lives in [`main_workflow.py`](../main_workflow.py) and additionally carries `review_notes` and `telegram_messages`.

**Two levels of user knowledge in the state:**
- `user_profile`: always loaded, compressed, static (~80–120 lines). Contains language distribution, interest clusters and story_score statistics. Answers: *"Who is the user?"*
- `graph_context`: dynamic, per task, specific. Contains the N most relevant wiki pages for the current input. Answers: *"What does the graph already know about this?"*

### 3.3 Supervisor decision logic

```
Input arrives
    │
    ├─ [1. Classification] → what is it? (Haiku, cheap)
    │       ├─ Spanish word/expression → language agent
    │       ├─ personal experience    → diary agent
    │       ├─ both                   → both in parallel
    │       ├─ user question          → query flow
    │       └─ unclear                → supervisor asks back (Telegram reply)
    │
    ├─ [2. Graph context match] → extract key terms → graph_reader.search_wiki()
    │       ├─ PersonalFact: similar facts, topic clusters, places, people
    │       ├─ Vocab: related words, bridges, CulturalEntries
    │       └─ result: graph_context (top 5–10 relevant pages)
    │
    │       Example: input "burnt the rice again, but the socarrat was perfect"
    │       → graph_context contains [[pf_2026-03-22_first-burnt-socarrat]],
    │         [[v_es_socarrat]], [[c_es_paella-valenciana]]
    │       → diary agent recognizes a pattern → story_score goes up
    │
    ├─ [3. Execution] → agents receive task + user_profile + graph_context
    │       → agents run in parallel where possible
    │
    ├─ [4. Review] → supervisor checks agent output against user_profile + graph_context
    │       ├─ is the story_score consistent with similar facts in graph_context?
    │       ├─ were relevant cross-links from graph_context used?
    │       ├─ does the language assignment match the known distribution?
    │       └─ does it contradict existing wiki pages?
    │
    └─ [5. Write] → only after supervisor approval does anything reach the graph
```

### 3.4 The supervisor as the user's advocate

The supervisor combines two sources of knowledge to understand the user:

**`user_profile.md`: the compressed signature** (~80–120 lines, always in context)
- language distribution over the last 30/90 days
- interest clusters (from topic frequency in the graph)
- story_score average and thresholds
- high-score facts not yet elaborated

**`graph_context`: the situational memory** (dynamic, per task)
- the wiki pages that are actually relevant to the current input
- gives the agent real context, not just the user's profile

**Positive feedback loop:** the richer the graph, the better the graph_context hits, the more accurate the reviews, and the better the graph keeps growing.

```
Empty graph      → graph_context empty → score based on user_profile only
Graph, 50 pages  → 3–5 hits            → score informed by patterns
Graph, 200 pages → 8–10 hits           → score precise and well linked
```

---

## 4. Agents

### Communication principle

**Agents never talk to each other directly.** All coordination goes through:
1. **The LangGraph state dict**: ephemeral, per run (the supervisor shares context).
2. **The knowledge graph**: persistent (agents read and write files).

This keeps the system debuggable and extensible: a new agent only has to know the file format, not the other agents.

### 4.1 Ingestion agent

**Purpose:** classifies and normalizes RawEvents. It is the system's entry gateway.

**Input:** a file in `raw/events/`
**Output:** a structured task for the supervisor plus the classified intent

**Responsibilities:**
- detect the input language (ISO 639-1)
- classify the intent (vocab / personal_fact / query / ambiguous)
- if ambiguous: phrase a follow-up question to the user via Telegram
- normalize metadata (timestamp, source)

**Model:** Claude Haiku (classification is cheap).
*Status:* implemented as `Supervisor.classify` in [`agents/supervisor.py`](../agents/supervisor.py).

### 4.2 Language agent

**Purpose:** processes language-related input → creates or updates VocabEntry, CulturalEntry and LanguageBridge pages.

**Input:** classified task from the supervisor plus relevant wiki pages from the index
**Output:** new or updated Markdown pages plus an optional Anki export task

**Responsibilities:**
- create VocabEntries with full context (translations, conjugation, example sentences, mnemonic)
- identify and link cross-language bridges
- create CulturalEntries with country context
- update existing entries when new information arrives
- trigger the Anki export
- update the input distribution in `user_language_profile.md`

**Model:** Haiku for routine VocabEntries, Sonnet for complex CulturalEntries and bridges.
*Status:* Anki export runs as a separate script ([`scripts/export_anki.py`](../scripts/export_anki.py), `.apkg` via genanki), not via AnkiConnect.

### 4.3 Diary agent

**Purpose:** extracts PersonalFacts, rates their story potential and elaborates stories.

**Input:** classified task plus PersonalFacts from the index (for context and correlations)
**Output:** new or updated PersonalFact pages, possibly story pages

**Responsibilities:**
- extract the PersonalFact from the RawEvent
- compute the `story_score` (0–10) from these criteria:
  - surprise (0–3 points)
  - universal relatability: "can anyone relate?" (0–3 points)
  - concrete, sensory details (0–2 points)
  - punchline or twist (0–2 points)
- look for correlations with existing PersonalFacts (topic clusters)
- mark facts with `story_score > 7` for elaboration
- generate practice prompts (Telegram message to the user)

**Model:** Sonnet (nuanced reasoning about narrative quality).
**Privacy:** strictly respect the sensitivity tier from SCHEMA.md §6.3.

### 4.4 Lint agent

**Purpose:** periodic graph health. Finds structural weaknesses and fixes what can be fixed automatically.

**Input:** all wiki pages (in batches) plus index.md and log.md
**Output:** lint report, repaired pages, a queue of decisions for the user

**Responsibilities:**
- check the symptoms from SCHEMA.md §8
- automatic: add missing cross-links, update the index
- not automatic: flag contradictions and ask the user (Telegram)
- generate a monthly "graph health report" for the user

**Model:** Haiku (structure checks are cheap).
**Trigger:** daily at 03:00 (planned; currently not scheduled).

---

## 5. Provider strategy

### 5.1 Two operating modes

The system knows two provider modes, selected automatically from the environment:

| Mode | Condition | "Haiku" role | "Sonnet" role | Purpose |
|---|---|---|---|---|
| **Claude** | `ANTHROPIC_API_KEY` set | Claude Haiku 4.5 | Claude Sonnet 4.6 | Production |
| **Ollama** | no API key | llama3.2 (or similar) | llama3.2 (or similar) | Local tests |

The selection lives only in [`agents/base_agent.py`](../agents/base_agent.py); no agent code changes. Agents keep calling `_haiku()` and `_sonnet()`.

```bash
# .env, production
ANTHROPIC_API_KEY=...

# .env, local tests (no API key needed)
OLLAMA_MODEL=llama3.2                # optional, default: llama3.2
OLLAMA_HOST=http://localhost:11434   # optional
```

### 5.2 Quality note for Ollama mode

Ollama/llama3.2 follows structured output formats (`key: value`) less reliably than Claude. In test mode individual fields may come back empty or malformed. That is a known model limitation, not a bug in the pipeline. For pure mechanics tests (LangGraph routing, WikiWrite objects, graph_reader) it is entirely sufficient.

Quality tests (story_score, VocabEntry content) need the Claude API.

---

## 6. LangGraph implementation

### 6.1 Graph structure (ingestion flow)

As implemented in [`main_workflow.py`](../main_workflow.py) (simplified):

```python
from langgraph.graph import StateGraph, END
from langgraph.constants import Send

wf = StateGraph(SupervisorState)

wf.add_node("classify",            supervisor.classify)
wf.add_node("fetch_graph_context", lambda s: graph_reader.fetch_context(s, wiki_root))
wf.add_node("diary_agent",         diary.process)
wf.add_node("language_agent",      language.process)
wf.add_node("supervisor_review",   supervisor.review)
wf.add_node("write_to_graph",      write_node)     # graph_writer.execute_writes
wf.add_node("update_index",        index_node)     # index.md + log.md

wf.set_entry_point("classify")
wf.add_edge("classify", "fetch_graph_context")     # always query the graph first

def route_after_context(state):
    intent = supervisor.route(state)
    if intent == "both":                            # fan out in parallel
        return [Send("diary_agent", state), Send("language_agent", state)]
    return {"diary_agent": "diary_agent",
            "language_agent": "language_agent"}.get(intent, "supervisor_review")

wf.add_conditional_edges("fetch_graph_context", route_after_context)
wf.add_edge("diary_agent",       "supervisor_review")
wf.add_edge("language_agent",    "supervisor_review")
wf.add_edge("supervisor_review", "write_to_graph")
wf.add_edge("write_to_graph",    "update_index")
wf.add_edge("update_index",      END)
```

A full deterministic rebuild of `index.md` from frontmatter is available as [`scripts/rebuild_index.py`](../scripts/rebuild_index.py).

### 6.2 File write contract

No agent writes files directly. They all write into the state:

```python
class WikiWrite(TypedDict):
    path: str        # relative to the vault root, e.g. "wiki/language/vocab/v_es_socarrat.md"
    content: str     # full Markdown content
    operation: str   # "create" | "update" | "append"
```

The `write_to_graph` node executes all writes after the supervisor's approval. That gives the supervisor the final say and makes rollbacks possible. Before every write, `graph_writer.assert_writable()` refuses paths inside human-owned zones (SCHEMA.md §2).

### 6.3 Graph reader: the index abstraction

`graph_reader` is the only place that knows how the index is implemented. All agents and the supervisor call only this interface:

```python
# agents/graph_reader.py
WIKI_PAGE_THRESHOLD = 30  # from here on: SQLite instead of index.md

def search_wiki(query, page_type=None, language=None, limit=10, wiki_root=VAULT_ROOT):
    if _wiki_size(wiki_root) < WIKI_PAGE_THRESHOLD:
        return _search_index_md(...)   # phase 1: simple
    return _search_sqlite(...)         # phase 2: automatic

def fetch_context(state, wiki_root=VAULT_ROOT):
    """LangGraph node: extract key terms and fill graph_context."""
```

**Phase 1** (< 30 pages): `_search_index_md` parses `index.md` with simple keyword matching.
**Phase 2** (≥ 30 pages): `_search_sqlite` uses SQLite FTS5 over `wiki_index.db`. If the database doesn't exist yet, it falls back to phase 1.
**Switch:** automatic via `_wiki_size()`. The rest of the system doesn't notice.

*Status:* the script that builds `wiki_index.db` is still on the roadmap.

---

## 7. User interaction: Telegram UI levels

Telegram is the primary interaction channel. It offers three native UI levels, from simple to rich.

### Level 1: buttons and polls (immediate, no extra code)

```
Conflict flag from the lint agent:
┌─────────────────────────────────────┐
│  ⚠️ Contradiction found              │
│                                     │
│  Old: "Cooking class was in March"  │
│  New: "Cooking class was in April"  │
│                                     │
│  [Keep March]  [Use April]          │
│  [Keep both: different events]      │
└─────────────────────────────────────┘
→ InlineKeyboardMarkup with callback buttons
→ user taps, supervisor executes the decision
```

```
Vocabulary quiz from the language agent:
┌─────────────────────────────────────┐
│  🇪🇸 What does "socarrat" mean?      │
│                                     │
│  ○ A type of saffron                │
│  ○ Crispy rice at the pan's bottom ✓│
│  ○ The paella pan                   │
│  ○ A fried onion-tomato base        │
└─────────────────────────────────────┘
→ Telegram poll with is_quiz=True
→ native answer reveal with explanation, no code needed
```

### Level 2: conversation flow (medium, ~50 lines)

For practice rounds from the diary module: multi-step conversations by message.

```
Bot:  "Tell me the story of your first burnt socarrat in three sentences."
User: [answers]
Bot:  "Good. Now with a punchline at the end: what was the surprise?"
User: [answers]
Bot:  "story_score: 7/10. The punchline is strong; the opening could be more concrete."
```

→ `ConversationHandler` in python-telegram-bot, a state machine per user session (already used for `/bootstrap`).

### Level 3: Telegram Mini Apps (upgrade path, if needed)

When native Telegram UI isn't enough: Mini Apps are full web apps (HTML/CSS/JS) that open directly in the Telegram chat, with no separate app.

**Possible uses:**
- Obsidian-like graph visualization on the phone
- richer story practice interfaces
- a dashboard for the graph health report

**Effort:** about one week for a simple Mini App. No app store needed.

**Decision:** start with levels 1 and 2. Level 3 only when there is a concrete need.

---

## 8. Graph versioning: draft → production workflow

### The concept

The vault runs on **two git branches**:

```
draft  ← the LLM writes here (all new or updated wiki pages)
master ← the "production" graph: what Obsidian reads, what counts
```

No GitHub needed. A local git repo; a Python script does the merge.

### Flow

```
LLM agent processes input
    → graph_writer writes to the draft branch
    → lint agent checks the new pages on draft
    → supervisor generates a review summary

Supervisor → Telegram message to the user:
┌─────────────────────────────────────────┐
│  📋 3 new pages awaiting approval        │
│                                         │
│  • pf_2026-04-18_paella-cooking-class   │
│  • v_es_socarrat (updated)              │
│  • lb_es-en_azafran (new)               │
│                                         │
│  [Approve ✓]  [Details]  [Reject ✗]     │
└─────────────────────────────────────────┘

[Approve] → git merge draft → master (Python subprocess)
[Details] → bot sends a diff summary of the changes
[Reject]  → reset draft to master, optional user feedback
```

### Implementation

The git helpers `approve_draft()`, `reject_draft()` and `ensure_draft_branch()` live in [`agents/graph_writer.py`](../agents/graph_writer.py).

*Status:* they have no production caller yet; writes currently go directly to the checked-out branch. `reject_draft()` assumes the production branch is called `master` (see [ROADMAP](../ROADMAP.md)).

### When is approval needed?

Not every change needs manual approval; that would be too much overhead:

| Change type | Approval? | Reason |
|---|---|---|
| New VocabEntry | No | Low risk, reversible |
| New CulturalEntry | No | Low risk |
| New PersonalFact (`raw`) | No | Extraction only, not elaborated yet |
| PersonalFact (`story_score > 7`) | Yes | Valuable content; the user should know |
| Contradiction resolution | Yes | A content decision |
| Lint fix (cross-links) | No | Structural, low risk |
| Deletion / archiving | Always | Destructive |

---

## 9. Triggers and scheduling

| Trigger | When | Source | Flow |
|---|---|---|---|
| Telegram message | any time (user) | Telegram (long polling) | Ingestion |
| Daily lint | 03:00 | scheduler | Lint |
| Weekly practice round | Sunday 10:00 | scheduler | Diary (practice) |
| Random language nudge | once a day, random time | scheduler | Language (push) |
| Monthly graph report | 1st of the month | scheduler | Lint (report) |
| Draft review reminder | when draft is older than 24 h | scheduler | Telegram approval |

*Status:* only the Telegram trigger is implemented; the scheduled jobs are planned.

---

## 10. Open architecture questions

- [x] Supervisor granularity: user_profile (~80–120 lines) + graph_context (dynamic), two levels
- [x] Index threshold: graph_reader abstraction with an automatic phase 1 → 2 switch
- [x] User UI: Telegram level 1 (buttons/polls) + level 2 (ConversationHandler); Mini Apps as an upgrade path
- [x] Graph versioning: draft → master branch workflow, manual Telegram approval for critical changes
- [x] Local Ollama: llama3.2 as the default for the `private` tier and as the test fallback
- [ ] Key-term extraction for graph_context: how many terms, which weighting (entities > verbs)?
