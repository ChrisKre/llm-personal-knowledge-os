# CLAUDE.md

Guidance for Claude Code sessions in this repository.

## What this is

A personal learning engine: Telegram capture → LLM agents → cross-linked Markdown knowledge graph → practice (Anki today; quizzes, spaced repetition and story retelling on the roadmap). See [README.md](README.md) for the architecture and [ROADMAP.md](ROADMAP.md) plus the GitHub milestones and issues for planned work. `ROADMAP.md` is the source of truth for scope.

## Data and privacy (hard rules)

- **Never commit personal data.** This repository is public. No real diary entries, vocabulary, health information, names of real people, web clippings, transcripts or local file paths, not in code, tests, docs, session logs or commit messages.
- **Real data lives outside the repo**, in the private vault selected by `KOS_VAULT_ROOT` (see `.env.example`). Unset, the code falls back to the fictional `sample_vault/`.
- Root-level `wiki/`, `raw/`, `index.md`, `log.md`, `user_profile.md`, `*.db` and `.env` are gitignored. Keep it that way; never force-add them.
- Never print, copy or commit `.env` contents.
- New examples and fixtures go into `sample_vault/` or `tests/` and must be fictional.

## Tests

- Run with `python -m pytest`.
- The suite is pinned to `sample_vault/` by `tests/conftest.py`, which forces `KOS_VAULT_ROOT` before `agents.config` is imported. Tests must never read or write a real vault; don't weaken that pin.
- New features come with tests against `sample_vault/`.

## Scope rule

The project uses hosted or local LLMs as they are, as an application component. It does **not** train, fine-tune, evaluate or benchmark models, and it does not build inference infrastructure. In code, docs, issues and commit messages, say "exercises" or "practice material", never "training data".

## Writing conventions

- **English** for code, comments, docs, commit messages and session logs from session 033 on. Sessions 001–032, `workshop/`, `hinweise/` and the other dev-log folders are German and stay that way.
- Some German is intentional and parsed by code: LLM prompts and their output keys, generated page headings (`## Übersetzungen`, `## Beispielsätze`, …), the TopicPage body grammar. Don't translate these without changing the parser and tests in the same commit. User-facing bot strings move to English via the i18n issue, not ad hoc.
- Agents never write files directly. They return `WikiWrite` objects; only `graph_writer` writes, and it enforces human-owned zones.

## Session workflow

- Each working session gets a log in `sessions/NNN_YYYY-MM-DD.md` (next number after the highest existing one), in English: goal, what was done, test count, open points, linked issues.
- Session logs describe the work, not the user's life. No personal details.
- Commit messages: `Session NNN: <what changed>`, English. Reference issues with `#N` where relevant.
- End each session with the log written and committed.
