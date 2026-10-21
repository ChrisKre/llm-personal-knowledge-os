# Roadmap

Planned work, grouped by horizon. Sizes are rough estimates of focused development time. IDs in brackets (`BL-xx`) refer to the German backlog in [workshop/backlog.md](workshop/backlog.md) and the development logs in `sessions/`.

Total planned effort: **about 80–90 hours** (Now ≈ 25 h, Next ≈ 30 h, Later ≈ 30 h).

## Now: cleanup and wiring what exists

| Item | Size |
|---|---|
| **Fix the draft-branch name.** `graph_writer.reject_draft()` hardcodes `master`, but new vaults default to `main`. Detect the vault's default branch instead, with a test. | 1 h |
| **Separate vault and code directories in `init_wiki`.** `REQUIRED_DIRS` still creates `scripts/` inside the vault. | 0.5 h |
| **Move build output into the vault.** `out/` (Anki `.apkg`, ingest plan and report) contains vault-derived data; write it to `<vault>/out/` instead of the repo. | 1.5 h |
| **Ignore runtime files in `sample_vault/`.** Bot runs against the demo vault leave untracked files in `sample_vault/raw/events` and `raw/assets`. | 0.5 h |
| **Translate user-facing strings to English and add i18n.** Bot replies, bootstrap questions and error messages are German; move them into a message catalogue with a configurable language. | 4 h |
| **Make the language pair configurable.** The language agent and several prompts assume German → Spanish; read primary and target languages from `user_language_profile.md` / config. | 5 h |
| **Lint auto-fixes** [BL-07]: backlink symmetry, index sync and slug dedup, all routed through the human-owned-zone guard, with before/after fixture tests. | 6 h |
| **Lint rules for TopicPages** [BL-18]: healthy "dissent" sections are not contradictions; conflicts with human-owned pages are flagged to the user. | 2–3 h |
| **Schedule the lint agent** (daily job via python-telegram-bot's job queue) and report results to Telegram. | 3 h |
| **Fix pyflakes warnings** (unused imports in `graph_reader`, `lint_agent`, `supervisor`, `extractor`, `test_ingest`) and add a lint step to the test run. | 1 h |

## Next: retrieval and external knowledge

| Item | Size |
|---|---|
| **SQLite FTS5 build script** [BL-09]: build `wiki_index.db` from the vault and test `graph_reader._search_sqlite` against a real database. Today the code falls back to `index.md` when the DB is missing. | 4 h |
| **Batch ingestion of web clippings, stages 1–5** [BL-17]: classification, claim extraction with mandatory evidence spans, a human-confirmed topic cluster plan, deterministic confidence, and atomic writes to a draft branch for review. Builds on the existing stage 0 (`scripts/ingest_clippings.py`). | 17–18 h |
| **Continuous source ingestion** [BL-19]: a `source_ingest` intent, a `topic_agent` that merges new clips into existing TopicPages, a daily scan and an `/ingest` command. | 4–5 h |
| **Draft → approve workflow in Telegram:** inline buttons to approve or reject pending wiki changes; the git helpers exist in `graph_writer` but have no caller yet. | 4 h |

## Later: learning loop and polish

| Item | Size |
|---|---|
| **Card render module** [BL-05]: `agents/render/card.py` with a `RenderDict` contract and snapshot-tested card profiles; `export_anki.py` becomes a thin wrapper. | 9 h |
| **Anki export feedback** [BL-06]: tag cards whose mnemonic is outdated and send a Telegram summary after each export. | 5 h |
| **Multi-modal backfill and asset dedup** [BL-08]: process quick-saved images and PDFs later, and dedupe assets by SHA-1. | 4 h |
| **Self-refreshing user profile** [BL-10]: a weekly pass that updates `user_profile.md` from the wiki's statistics. | 4 h |
| **Growth telemetry** [BL-13]: `scripts/graph_stats.py` for page counts, link density and cost per run. | 2 h |
| **End-to-end tests for the bot handlers** with a mocked Telegram update and pipeline. | 4 h |
| **Practice rounds:** spaced prompts that ask the user to retell high-`story_score` facts, built on python-telegram-bot's `ConversationHandler`. | 6 h |

Ideas without a commitment yet are collected (in German) in [doc/CHANCEN.md](doc/CHANCEN.md).
