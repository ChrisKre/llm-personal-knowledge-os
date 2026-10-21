# Roadmap

**Where this is going:** from a knowledge graph that *stores* what you learn to a learning engine that *teaches it back to you*. Personal, connected, and spaced over time.

Today the system captures input, compiles it into a cross-linked Markdown graph (language, culture, personal stories) and exports vocabulary to Anki. The milestones below add the practice layer on top of that graph, open it up to new knowledge domains, and keep the foundation solid.

Sizes are rough estimates of focused development time. IDs in brackets (`BL-xx`) refer to the German backlog in [workshop/backlog.md](workshop/backlog.md).

| Milestone | Theme | Size |
|---|---|---|
| [M1](#m1-practice-core) | Practice core: exercises, Telegram quizzes, spaced repetition | ~30 h |
| [M2](#m2-stories-and-connections) | Story retelling and cross-domain connections | ~25 h |
| [M3](#m3-extensible-domains) | Plugin domains, facts & topics from sources | ~30 h |
| [Foundation](#foundation-ongoing) | Cleanup, i18n, retrieval, tests | ~20 h |
| | **Total** | **~105 h** |

---

## M1: Practice core

*Goal: the graph starts asking questions. Every elaborated page can produce exercises, and a scheduler decides what to practise when.*

| Item | Done when | Size |
|---|---|---|
| **Exercise model.** A common `Exercise` structure (type, prompt, answer, source pages, domain) plus a per-user review state (due date, stability, last result). Stored in the vault so it stays plain, inspectable data. | Schema documented in `doc/SCHEMA.md`; round-trip tests | 4 h |
| **Generator interface + language generators.** `ExerciseGenerator` protocol; first generators for VocabEntry (recall card, reverse card, cloze from the page's own example sentences) and LanguageBridge ("why do these words look alike?"). Deterministic where possible, LLM only where it adds value. | Generators produce valid exercises for every page in `sample_vault/`; snapshot tests | 6 h |
| **Card render module** [BL-05]. Shared rendering for exercises (`RenderDict` contract), so Anki and Telegram show the same content; `export_anki.py` becomes a thin wrapper and exports all exercise types. | Existing Anki tests pass; new exercise types appear in the `.apkg` | 6 h |
| **Spaced repetition scheduler.** FSRS-based scheduling of review states; picks the next due exercises across domains. | Unit tests for scheduling and due-queue ordering | 5 h |
| **`/practice` in Telegram.** A short session of due exercises with inline-keyboard answers and self-rating (again / hard / good / easy), via `ConversationHandler`. Optional daily nudge through the job queue. | A full session works end to end against `sample_vault/`; handler tests with a mocked update | 6 h |
| **Mastery back into the graph.** Review results update a per-page mastery value in frontmatter, visible in Obsidian and usable by generators. Anki export tags pages whose mnemonic needs a refresh [BL-06]. | Mastery updates covered by tests; documented in the schema | 3 h |

## M2: Stories and connections

*Goal: practise speaking about your own life, and learn through the links between topics, not just the topics.*

| Item | Done when | Size |
|---|---|---|
| **Story Lab.** For `story-ready` PersonalFacts, the bot asks you to retell the story in your target language, optionally with required words. The voice answer is transcribed locally, compared with the fact and its vocabulary, and answered with focused feedback. Each attempt is stored in the fact's `practice_log`. | Retelling flow works by voice and text; `practice_log` entries written through `graph_writer` | 8 h |
| **Story progress over time.** Compare attempts on the same story ("three months ago vs. today") and surface new vocabulary you used. | Comparison message generated from `practice_log`; tests with fixtures | 3 h |
| **Connection finder.** A periodic pass that proposes new links across domains (a vocab word ↔ a cultural entry ↔ a personal story) and writes them as reviewed suggestions, not silent edits. | Suggestions created for `sample_vault/`; accept/reject from Telegram | 6 h |
| **Connection questions.** Generator that turns links into questions: "What connects *socarrat* to the smoke alarm story?", "Which cultural entry explains this word?" | Generator + tests; included in `/practice` | 4 h |
| **Draft → approve in Telegram.** Inline approve/reject for pending graph changes; the git helpers already exist in `graph_writer` but have no caller yet. | Approve/reject works on a test vault; branch name detected, not hardcoded | 4 h |

## M3: Extensible domains

*Goal: languages are the first domain, not the only one. Science, history, culture and your own topics plug into the same capture → graph → practice loop.*

| Item | Done when | Size |
|---|---|---|
| **Domain plugin interface.** A registry where a domain declares its page types, agent, schema and exercise generators. Diary and language become the first two plugins without behaviour changes. | Existing tests pass unchanged; a minimal example domain in `doc/` | 8 h |
| **Configurable language pair.** Primary and target languages from config / `user_language_profile.md` instead of German → Spanish assumptions in prompts. | Pipeline works for an English → Italian test profile | 5 h |
| **Facts & topics domain from sources** [BL-17]. Batch processing of saved web clippings (stage 0, the inventory, exists): classification, claim extraction with mandatory evidence quotes, human-confirmed topic plan, TopicPages with sourced claims. | Pilot topics generated from sample sources; every claim has an evidence span | 12 h |
| **Fact questions grounded in sources.** Generator for TopicPage claims ("true or false, and why?"), always showing the source quote in the answer. | Generator + tests; included in `/practice` | 3 h |
| **Continuous source ingestion** [BL-19]. New links you send are merged into existing TopicPages instead of piling up. | `/ingest` command and a daily scan | 4 h |

## Foundation (ongoing)

| Item | Size |
|---|---|
| **English UI + i18n.** Bot replies, bootstrap questions and error messages move to a message catalogue with a configurable language. | 4 h |
| **SQLite FTS5 build script** [BL-09], so retrieval scales beyond `index.md`. | 4 h |
| **Lint agent scheduling and auto-fixes** [BL-07]: daily run via the job queue, backlink symmetry, index sync, slug dedup, all through the human-owned guard. | 6 h |
| **End-to-end tests for the bot handlers** with mocked Telegram updates. | 4 h |
| Small fixes: draft branch name hardcoded as `master`; `init_wiki` creates a `scripts/` folder in the vault; build output (`out/`) should live in the vault; ignore runtime files in `sample_vault/`; unused imports + a pyflakes step in the test run. | 2 h |

---

**Not planned:** training or fine-tuning machine-learning models. The project uses hosted or local LLMs as they are; the knowledge graph and practice data serve the user's own learning only.

Ideas without a commitment are collected (in German) in [doc/CHANCEN.md](doc/CHANCEN.md).
