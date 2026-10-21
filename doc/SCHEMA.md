# SCHEMA.md: The constitution of llm-personal-knowledge-os
> Version: 0.4 (English edition, 2026-10) | Status: DRAFT | German original: [de/SCHEMA.md](de/SCHEMA.md)
>
> Decision references (`ENT-xxx`) point to the German decision log [ENTSCHEIDUNGEN.md](ENTSCHEIDUNGEN.md).

---

## 1. System philosophy

This system is **not a note-taking tool**. It is a persistent, compiled memory of the user: maintained by LLMs, navigable through Obsidian, triggered by everyday life.

Three axioms:
1. **Raw data is sacred.** It is never modified, only read and processed.
2. **The graph belongs to the AI, outside declared human-owned zones.** Humans don't write wiki pages by hand; the AI writes, the human reads and corrects. The exception is the **human-owned zones** declared in §2 (ENT-062): there, only the human writes. The AI reads them as graph_context and flags contradictions (the §8 mechanism, the user decides), but **never** writes or auto-fixes there. This is enforced by a deterministic guard in `graph_writer` (§2). Changing ownership is a deliberate act by the user (remove the flag or move the page), never a side effect.
3. **Every interaction is a potential insight.** The supervisor rates every input for its relevance to the graph.

---

## 2. Directory layout

All paths are relative to the **vault root** (`KOS_VAULT_ROOT`, default `sample_vault/`). Code lives in the repository; data lives in the vault.

```
<vault>/
│
├── raw/                        # [IMMUTABLE] raw data: the AI reads, never writes
│   ├── events/                 # Telegram inputs, trigger messages (JSON + MD)
│   ├── sources/                # articles, PDFs, web clips (Obsidian Web Clipper)
│   ├── assets/                 # images, audio (stored locally)
│   └── style_refs/             # style reference media (IMMUTABLE)
│       └── [name]/             # one folder per reference: comedian/, ted-talk/, ...
│
├── wiki/                       # [LLM-OWNED] compiled knowledge (except human-owned zones, see below)
│   ├── personal/               # personal facts, diary entries
│   │   ├── facts/              # individual PersonalFact pages
│   │   ├── stories/            # elaborated stories / punchlines
│   │   ├── style_refs/         # StyleProfile pages (sp_[name].md)
│   │   └── health/             # [HUMAN-OWNED] health notes: human writes, AI reads (ENT-062)
│   ├── language/               # multilingual vocabulary, grammar, culture
│   │   ├── vocab/              # individual VocabEntry pages (all languages)
│   │   ├── grammar/            # grammar concepts (per language)
│   │   ├── culture/            # people, places, cultural keywords (per country/region)
│   │   └── bridges/            # cross-language correlations and cognates
│   ├── concepts/               # general concepts, themes, cross-links
│   └── topics/                 # TopicPages: aggregated external knowledge (tp_*, §3.9)
│
├── index.md                    # [LLM-MAINTAINED] table of contents of all wiki pages
├── log.md                      # [LLM-MAINTAINED] append-only operation log
└── user_profile.md             # [LLM-MAINTAINED] compressed user signature (§3.8)
```

**Ingestion source mounts (ENT-058):** ingestion reads the configured list `SOURCE_DIRS = ("raw/sources/", "raw/Wiki/Clippings/")` (defined in `scripts/ingest/`). `raw/Wiki/Clippings/` (an Obsidian Web Clipper folder) is a registered source mount: a configuration entry, not a file move, and no clipper reconfiguration is needed. The rest of `raw/Wiki/` (vault artifacts) is ignored.

### Human-owned zones (axiom 2 carve-out, ENT-062)

Declared directories in which **only the human** writes. Axiom 2 applies without restriction outside these zones.

| Zone | Contents | Since |
|---|---|---|
| `wiki/personal/health/` | Human-owned health notes (type family §3.10) | 2026-07-04 (ENT-062) |

**Double marking:** (1) The declaration in this table, enforced by the deterministic guard in `graph_writer` (`assert_writable()`, a hard exception before every write; the same shared function must be called before every future file-write path, including lint auto-fixes). (2) `owner: human` frontmatter on each page, which keeps the marking portable, visible in Obsidian and filterable by lint. A lint detector (`find_zone_owner_violations()`) checks that both markings agree. The AI reads the zone as graph_context and flags contradictions (§8), but never writes or auto-fixes there.

---

## 3. Entity ontology

The following types are the building blocks of the graph. Every wiki page belongs to exactly one type.

### 3.1 `PersonalFact`
> A story-worthy event, observation or trait of the user.

**Fields:**
- `title`: short, memorable title
- `date`: date of the event (not of capture)
- `context`: where / when / with whom
- `core_fact`: the raw fact in 1–2 sentences
- `narrative_hook`: the potential punchline, what makes it interesting
- `related_facts`: links to other PersonalFacts
- `story_score`: 0–10, how story-worthy (LLM-rated)
- `status`: `raw` | `elaborated` | `story-ready`

### 3.2 `VocabEntry`
> A word or expression in any target language, with full learning context and linguistic bridges to other languages the user knows.

**Fields:**
- `word`: the target word
- `language`: ISO 639-1 code (`es`, `en`, `de`, `fr`, ...), **derived from the graph**
- `translations`: map of language → translation
  ```yaml
  translations:
    de: "knusprige, leicht angebrannte Reisschicht am Pfannenboden"
    en: "crispy toasted rice layer at the bottom of the pan"
  ```
- `conjugation`: verb conjugation (for verbs, language-specific)
- `example_sentences`: three example sentences in the target language
- `mnemonic`: memory aid (LLM-generated, using the user's known languages)
- `cross_language_bridges`: cognates, false friends or semantic parallels in other languages
  ```yaml
  cross_language_bridges:
    - lang: en
      type: concept-gap
      note: "No single English word; borrowed from Valencian (socarrar = to toast lightly)."
  ```
- `ipa`: optional pronunciation, e.g. `"[so.kaˈrat]"` (ENT-055)
- `anki_id`: ID of the matching Anki note (after export)
- `difficulty`: `A1` to `C2` (CEFR, language-specific)
- `related_words`: links to related VocabEntries (also across languages)

**Language detection from the graph:**
The language agent periodically analyzes the language distribution in `raw/events/` and `raw/sources/` and updates `wiki/language/user_language_profile.md`. That file controls which languages are prioritized in `translations` and `cross_language_bridges`.

### 3.3 `CulturalEntry`
> A person, place, event or cultural keyword. **Not limited to one language or region**, but always with geographic and linguistic context.

**Fields:**
- `name`: name of the entity
- `type`: `person` | `place` | `event` | `cultural-concept`
- `country`: ISO 3166-1 alpha-2 code (`ES`, `MX`, `US`, `GB`, `DE`, ...)
- `language_context`: primary language(s) of the entity (ISO 639-1 list)
- `summary`: 3–5 sentence summary
- `why_relevant`: why it matters to this user (LLM-personalized from the graph context)
- `cross_cultural_links`: connections to entities of other cultures or countries
  ```yaml
  cross_cultural_links:
    - entry: "[[c_es_paella-valenciana]]"
      note: "Rice dish family: paella ↔ risotto, bridge ES ↔ IT"
  ```
- `sources`: links to sources in `raw/sources/`
- `related_entries`: links to other CulturalEntries

### 3.3.1 `LanguageBridge`
> A dedicated type for explicit connections between languages: cognates, false friends, structural parallels, cultural concepts without an equivalent.

Lives in `wiki/language/bridges/`. Created automatically by the language agent when it discovers correlations.

**Fields:**
- `type`: `cognate` | `faux-ami` | `concept-gap` | `structural-parallel`
- `languages`: list of the languages involved
- `entries`: links to the VocabEntries involved
- `insight`: the learning-relevant insight in 1–2 sentences

### 3.4 `Concept`
> An abstract theme or field of knowledge (cross-domain).

**Fields:**
- `title`: concept name
- `summary`: condensed explanation
- `connections`: links to all entities that touch this concept
- `open_questions`: open questions, an invitation to explore further

### 3.5 `RawEvent`
> An unprocessed input (Telegram message, manual trigger). Lives in `raw/events/`.

**Fields:**
- `timestamp`: ISO 8601
- `source`: `telegram` | `manual` | `scheduled`
- `content`: raw text or structured JSON
- `processed`: `true` | `false`
- `wiki_refs`: links to the wiki pages created or updated from it

### 3.6 `StyleProfile`
> An aggregated style profile of a speaker or comedian reference, built by aggregating several `StyleFingerprints` from `raw/style_refs/[name]/`. Lives in `wiki/personal/style_refs/sp_[name].md`.

**Fields:**
- `name`: identifier of the reference (e.g. `"ted-talk"`)
- `sample_count`: number of contributing clips or transcripts
- `confidence`: 0.0–1.0 (thresholds: 1→0.25, 3→0.60, 5→0.85, 8→1.00)
- `avg_words_per_second`: mean speaking rate (only with audio samples)
- `avg_pause_before_punchline`: mean pause before the punchline in seconds (audio only)
- `setup_ratio`: mean setup vs. punchline share across all samples (0.0–1.0)
- `key_patterns`: core patterns that occur in ≥ 50 % of the clips
- `style_tags`: labels with a frequency of ≥ 50 % of the clips
- `sources`: paths to all contributing files in `raw/style_refs/[name]/`

**Usable for feedback from** `confidence >= 0.60` (≥ 3 samples).

**Linking:** StyleProfiles don't link to other wiki entities, but PersonalFact `practice_log` entries reference the active StyleProfile via `style_profile_ref`.

### 3.7 `ServiceDefinition`
> A domain-specific practice routine generated from the graph content that enriches the StyleProfile along dimensions that diary and language alone don't cover (e.g. explaining a technical topic, Spanish improv). Lives in `wiki/services/sd_[slug].md`. Detailed specification, workflow and ServiceInstance handling: `COMP_SERVICES.md` (German; status: phase 3, planned).

**Required frontmatter (minimum fields):**
- `type: ServiceDefinition`
- `slug`: kebab-case identifier (unique)
- `domain`: topical category (`finance`, `language`, `presentation`, ...)
- `style_context_key`: key in the active `StyleProfile.context_profiles` used for aggregation
- `analysis_type`: `style_fingerprint` | `story_lab` | `vocab` | `language_quality`
- `created`, `updated`, `status`, `tags`, `sources`, `related` (see §5)

**Linking:** `practice_log` entries from service runs reference `service_slug` and `style_context_key`. The full schema (including `cost_estimate`, `conversation_config`, `ServiceInstance`) is in COMP_SERVICES.md §2.

### 3.8 System files (`user_profile.md`, `index.md`, `log.md`)

These three files are **not wiki entities**: they have no `type:` in their frontmatter and live directly in the vault root. Only agents and scripts write them.

#### `user_profile.md`: compressed user signature

Always loaded into the supervisor's context (~80–120 lines). Template:

```markdown
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# User profile

## Language profile
- Primary language: de
- Active target languages: [es, en]
- Input distribution (30 days): de: 60%, es: 30%, en: 10%
- Input distribution (90 days): de: 65%, es: 25%, en: 10%

## Interest clusters
- [cluster name] (high | medium | low) — [basis: N pages]

## PersonalFacts profile
- Total: N PersonalFacts
- Average story_score: X.X
- High-score facts (≥ 7) not practiced: N
- Last elaborated: YYYY-MM-DD

## Bootstrap
bootstrap_progress: N/10
bootstrap_complete: true | false
bootstrap_started: YYYY-MM-DD

## Style
active_style_profile: "[name]" | null

## Thresholds (system defaults, can be overridden)
concept_threshold: 3
story_score_elaborate_threshold: 6
story_score_review_required: 7
stale_raw_days: 7
```

#### `index.md`: table of contents of all wiki pages

One section per entity type, regenerated deterministically by `scripts/rebuild_index.py`. Format as described in ARCHITECTURE.md §2.2.

#### `log.md`: chronological operation log

Append-only. Format: `## [YYYY-MM-DDTHH:MM] operation | short description`

### 3.9 `TopicPage`
> Aggregated **external knowledge** on a topic, distilled from external sources (`raw/` clips), with source attribution and consensus/dissent as first-class content. Created **by ingestion only, never emergently** (distinct from `Concept`, ENT-010 unaffected). Lives in `wiki/topics/`. Decision: ENT-057.

**Frontmatter:**

```yaml
---
type: TopicPage
topic: karpathy-llm-wiki   # kebab slug, == file name without prefix (tp_[domain]_<topic>.md)
domain: health | tech | language | music | esport | photo | career | other
mode: claims | digest      # claims: consensus / dissent / single findings (empirical knowledge)
                           # digest: key statements / primary vs. reception / assessment (design or definitional knowledge)
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: raw | merged | reviewed  # raw = first extraction (1 source), merged = ≥ 2 sources consolidated,
                                 # reviewed = approved by the user
tags: []
sensitivity: sensitive     # mandatory default for domain: health (ENT-061); otherwise optional (default public)
sources:                   # required, ≥ 1; structured: anchor for dedup and attribution
  - key: A                 # short key for attribution in the body ([A] 3:38)
    id: "yt:exampleVid1"   # canonical ID: "yt:<video_id>" | "url:<normalized-url>" | "sha1:<hash>" (fallback)
    path: "raw/Wiki/Clippings/Example Source A.md"
    author: "Dr. Jane Doe" # plain text, NO [[wikilink]] (raw/ is not part of the wiki)
    tier: 3                # 1–5, scale below; default when extraction is uncertain: 5
    published: 2024-03-01  # optional (often missing)
related: []                # may include links to human-owned pages (§3.10): read yes, write never
---
```

**Deliberately NOT in the frontmatter:** a global `confidence` field (a page has high *and* low confidence claims, so confidence is stated per claim in the body); `independent_source_count` as a persisted field (derivable from the distinct `sources[].author` values, and redundancy would be a source of drift); the claims themselves as YAML (the page is meant to be read; machine readability comes from the body grammar).

**Body grammar for `mode: claims`** (human-readable and regex-parsable, strict line grammar):

```markdown
# <Topic>

## Konsens
- **Claim:** <atomic, decontextualized statement> | **Quellen:** [A 3:38], [C 6:05] | **Konfidenz:** hoch
## Dissens
- **<Question in dispute>.**
  - **[A] sagt:** … (evidence location)
  - **[B] sagt:** … (evidence location)
  - **Einordnung:** … (including a reference to the user's position, if a human-owned page states one)
## Einzelbefunde
- <statement> | [B 9:06]
## why_relevant
> 2–3 sentences linking to the user's goals ([[…]] links to human-owned pages are allowed: read yes, write never).
```

> The section headings and field labels (`Konsens` = consensus, `Dissens` = dissent, `Einzelbefunde` = single findings, `Quellen` = sources, `Konfidenz` = confidence with values `hoch`/`mittel`/`niedrig` = high/medium/low, `Einordnung` = assessment) are German literals in the current grammar. Planned extraction and lint code (BL-17/BL-18) is specified against these exact strings.

**Body grammar for `mode: digest`:** `## Kernaussagen` (key statements, with source keys, confidence optional) / `## Primärquelle vs. Rezeption` (primary source vs. reception) / `## Einordnung` (assessment) / `## why_relevant`. Taxonomies and lists are legitimate content here.

**Rules for both modes:**
- **An evidence location is required for every claim** (timestamp `MM:SS` for transcripts, section title for articles). A claim without an evidence location is an abstain: the extraction prompt discards it, and lint flags it if one slips through.
- The body references sources only as `[<key> <evidence location>]`. **No `[[wikilink]]` to `raw/` files** and **no URLs in the body** (they are in the clip's frontmatter).
- `## Dissens` in `mode: claims` pages is **healthy first-class content**, not a contradiction symptom in the sense of §8. Only a contradiction between a TopicPage and a human-owned page must be flagged (the user decides).
- **Mandatory disclaimer** for `mode: claims` + `domain: health`, as the first body line under the `# <Topic>` heading (ENT-061). The current German wording means: *"Aggregated external knowledge, not medical advice. Source tier ≠ medical recommendation."*
  ```markdown
  > Aggregiertes Fremdwissen, keine medizinische Beratung. Quellen-Tier ≠ ärztliche Empfehlung.
  ```

**Source tier scale (normative, ENT-060):**

| Tier | Meaning |
|---|---|
| 1 | Primary source / cited study |
| 2 | Specialist physician / evidence-focused podcast |
| 3 | Physician-influencer with a sales funnel |
| 4 | Anecdote, n = 1 |
| 5 | Aggregator / unknown |

**Default when extraction is uncertain: tier 5** (conservative).

**Confidence derivation rule (normative, ENT-060; deterministic, never a raw count):**

- **Independence** = the number of distinct authors, determined by fuzzy matching (`SequenceMatcher ≥ 0.85`: "Dr. Jane Doe DC" ≈ "Dr. Doe" = one author), not string equality.
- `hoch` (high) = ≥ 2 independent authors, at least one with tier ≤ 2
- `mittel` (medium) = several sources by the same author OR exactly one source with tier ≤ 2
- `niedrig` (low) = only tier ≥ 3, or mechanistically unsupported

**The tier basis is visible in every confidence line** in the body (e.g. `**Konfidenz:** mittel (3 Quellen, 1 Autor, tier 3)`). The pseudo-consensus case (3 sources = 1 author) is therefore `mittel` by definition, never `hoch`.

### 3.10 Human-owned type family (`HealthProtocol`, `HealthReview`, `DeepResearchPrompt`)
> Pages in the human-owned zone `wiki/personal/health/` (§2, ENT-062). They are **not written by the AI**, so they need no full schema and no agent specification, only the ability to be indexed. **Required fields:** `type` (one of the three family types), `created`, `owner: human`. Everything else (status, tags, related, body structure) is up to the user. `rebuild_index.py` lists them in the `Human-Owned (health)` section, which makes them visible as graph_context (read yes, write never).

---

## 4. File naming conventions

| Entity type | Prefix | Format | Example |
|---|---|---|---|
| PersonalFact | `pf_` | `pf_YYYY-MM-DD_kebab-title.md` | `pf_2026-03-22_first-burnt-socarrat.md` |
| VocabEntry | `v_` | `v_[lang]_kebab-word.md` | `v_es_socarrat.md`, `v_en_serendipity.md` |
| CulturalEntry | `c_` | `c_[cc]_kebab-name.md` | `c_es_paella-valenciana.md`, `c_mx_frida-kahlo.md` |
| LanguageBridge | `lb_` | `lb_[lang1]-[lang2]_kebab-topic.md` | `lb_es-en_azafran.md` |
| Concept | `con_` | `con_kebab-concept.md` | `con_storytelling-structure.md` |
| RawEvent | — | `YYYY-MM-DDTHH-MM-SS_source.json` | `2026-04-18T09-32-11_telegram.json` |
| StyleProfile | `sp_` | `sp_[name].md` | `sp_ted-talk.md` |
| TopicPage | `tp_` | `tp_[domain]_kebab-topic.md` (stored in `wiki/topics/`) | `tp_tech_karpathy-llm-wiki.md` |

---

## 5. Frontmatter standard (YAML)

Every wiki page starts with this YAML block:

```yaml
---
type: PersonalFact | VocabEntry | CulturalEntry | Concept
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: raw | elaborated | story-ready | archived
tags: []
sources: []       # links to raw/sources/ or raw/events/
related: []       # internal wiki links [[other-page]]
---
```

The frontmatter must parse with `yaml.safe_load` without workarounds. `agents/frontmatter.py` is the single helper for reading, writing and patching it.

---

## 6. Tech stack

### 6.1 Components

| Component | Technology | Rationale |
|---|---|---|
| LLM core | Claude API (Anthropic) | Strong reasoning for synthesis tasks |
| Bulk operations | Claude Haiku 4.5 | Cheap for lint, indexing, classification |
| Agent framework | LangGraph (Python) | Explicit state machines, debuggable |
| Input trigger | python-telegram-bot | Friction-free raw data capture |
| Anki integration | genanki (`.apkg` export) | Local, no Anki process or cloud needed |
| Knowledge store | Markdown files + git | Obsidian-compatible, versioned, portable |
| UI / navigation | Obsidian | Graph view, Dataview, free |
| Search (larger wikis) | SQLite FTS5 | BM25 search over Markdown, local |

### 6.2 Extensibility

The system follows a **plugin architecture**. New features follow this pattern:

```
agents/
├── base_agent.py          # abstract base class: the interface contract
├── supervisor.py          # central orchestration
├── language_agent.py      # module: language
├── diary_agent.py         # module: diary / personal facts
└── [new_component].py     # new agents follow the same interface
```

**New interfaces** (input channels) are isolated from the graph:
- WhatsApp → its own receiver, writes to `raw/events/` → same pipeline as Telegram
- Web UI → Flask/FastAPI endpoint → same `raw/events/` pipeline
- Scheduled jobs → a scheduler → the same agent call

**Principle:** anything that writes data to `raw/events/` is compatible. The graph core never changes.

### 6.3 LLM cost strategy (sensitivity tier model)

Personal facts are sensitive; vocabulary is not. Hence three tiers:

| Tier | Data category | Model | Cost (approx.) | Rationale |
|---|---|---|---|---|
| 1 | VocabEntry, CulturalEntry, Concepts | Claude Haiku 4.5 | ~$0.001/page | Not sensitive, bulk is fine |
| 2 | Synthesis, story crafting, bridges | Claude Sonnet 4.6 | ~$0.01/page | Needs good reasoning |
| 3 | PersonalFacts with `sensitivity: private` | Ollama (local) | $0.00 | Never leaves the device |

**Sensitivity tag** in every PersonalFact's frontmatter:
```yaml
sensitivity: public | sensitive | private
```
- `public` → Haiku / Sonnet
- `sensitive` → Sonnet, but anonymized before the API call (PII stripping)
- `private` → local model only (Ollama: `llama3.2` or `mistral`)

**Estimated monthly cost** with daily use: **$3–8 per month** (mostly Haiku for lint and indexing, Sonnet only for deep synthesis).

---

## 7. LLM instruction conventions

Every agent receives its context in this order:
1. `SCHEMA.md` (this file): system rules
2. `index.md`: current graph state
3. The task-specific module spec (`COMP_LANGUAGE.md`, `COMP_DIARY.md`, etc.)
4. Relevant wiki pages (selected by the supervisor)
5. The concrete task

---

## 8. Self-healing ("what is an unhealthy graph?")

A **lint pass** (daily, triggered by the supervisor) checks:

| Symptom | Diagnosis | Remedy |
|---|---|---|
| Wiki page has no `related:` | Orphan page | LLM finds and adds cross-links |
| `status: raw` older than 7 days | Unprocessed input | Agent task: elaborate or archive |
| Contradiction between two facts | Inconsistency | LLM flags it, the user decides |
| `story_score` > 7, never practiced | Wasted potential | Diary agent suggests a practice round |
| VocabEntry without an Anki card | Learning gap | Language agent triggers the Anki export |

---

## 9. Open questions

- [ ] How granular should the supervisor's user model be?
- [ ] Do we need an SQLite DB for structured queries on PersonalFacts?
- [ ] How should contradictions in the graph be resolved (LLM flag vs. auto-merge)?
- [x] Privacy: sensitivity tier model (public / sensitive / private → Haiku / Sonnet / Ollama)
- [x] Ollama setup: llama3.2 as the default, mistral as the fallback (ENT-028)
- [ ] Define the schema of `user_language_profile.md`: update frequency, thresholds?
