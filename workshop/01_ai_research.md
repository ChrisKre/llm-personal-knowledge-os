# 01 — AI-Research: Knowledge-Graph-Bestandsaufnahme + State-of-Art
> Phase 1 von 5 | Erstellt: 2026-05-08 | Rolle: AI-Experte Research | Modus: Implementierungs-Research mit GE-Anteilen
> Folge-Phase: UX (Phase 2). Handover: [handovers/handover_01_research_to_ux.md](handovers/handover_01_research_to_ux.md).

---

## Zusammenfassung (max 5 Bullets)

- **Der Karpathy-Knoten hält** — die Wiki-Idee ist nach 2026-Q1-Forschung weiter mehrheitsfähig (state-of-art-Implementierungen bauen explizit auf diesem Pattern auf, siehe §B). Kein Architekturschwenk nötig.
- **Aber der Index ist heute kaputt:** [index.md:7-23](../index.md#L7-L23) zeigt 18 PersonalFacts, deren "Summary" identisch zum Slug ist (`pf_X — pf_X`). Der `graph_reader` liefert dadurch nur Slug-basierte Pseudo-Tag-Treffer (siehe [agents/graph_reader.py:119-129](../agents/graph_reader.py#L119-L129)). **Ohne echte Summaries gibt es keinen graph_context.**
- **Lint ist Stub und das rächt sich jetzt:** [ENT-017](../doc/ENTSCHEIDUNGEN.md) legt Auto-Fixes als no-ops fest, der Index zeigt sichtbare Duplikate (`v_es_enzimismado` vs. erwartete `ensimismado`, drei `*madrugada*`-PFs an drei aufeinanderfolgenden Tagen). Konsolidierung passiert nicht — die Schuld wächst pro ES-Voice.
- **Multi-Modal-Extraktoren existieren, werden aber nicht genutzt:** [agents/extractors/](../agents/extractors/) ist vollständig (Audio/Image/PDF/URL/YouTube), aber `raw/sources/` ist faktisch leer und nur der Voice-Pfad ist live ([ENT-044](../doc/ENTSCHEIDUNGEN.md)). Bilder/PDFs/YouTube-Transkripte fließen nicht in den Graph zurück.
- **Symbiose Graph↔Frontend hat heute genau einen Pfad:** der Obsidian-Backlink im Anki-Back ([ENT-052](../doc/ENTSCHEIDUNGEN.md)). Das ist UX-Phase-2-Ankerpunkt und gleichzeitig die ärmste Stelle: der Renderer ist deterministisch, aber die Quelldaten sind durch Frontmatter-Schuld ([sessions/023 §Befund](../sessions/023_2026-05-07.md)) brüchig.

---

## Teil A — Bestandsaufnahme

### A1: Was ist der Knowledge Graph?

**Definition (operational):** Der Knowledge Graph ist eine kompilierte, querverlinkte Markdown-Struktur unter [wiki/](../wiki/), gepflegt durch LLM-Agenten, navigierbar über Obsidian, indexiert über drei System-Dateien im Repo-Root ([index.md](../index.md), [log.md](../log.md), [user_profile.md](../user_profile.md)).

**Größe heute** (2026-05-08, gezählt via Glob `wiki/**/*.md` aus dieser Session):

| Entität | Anzahl | Pfad |
|---|---|---|
| PersonalFact | 10 echte Files (Index meldet 18 — Drift!) | [wiki/personal/facts/](../wiki/personal/facts/) |
| VocabEntry — ES | 7 echte Files (Index meldet 10 — Drift!) | [wiki/language/vocab/](../wiki/language/vocab/) |
| LanguageBridge | 2 Files (Index meldet 3) | [wiki/language/bridges/](../wiki/language/bridges/) |
| CulturalEntry | 1 File ([c_es_flamenco.md](../wiki/language/culture/c_es_flamenco.md)) | [wiki/language/culture/](../wiki/language/culture/) |
| Concept | 0 | (Ordner existiert nicht) |
| StyleProfile | 0 | (Ordner existiert nicht) |

**Gesamt: ~21 Markdown-Files** — also weit unter dem Phase-2-Schwellwert von 150 ([ARCHITECTURE.md §6.3](../doc/ARCHITECTURE.md#63-graph-reader--index-abstraktion)) und deutlich unter dem 30-Seiten-Schwellwert in [ENT-027](../doc/ENTSCHEIDUNGEN.md). Wir sind in der **Bootstrap-Phase** ([KNOWLEDGE_GRAPH.md §6](../doc/KNOWLEDGE_GRAPH.md#6-graph-wachstumsphasen)), zweiter Anstieg.

**Drift Index ↔ Filesystem ist real.** [index.md](../index.md) listet `pf_2026-04-22_*` und `pf_2026-04-21_*`-Einträge die im Filesystem nicht (mehr) existieren. Außerdem: `v_es_enzimismado` (Tippfehler, sollte `ensimismado` sein), `v_es_hola`, `v_es_sonrisa` — alle drei nur im Index, nicht im Filesystem. Das ist nicht harmlos: jede `graph_reader`-Suche erzeugt _potenziell tote Treffer_.

**Relationen heute:** über Obsidian-Wiki-Links im `related:`-Frontmatter-Feld ([SCHEMA.md §5](../doc/SCHEMA.md#5-frontmatter-standard-yaml)). Plus implizite Relation per `cross_language_bridges` (auf VocabEntry) und `cross_cultural_links` (auf CulturalEntry). Manuell von [language_agent.write_entries](../agents/language_agent.py#L389-L557) in den Markdown-Body geschrieben — **ohne Backlink-Symmetrie**. Bidirektionale Konsistenz ist explizit Lint-Aufgabe ([KNOWLEDGE_GRAPH.md §4.3](../doc/KNOWLEDGE_GRAPH.md)) — und Lint ist Stub.

**Wachstums-Pfade** (heute aktiv):
1. **Telegram-Text** → [bot.py](../bot.py) → `raw/events/` → Supervisor → Diary/Language-Agent → WikiWrite ([ARCHITECTURE.md §3.3](../doc/ARCHITECTURE.md#33-supervisor-entscheidungslogik)).
2. **Telegram-Voice** → [audio_extractor.py](../agents/extractors/audio_extractor.py) (Whisper) → wie 1.
3. **Vocab via Hint-Gate** → [supervisor.py:87-95](../agents/supervisor.py#L87-L95) ([ENT-047](../doc/ENTSCHEIDUNGEN.md)/[ENT-048](../doc/ENTSCHEIDUNGEN.md)) → Language-Agent → Vocab + Bridges + Culture.
4. **Anki-Output** → [scripts/export_anki.py](../scripts/export_anki.py) ([ENT-050](../doc/ENTSCHEIDUNGEN.md) bis [ENT-052](../doc/ENTSCHEIDUNGEN.md)). Einseitig (Wiki → Anki); kein Sync-Back.

**Wachstums-Pfade die existieren aber nicht aktiv sind:**
- URL-/PDF-/Bild-/YouTube-Extraktoren ([agents/extractors/](../agents/extractors/)) — Code da, aber kein Telegram-Handler ruft sie für andere Inputs als Voice auf.
- Lint-Pfad ([agents/lint_agent.py](../agents/lint_agent.py)) — STUB ([ENT-017](../doc/ENTSCHEIDUNGEN.md)), nicht periodisch getriggert.
- Concept-Cluster aus PersonalFacts ([ENT-010](../doc/ENTSCHEIDUNGEN.md)) — Korrelations-Engine nicht implementiert. Concept-Verzeichnis existiert nicht.

---

### A2: Existierende Routinen (Indexierung / Updates / Retrieval / Konsolidierung / Multi-Modal)

#### (a) Indexierung
- **Was:** [index.md](../index.md) wird beim WikiWrite append-mäßig fortgeschrieben. Format: `## Section (N)` + `- [[slug]] — summary`.
- **Wie/Wer:** Implizit über `index_updater` (in [ARCHITECTURE.md §6.1](../doc/ARCHITECTURE.md#61-graph-struktur-ingestion-flow) als LangGraph-Node spezifiziert) — **Code-Search liefert kein eigenständiges Modul** (`agents/index_updater.py` existiert nicht). Vermutung: Index wird heute manuell oder gar nicht gepflegt; Drift bestätigt das.
- **Phase-Schalter ([ENT-027](../doc/ENTSCHEIDUNGEN.md)):** [graph_reader.py:20](../agents/graph_reader.py#L20) hat `WIKI_PAGE_THRESHOLD = 30`. Phase 2 (SQLite FTS5) ist Stub mit funktionierendem Fallback auf Phase 1, aber niemals aktiv getestet (siehe [hinweise/technischer_hinweis.md §Was nicht getestet](../hinweise/technischer_hinweis.md)).
- **Zusatz-Index `wiki_index.db`:** Nicht vorhanden — wäre Output von einem Build-Skript, das nicht existiert.

#### (b) Updates
- **Auf Wiki-Seiten:** [graph_writer.py:29-38](../agents/graph_writer.py#L29-L38) implementiert `create | update | append`. **Kein Diff-Merge** — `update` ist `path.write_text(content)`, also komplettes Überschreiben.
- **Auf Frontmatter:** Re-Export-Stempel `anki_id` in Wiki-Datei ([ENT-052](../doc/ENTSCHEIDUNGEN.md)) ist heute der einzige nicht-LLM-getriebene Frontmatter-Patch. Idempotenz: ja, beim zweiten Lauf keine weiteren Patches (Verifikation in S023 erbracht).
- **Auf `user_profile.md` und `user_language_profile.md`:** [language_agent.update_profile:343-383](../agents/language_agent.py#L343-L383) inkrementiert Counter-Felder via Regex. Funktioniert, aber Brüche silently möglich, wenn Format vom Template abweicht.
- **Draft → Master:** [graph_writer.approve_draft/reject_draft:45-65](../agents/graph_writer.py#L45-L65) implementiert. **Wird in der Pipeline aktuell aber nicht aufgerufen** (Bot-Code prüft kein `requires_user_approval` an klar einer Stelle für PersonalFacts mit `story_score > 7`). Konsequenz: Direct-Write auf `master`, kein Draft-Gate aktiv.

#### (c) Retrieval
- **Public API:** [graph_reader.search_wiki:53-75](../agents/graph_reader.py#L53-L75) und [graph_reader.fetch_context:78-112](../agents/graph_reader.py#L78-L112).
- **Phase 1 (aktiv):** [graph_reader._search_index_md:132-200](../agents/graph_reader.py#L132-L200). Algorithmus: Query → `_extract_keywords` (Regex, Stopword-Filter, ≥4 Zeichen) → Keyword-Overlap mit `_slug_to_tags(slug) ∪ _extract_keywords(summary)`. Score: `overlap / |query_keywords|`.
- **Schwäche der Phase 1:** `_slug_to_tags` zerlegt einen Slug wie `pf_2026-04-18_flamenco-kurs` in Tokens. Wenn die Index-Summary aber identisch zum Slug ist (heute der Fall, siehe A1), kommt **kein semantischer Mehrwert** aus dem Summary. Faktisch reduziert sich Retrieval auf Slug-Token-Match.
- **Phase 2 (Stub):** SQLite FTS5 + BM25 ([graph_reader._search_sqlite:207-256](../agents/graph_reader.py#L207-L256)). Kein DB-Build-Skript, kein Trigger-Setup.

#### (d) Konsolidierung / Deduplizierung
- **Heute: keine Routine.** [lint_agent.py](../agents/lint_agent.py) ist STUB pro [ENT-017](../doc/ENTSCHEIDUNGEN.md).
- Sichtbare Konsequenz: drei Files mit Variations-Stems `pf_*aprend-la-palabra-espa-ola-madrugada` aus zwei Tagen im Index, plus `enzimismado`/`ensimismado`-Tippfehler-Doppel.
- **Frontmatter-Schuld als Sonderfall** ([sessions/023 §Befund](../sessions/023_2026-05-07.md)): `dedent()` in [language_agent.py:423-459](../agents/language_agent.py#L423-L459) wirkt nicht auf eingesetzte Multi-Line-Blöcke — die elaborierten Vocab-Files haben strukturell-kaputtes YAML (sichtbar in [v_es_madrugada.md:1-22](../wiki/language/vocab/v_es_madrugada.md#L1-L22)). pyyaml verweigert; jeder Konsument muss Regex-Parser mitschleppen.

#### (e) Multi-Modal-Extraktion
- **Vorhanden, aktiv:** Voice ([audio_extractor.py](../agents/extractors/audio_extractor.py), faster-whisper, lokal, kostenlos, ENT-044 live in S021).
- **Vorhanden, inaktiv:**
  - [url_extractor.py](../agents/extractors/url_extractor.py) — requests + BeautifulSoup.
  - [pdf_extractor.py](../agents/extractors/pdf_extractor.py) — pdfplumber.
  - [image_extractor.py](../agents/extractors/image_extractor.py) — Claude Vision.
  - [youtube_extractor.py](../agents/extractors/youtube_extractor.py) — youtube-transcript-api.
- **Audio-Einschränkung:** [ENT-024](../doc/ENTSCHEIDUNGEN.md) — Claude API kein Audio-Input. Whisper liefert Transkript, danach Text-Pipeline. Tonalitäts-Coaching (Tempo, Pause, Enthusiasmus) ist V1-Stumpf.
- **Trigger-Lücke:** Bot-Handler ist nur für Text und Voice angeschlossen; URL/PDF/Bild/YouTube haben keine Eintritts-Tür. `raw/sources/` und `raw/assets/` sind heute leer (per Glob bestätigt).

---

### A3: Lücken (sehr kritisch, mit `[STUB]`-Flags)

| # | Bereich | Lücke | Quelle |
|---|---|---|---|
| L1 | Lint | `LintAgent._apply_auto_fixes()` ist `[STUB]` | [ENT-017](../doc/ENTSCHEIDUNGEN.md), [agents/lint_agent.py](../agents/lint_agent.py) |
| L2 | Indexierung | Kein `index_updater` als eigenständiger Code-Pfad; Drift Index ↔ FS belegt | [ARCHITECTURE.md §6.1](../doc/ARCHITECTURE.md#61-graph-struktur-ingestion-flow) vs. [agents/](../agents/) |
| L3 | Retrieval | `index.md`-Summaries sind Slug-Replikate → Phase 1 Retrieval ist faktisch nur Slug-Match | [index.md:7-23](../index.md#L7-L23) |
| L4 | Retrieval | Phase-2-SQLite-FTS5-Pfad nie getestet, kein Build-Skript | [hinweise/technischer_hinweis.md §Was nicht getestet](../hinweise/technischer_hinweis.md), [agents/graph_reader.py:207-256](../agents/graph_reader.py#L207-L256) |
| L5 | Konsolidierung | Keine Dedup-Routine; sichtbare Duplikate im Index | [index.md](../index.md) (PFs `*madrugada*`, Vocab `enzimismado`/`ensimismado`) |
| L6 | Konsolidierung | Frontmatter-Schuld in 7 elaborierten VocabEntries (pyyaml-verweigerung) | [sessions/023 §Befund](../sessions/023_2026-05-07.md), [v_es_madrugada.md](../wiki/language/vocab/v_es_madrugada.md) |
| L7 | Backlink-Symmetrie | A → B existiert, B → A muss von Lint nachgezogen werden — Lint ist STUB | [KNOWLEDGE_GRAPH.md §4.3](../doc/KNOWLEDGE_GRAPH.md), [ENT-017](../doc/ENTSCHEIDUNGEN.md) |
| L8 | Multi-Modal | Bild/PDF/URL/YouTube haben keinen Telegram-Trigger; Extraktoren ungenutzt | [bot.py](../bot.py), [agents/extractors/](../agents/extractors/) |
| L9 | Multi-Modal | `raw/style_refs/` ([ENT-021](../doc/ENTSCHEIDUNGEN.md)) leer; StyleProfile-Pfad faktisch dormant | Glob `raw/style_refs/**` |
| L10 | Concept-Bildung | [ENT-010](../doc/ENTSCHEIDUNGEN.md) Korrelations-Engine nicht implementiert; 0 Concepts | Glob `wiki/concepts/**` |
| L11 | Draft-Gate | `requires_user_approval` existiert, wird aber nicht im Bot-Flow eingesetzt | [agents/graph_writer.py:78-100](../agents/graph_writer.py#L78-L100), [bot.py](../bot.py) |
| L12 | Renderer ↔ Wiki-Symbiose | Anki-Back-Backlink ist heute der einzige Renderer-Pfad zurück zur Wiki-Quelle | [ENT-052](../doc/ENTSCHEIDUNGEN.md) |
| L13 | Multi-Modale Karten | Anki-Karten haben weder Audio (Whisper-Replay) noch Bild — Front/Back ist Text-only | [ENT-051](../doc/ENTSCHEIDUNGEN.md), [scripts/export_anki.py](../scripts/export_anki.py) |
| L14 | Sprach-Detection im Text | `language_detected` wird laut [ENT-048](../doc/ENTSCHEIDUNGEN.md) im Text-Pfad nicht gesetzt — Hint-Gate kann reines-ES-Tippen nicht abfangen | [ENT-048](../doc/ENTSCHEIDUNGEN.md) |

---

### A4: Heutige Schwachstellen (Top 5, nach Schmerz priorisiert)

1. **Index-Drift + Slug-Summaries** (L2 + L3). Akut: Retrieval ist heute schwach, weil die Datenbasis von `_search_index_md` aus zwei Quellen besteht — `_slug_to_tags` (Tokens aus Dateiname) und `_extract_keywords(summary)` (Tokens aus Summary). Wenn `summary == slug`, fällt zweite Quelle weg und der Score-Nenner halbiert sich. Bootstrap-Phase ist exakt der Zeitraum, in dem präzise graph_context-Treffer den größten Hebel hätten.
2. **Frontmatter-Schuld auf VocabEntries** (L6). Drei Folgewirkungen: (a) pyyaml-Verweigerung blockiert künftige Lint-Auto-Fixes, (b) Anki-Export schleppt Regex-Workaround mit, (c) jede Story-Lab-/Service-Anbindung an Vocab muss eigenen Parser bauen. Kosten wachsen mit Konsumenten-Zahl, nicht mit Zeit.
3. **Lint ist Stub trotz vier Lint-Tasks im Schema** (L1, L5, L7). [SCHEMA.md §8](../doc/SCHEMA.md#8-selbstheilungs-definition-was-ist-ein-kranker-graph) listet 5 Symptome — heute kein einziges automatisch reparierbar. Konsolidierung entsteht nicht von selbst.
4. **Multi-Modal-Pfade still: Code lebt, Trigger fehlen** (L8, L9). Bei einem Single-User-System mit ohnehin geringen Kosten (Haiku ~$0.001/Bildbeschreibung) ist das verschenkte Substanz: PDFs, Web-Clipper-Ausgaben und alte Whatsapp-Bild-Drops könnten den Bootstrap-Phase-Schmerz lindern.
5. **Renderer-Symbiose minimal** (L12, L13). Anki ist heute der einzige Frontend-Konsument. Der Rückkanal (Anki-Backlink) zeigt zur Wiki-Datei — er prüft nicht, ob die Datei seit dem Karten-Export geändert wurde, und er bringt weder Audio (obwohl Whisper-File da war) noch Bild (obwohl Vision möglich wäre). UX-Phase 2 hat hier viel Spielraum.

---

## Teil B — State-of-Art

> Recherche-Stichtag: 2026-05-08. Suchen via WebSearch + WebFetch durchgeführt. Quellen-Liste in §Quellen.

### B1: GraphRAG / verwandte Architekturen

**Microsoft GraphRAG** (Edge et al., arXiv 2404.16130 v2, 2025) etabliert ein zwei-stufiges Graph-Index-Verfahren: Entity-Extraction → Community-Detection → Community-Summaries. Query-Modi: **Local Search** (entity-zentriert, fan-out zu Nachbarn) und **Global Search** (sensemaking über alle Communities, partial-then-full Map-Reduce-Synthese). Substanzielle Qualitätsgewinne bei "What are the main themes?"-artigen QFS-Fragen, aber teure Indexierung.

**LazyGraphRAG** (Microsoft Research Blog, Nov 2024) ist die Antwort auf den Kosten-Cliff: **0,1 % der Indexierungs-Kosten** von Vollversion-GraphRAG, **bis zu 700× günstiger pro Query** bei vergleichbarer Qualität. Trick: NLP-Konzept-Extraktion + Co-Occurrence-Graph + Community-Detection sind günstig. LLM-Calls werden bis zur Query verschoben, dann durch ein **Relevance-Test-Budget** parameterisiert. Für Karpathy-Kompatibilität wichtig: **die Indexierung selbst ist NLP-statisch, kein Vektor-Store nötig**.

**Karpathy's LLM Wiki** (Original-Gist, 2026-04-04). Die hier zentrale Quelle. Drei Operationen: **Ingest** (10–15 Wiki-Pages pro neuem Source), **Query** (LLM liest Index → relevante Pages → synthetisiert mit Quellen), **Lint** (periodische Health-Checks: Widersprüche, stale Claims, Orphan-Pages, fehlende Cross-Refs, Daten-Lücken). Skalen-Hinweis: "_at small scale the index file is enough, no search engine required_" — Übergang etwa bei "moderate scale (~100 sources, hundreds of pages)". **Unser Wiki liegt mit ~21 Pages weit darunter** — Phase 1 ist objektiv ausreichend, das Problem ist die Index-Qualität, nicht die Wahl der Methode.

**Production-Praxis 2025/2026** (Branzan, Medium 2025; Memgraph 2025): KG-Konstruktion ist 2024–25 von Forschungs-Prototyp zu Produktions-System gereift. Trend: hybride Stacks aus FTS5/BM25 (Keyword), Embedding-Similarity (semantisch) und Recursive-CTE-Graph-Traversal — drei parallele Retrieval-Modi, kombiniert per Reciprocal Rank Fusion. **Karpathy-konform machbar nur mit (1)+(3); (2) bricht das Prinzip.**

### B2: Indexierung ohne Vektor-Store

**memweave** (Towards Data Science, 2025) baut Agent-Memory aus Markdown + SQLite ohne Vektor-DB. Pattern: drei FTS5-Virtual-Tables (`episodes_fts`, `entities_fts`, `edges_fts`), Sync-Trigger auf INSERT/UPDATE/DELETE, BM25-Ranking nativ. Unterstützt Reciprocal-Rank-Fusion über mehrere Modi.

**SQLite als Graph-DB** (Rohan Sharma, dev.to 2025): Recursive CTEs für Graph-Traversal mit Tiefen-Limit, kombiniert mit FTS5-Volltext. Argumentation: für Single-User-/kleine Multi-Tenant-Systeme schlägt SQLite-Stack Neo4j auf Latenz und Ops-Overhead — bei Wiki-Größen unter ~10⁶ Edges.

**Konkretes Pattern für unser System:** [ENT-027](../doc/ENTSCHEIDUNGEN.md) sieht exakt das vor (FTS5-Phase ab 30 Pages). Lücke: Build-Skript fehlt, Trigger fehlen. Wenn wir Phase 2 vorziehen, wäre ein 100-Zeilen-Indexer mit `CREATE VIRTUAL TABLE wiki_fts USING fts5(...)` + Walk-and-Insert-Pass tragfähig — und kompatibel mit dem bestehenden Stub-Schema in [graph_reader._search_sqlite](../agents/graph_reader.py#L207-L256).

**SQLite-Kosten:** 0 $. Lokal. Kein Modell-Call. Karpathy-konform.

### B3: Multimodale Wissens-Extraktion

**Spotify "Describe What You See"** (arXiv 2508.09789, 2025): Multimodal-LLM extrahiert Frame-Level- und Audio-Segment-Captions aus Video, GPT-4 fusioniert zu zeitlich-koh ärenten Beschreibungen — angewendet auf Empfehlungs-Pipeline. Kernlehre: **Caption-Generation ist die Brücke** zwischen Multi-Modal-Source und Text-Pipeline; sobald Caption existiert, gelten alle Text-Routinen.

**Audio-Visual LLM für Video Understanding** (Shu et al., ICCV 2025): Three-Stage-Pipeline (modality encoder → modality interface → LLM). Late Fusion ist die simpelste, robusteste Variante — und passt zur Karpathy-Trennung "Extractor → einheitliches Text-Schema → Pipeline".

**Multimodal AI 2025-Edition** (Tomar, Medium 2025): aktuelle Modelle Claude 3.7 Sonnet Vision, GPT-4o, Gemini 2.0, LLaVA, Qwen-VL. Für unseren Stack relevant: **Claude Haiku 4.5 unterstützt Vision** ([KNOWLEDGE_GRAPH.md §0.4 Bilder](../doc/KNOWLEDGE_GRAPH.md)) — der Image-Extractor ist heute korrekt verdrahtet, fehlt nur am Trigger.

**Was außerhalb unseres Prinzips läuft:** Embedding-basiertes Multi-Modal-Retrieval (z.B. CLIP). Was innerhalb übernehmbar ist: **Caption-Then-Index-as-Markdown** — exakt was unsere Extractoren tun. Nur Bilder noch nicht angeschlossen.

### B4: Agentic Memory 2025/2026

**A-Mem / Agentic Memory** (Liu et al., arXiv 2502.12110 + arXiv 2601.01885, 2026): unifiziertes LTM/STM-Framework, Memory-Operationen als **Tool-Calls** des Agenten exposed (`store`, `retrieve`, `update`, `summarize`, `discard`). Der Agent entscheidet selbst, was wann konsolidiert wird. Übertragung auf unser System: Lint-Operationen könnten als Tool-Aufrufe modelliert werden, aufgerufen vom Supervisor-Review-Schritt — statt aus einem täglichen Cron-Job.

**State of AI Agent Memory 2026** (mem0, Blog 2026): Memory ist 2026 First-Class-Architektur-Komponente mit eigenem Benchmark (LOCOMO). Fünf Mechanismen-Familien: (1) context-resident compression, (2) retrieval-augmented stores, (3) reflective self-improvement, (4) hierarchical virtual context, (5) policy-learned management. **Unser Wiki ist Mechanismus 2 + 3** — wir sind im Mainstream, nicht am Rand.

**ICLR 2026 MemAgents Workshop** (OpenReview): zeigt, dass Memory-für-Agenten ein eigenes Forschungsfeld geworden ist. Offene Probleme: Privacy-Governance ("how users inspect, edit, delete memories"), App-Level-Evaluation. Beides sind in unserem System konzeptuell gelöst (Sensitivity-Tier [ENT-006](../doc/ENTSCHEIDUNGEN.md), Obsidian als read-only Editor) — und damit struktureller Vorteil gegenüber typischen Cloud-Agent-Memory-Systemen.

**Karpathy-Pattern in der Community** (Spisak `second-brain` GitHub-Repo, kytmanov `obsidian-llm-wiki-local`, ussumant `llm-wiki-compiler` Claude-Code-Plugin, DAIR.AI Academy Blog 2025, TheToolNerd Step-by-Step-Guide): das Pattern ist 2025–26 reproduziert, gefork't, und mehrfach als Claude-Code-Plugin/Skill umgesetzt worden. Gemeinsame Erweiterungen, die wir übernehmen könnten:
- **Nightly-Lint mit fünf Phasen:** day-close, contradiction-reconcile, cross-source-pattern, orphan-heal, index-rebuild ([second-brain README](https://github.com/NicholasSpisak/second-brain), 2025) — mappt 1:1 auf [SCHEMA.md §8](../doc/SCHEMA.md) Symptome.
- **Index als One-Liner-Summaries (Pflicht):** statt unserer Slug-Replikate.
- **Reflective Pass:** der LLM darf seinen eigenen Output als Quelle in den Wiki zurück-filen ([ARCHITECTURE.md §2.3 QUERY](../doc/ARCHITECTURE.md#23-graph-operationen) sieht das vor — heute aber inaktiv, weil der Query-Flow nicht implementiert ist).

---

## Teil C — Chancen

> Format pro Chance: Klassifizierung · State-of-Art-Bezug · Aufwand · Kosten · Risiko/Trade-off · Querverweis an UX wenn relevant.

### C1: index.md-Summaries reparieren (Renderer + Frontmatter-`summary`-Feld)
- **Klassifizierung:** `[MACHBAR]`
- **Was:** Cron-Skript `scripts/rebuild_index.py` walkt `wiki/**/*.md`, liest Frontmatter, rendert one-line summary. Falls `summary:` in Frontmatter fehlt: einmaliger Sonnet-Pass über alle Pages füllt es nach (~21 Calls, einmalig).
- **State-of-Art-Bezug:** §B1 Karpathy-Original ("page listed with a link, a one-line summary"); §B4 second-brain "index-rebuild"-Phase.
- **Aufwand:** ~3 Stunden Skript + 1 Stunde Sonnet-Pass-Lauf.
- **Kosten:** Einmalig ~$0,21 für 21 Sonnet-Calls (à ~500 Token In/Out, [hinweise/technischer_hinweis.md §6](../hinweise/technischer_hinweis.md#6-kostenmessung--api-verbrauch-stand-session-017)). Periodisch (täglich): 0 $ — nur Markdown-Renderer.
- **Risiko:** Frontmatter-Schuld blockt einmaligen Sonnet-Pass auf den 7 elaborierten VocabEntries → C6 muss vorher laufen oder gleichzeitig.
- **Hebel auf Bestandsaufnahme:** löst L2 + L3 + Schwachstelle 1.

### C2: SQLite-FTS5-Build-Skript jetzt ziehen (Phase-2-Vorbereitung)
- **Klassifizierung:** `[MACHBAR-BEDINGT: nur sinnvoll wenn C1 davor]`
- **Was:** `scripts/build_wiki_index.py` baut `wiki_index.db` mit FTS5-Virtual-Table, Trigger fehlt vorerst (manueller Re-Build im Cron). Test-Lauf mit 21 Pages.
- **State-of-Art-Bezug:** §B2 memweave + dev.to/SQLite-as-Graph; entspricht [ENT-027](../doc/ENTSCHEIDUNGEN.md) Phase-2-Pfad.
- **Aufwand:** ~4 Stunden (Schema + Walker + erster Test gegen [graph_reader._search_sqlite](../agents/graph_reader.py#L207-L256)).
- **Kosten:** 0 $.
- **Risiko:** Phase 2 zu früh — wir sind bei 21 Pages, Schwellwert ist 30. Trade-off: aber **Phase 2 als Stub heute = ungetestet** und ein Bug-Risiko bei späterem Sprung. Frühe Test-Validierung ist günstiger als späte Reparatur.
- **(?)Offene Frage:** soll FTS5 schon jetzt aktiv geschaltet werden oder nur das Build-Skript existieren, mit `WIKI_PAGE_THRESHOLD` weiterhin auf 30?

### C3: Lint-Auto-Fixes minimal aktivieren (Backlink-Symmetrie + Index-Sync + Dedup)
- **Klassifizierung:** `[MACHBAR]`
- **Was:** Drei Detektoren in [agents/lint_agent.py](../agents/lint_agent.py) implementieren — keine Sonnet-Calls nötig:
  1. **Backlink-Symmetrie** (file-Walker, Adjazenz-Vergleich, Append in `related:` der Zielseite).
  2. **Index ↔ FS-Sync** (Glob `wiki/**/*.md` ↔ `index.md`-Einträge — fehlende ergänzen, tote löschen).
  3. **Slug-Stem-Dedup** (Levenshtein/SequenceMatcher auf Slug-Kandidaten; Treffer ≥ 0,9 → Telegram-Frage "X und Y wirken doppelt — zusammenführen?").
- **State-of-Art-Bezug:** §B1 Karpathy-Lint; §B4 second-brain nightly-agent fünf-Phasen-Lint.
- **Aufwand:** ~6 Stunden (drei Detektoren, ein Test-Run).
- **Kosten:** 0 $ (kein LLM). Frage 3 nutzt Telegram-Buttons, die existieren.
- **Risiko:** Auto-Backlink-Append kann Frontmatter-Schuld sichtbarer machen (write_text auf bereits kaputtem YAML). → C6 erst.
- **Hebel:** löst L1 + L5 + L7.

### C4: Frontmatter-Schuld-Migration (einmaliges Skript)
(!)ARCH-FRAGE: Migration schreibt direkt auf wiki/ — Verhältnis zum Draft→Master-Workflow (ENT-007)? Detail in 03_architect.md §A.(!)
- **Klassifizierung:** `[MACHBAR]`
- **Was:** `scripts/migrate_vocab_frontmatter.py` mit pyyaml-Roundtrip — liest jedes der 7 elaborierten Vocab-Files, parst per Regex (vorhandener Workaround), schreibt sauberes YAML zurück. Plus: Fix in [language_agent.write_entries:423-459](../agents/language_agent.py#L423-L459) — sauberer Frontmatter-Build mit pyyaml.dump statt f-string-dedent.
- **State-of-Art-Bezug:** §B1 Karpathy "lint = stale claims, missing cross-references" — strukturelles Datenmodell muss zuerst stimmen.
- **Aufwand:** ~2 Stunden Migration + ~1 Stunde Code-Fix in language_agent.
- **Kosten:** 0 $.
- **Risiko:** Migration ist destruktiv; vor Lauf Backup-Branch ziehen. (?)`anki_id` muss stabil bleiben — sonst SRS-State-Verlust gemäß [ENT-052](../doc/ENTSCHEIDUNGEN.md).
- **Hebel:** löst L6 + Schwachstelle 2.
- **(!)PO-Deja-vu:** Diese Chance ist im S024-Brief schon als Option 1/2/3 verhandelt; PO hat sie in den Workshop-Backlog (P2) verschoben. C4 ist die konkrete Form, die der Workshop empfiehlt.

### C5: Symbiose Graph↔Frontend — Anki-Karte als Renderer-Layer mit Health-Tag
(!)ENT-NÖTIG: C5a verlangt persistierten Export-Zeitstempel pro Karte — `out/anki_export_log.json` vs. `usage_stats:` im Wiki ist eine ENT-Frage. Detail in 03_architect.md §A.(!)
- **Klassifizierung:** `[MACHBAR-BEDINGT: erst nach C1 + C4]`
- **Was (zwei Sub-Chancen):**
  - **C5a** — `--health`-Modus für `scripts/export_anki.py`: Skript prüft `wiki/language/vocab/v_*.md` `updated`-Datum gegen Anki-`anki_id` (Anki-Tag `health::stale-mnemonic` setzen, wenn Wiki-Update neuer als Karten-Export-Zeitstempel). Sichtbar im Anki-Filter — der Lerner weiß, "diese Eselsbrücke wurde überarbeitet".
  - **C5b** — Im Anki-Back zwei statt einem Backlink: einer zur Vocab-Datei (heute schon), einer zum aktuellen, gerenderten `index.md#section`-Anker. UX prüft, ob das auf Mobile sinnvoll oder störend ist.
- **State-of-Art-Bezug:** §B1 Karpathy-Lint "stale claims"; §B4 second-brain reflective pass; [ENT-052](../doc/ENTSCHEIDUNGEN.md).
- **Aufwand:** C5a ~3 Stunden, C5b ~1 Stunde.
- **Kosten:** 0 $ (kein LLM, deterministisch).
- **Risiko:** Anki-Tag-Schema-Änderung → Re-Export setzt neue Tags; bestehende Filter könnten brechen. Idempotenz: tags-Vergabe muss deterministisch sein.
- **Querverweis an UX:** **Das ist die Symbiose Graph↔Frontend-Chance für Phase 2** (Charta Leitfrage 5). UX bitte prüfen: Welche **Renderer-Tags** machen einen Lerner produktiver, ohne Karten-Layout zu überfrachten? Welche **Backlinks** auf Mobile vs. Desktop? Welche **multimodalen Felder** auf der Karte (Audio-Replay vom ursprünglichen Whisper-File? Vision-Caption-Bild?)
- **Detail-Übergabe an UX:** [handovers/handover_01_research_to_ux.md §Symbiose](handovers/handover_01_research_to_ux.md).

### C6: Multi-Modal-Backfill als Mini-Service (Bilder/PDFs)
(!)ENT-NÖTIG: Sensitivity-Tier-Verhältnis (ENT-006) für Bilder ungeklärt — Vision-API ist Cloud, ohne PII-Stripping bricht das `private`-Tier. Detail in 03_architect.md §A.(!)
- **Klassifizierung:** `[MACHBAR-BEDINGT: erst wenn Bild-Trigger im Bot]`
- **Was:** Bot-Handler für `MessageType.PHOTO` und `MessageType.DOCUMENT` (PDF) anhängen → ruft existierenden [image_extractor.py](../agents/extractors/image_extractor.py) bzw. [pdf_extractor.py](../agents/extractors/pdf_extractor.py) → schreibt `raw/events/`-JSON wie heute Voice → normaler Ingest-Flow.
- **State-of-Art-Bezug:** §B3 Caption-then-Index-as-Markdown.
- **Aufwand:** ~3 Stunden (zwei Handler + einen End-to-End-Test).
- **Kosten:** Vision-Call: ~$0,001/Bild (Haiku). PDF-Extraktion: 0 $ (lokal). 5 Bilder/Woche → ~$0,02/Monat.
- **Risiko:** Vision-Halluzination bei Foto ohne Text. Mitigation: Fall-through wie Voice (Hint-Gate-Idee analog: Bild ohne Hint → Quick-Save in `raw/assets/`, kein Auto-Ingest).
- **(?)Offene Frage an PO:** Aktivieren oder als Workshop-Backlog für MVP-3?

### C7: Phase-2 Concept-Cluster mit LazyGraphRAG-Idee
- **Klassifizierung:** `[NICHT-HEUTE: zu wenig PersonalFacts für sinnvolle Cluster]`
- **Was:** Wenn Korpus auf ≥ 50 PersonalFacts wächst, NLP-basierter Co-Occurrence-Graph (Tag-/Slug-Token-Pairs), Community-Detection (z.B. Louvain), pro Community eine Concept-Seite (Sonnet-Synthese, einmalig pro Community-Erkennung).
- **State-of-Art-Bezug:** §B1 LazyGraphRAG; [ENT-010](../doc/ENTSCHEIDUNGEN.md) Korrelations-Engine.
- **Aufwand:** ~1–2 Tage; **dispatch erst wenn ≥ 50 Facts** (heute 10).
- **Kosten:** Index-Build NLP-frei = 0 $. Concept-Synthese: ~$0,02 pro Concept × geschätzt 5 = $0,10/Quartal.
- **Risiko:** Cluster mit zu wenig Inhalt erzeugen leere Concepts. Mitigation: Min-Cluster-Größe 3.

### C8: User-Profile Self-Refresh aus Graph-Inhalt
- **Klassifizierung:** `[MACHBAR-BEDINGT: erst wenn Lint live (C3)]`
- **Was:** Lint-Pass scannt `wiki/personal/facts/`, aggregiert Sprach-Verteilung, Themen-Cluster, story_score-Statistiken → Sonnet refresh `user_profile.md` einmal pro Woche.
- **State-of-Art-Bezug:** §B4 mem0 reflective self-improvement (Mechanismus 3); [ARCHITECTURE.md §3.4](../doc/ARCHITECTURE.md#34-supervisor-als-nutzer-anwalt).
- **Aufwand:** ~4 Stunden + ~$0,05/Woche LLM-Kosten.
- **Kosten:** ~$0,20/Monat.
- **Risiko:** Drift zwischen aktiver Telegram-Session-Kontext und persistiertem Profil. Mitigation: Append-Diff statt Overwrite.

---

## Empfehlungen für UX-Phase

> Was die UX-Rolle aus diesem File **zwingend** mitnehmen soll. Konkret, mit Zeilen-Verweisen.

1. **Lese §A4 (Schwachstellen) komplett** — die fünf Schmerzpunkte definieren, was UX nicht ignorieren darf, auch wenn UX-Empfehlungen nicht alle adressieren.
2. **Symbiose Graph↔Frontend ist deine Bühne** (Charta Leitfrage 5). Anker-Chance: **C5** mit zwei Sub-Pfaden (Health-Tag in Anki-Karten, zweiter Backlink). UX-Verdict gewünscht: Welche **Render-Layer-Erweiterungen** auf Anki-Karten sind sinnvoll, ohne das Karten-Layout zu überfrachten?
3. **Multi-Modal auf Karten ist offen** (L13). Bild im Anki-Back (Vision-Caption als Bildunterschrift)? Audio-Replay (das ursprüngliche Whisper-File aus dem `raw/events/`-Eintrag)? UX-Format-Empfehlung erwartet.
4. **Frontmatter-Schuld** ist dir nicht UX-eigen, aber sie blockt mehrere UX-Vorschläge (C5a braucht funktionierenden YAML-Parser für `updated:`). Bitte als Reihenfolge-Hinweis im Handover an Architekt aufnehmen.
5. **Index-Drift ist sichtbar in jedem Tool, das den Wiki konsumiert** (Obsidian, Anki-Export, künftige Renderer). Wenn UX einen neuen Render-Layer-Vorschlag macht — bitte prüfen, ob er gegen einen kaputten Index robust ist oder einen reparierten Index voraussetzt.
6. **Workshop-Charta:** UX darf **inline in `02_ux.md` Markierungen vom Architekten erhalten** (Veto/ENT-NÖTIG). Diese Datei (`01_ai_research.md`) bleibt nach Phase 1 unverändert; künftige Edits dürfen nur Marker hinzufügen.

---

## Risiken (Top 3)

1. **Frontmatter-Schuld als unsichtbarer Bremsschuh.** Heute wirkt sie nur in `wiki/language/vocab/`. Aber jede Konsumenten-Klasse (Anki-Export ✓, Lint geplant, Story-Lab geplant, Service-Routinen geplant) muss eigenen Regex-Parser mitschleppen. Kosten skalieren mit Konsumenten-Zahl, nicht mit Daten-Volumen. Top-Risiko, weil **C1, C3, C5, C8 alle blockieren**, bis C4 läuft.
2. **Index-Drift wächst proportional zu jedem Wiki-Write ohne Index-Updater-Code-Pfad.** Solange `index.md` ohne Code-Pfad geschrieben wird (Drift-Beleg in §A1), wird jeder neue Wiki-Write die Drift potenziell vergrößern. Das ist der Single-Point-of-Failure für alle graph_context-basierten Routinen — und damit für das Karpathy-Versprechen "context-rich agent decisions".
3. **Lint-Stub heißt: Konsolidierung passiert nie automatisch.** [ENT-017](../doc/ENTSCHEIDUNGEN.md) sieht Auto-Fixes nach MVP-2 vor. MVP-2 ist geschlossen ([sessions/024 §Verdict zum MVP-2-Status](../sessions/024_2026-05-07.md)). Wenn der Workshop nicht klar einordnet, **wann** Lint live geht, vermehrt sich technische Schuld weiter — speziell mit jeder ES-Voice (Hint-Gate fängt nur Funktionswort-Flut, nicht semantische Duplikate).

---

## Quellen

> Mindest-Anforderung: 8 externe Quellen mit URL/Titel/Datum/Kurz-Summary. **Auto-Validierung: 14 Einträge gezählt vor Commit.**

1. **[LLM Wiki Pattern (Karpathy Gist)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)** — Andrej Karpathy, 2026-04-04. Original-Definition des Patterns: ingest/query/lint, index.md + log.md als zentrale Navigation, "no search engine required at small scale". Pflicht-Quelle, weil unser System ein direkter Klon davon ist.
2. **[From Local to Global: A Graph RAG Approach (arXiv 2404.16130 v2)](https://arxiv.org/abs/2404.16130)** — Edge et al., Microsoft Research, Update 2025-02. Etabliert Graph-Index + Community-Summaries + Local/Global-Suche. Kerntext für GraphRAG-State-of-Art.
3. **[LazyGraphRAG: Setting a new standard for quality and cost](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)** — Microsoft Research Blog, 2024-11. **Wichtigste Single Source für unsere Budget-Kompatibilität:** 700× geringere Query-Kosten ggü. GraphRAG, NLP-statische Indexierung ohne LLM-Calls.
4. **[A-Mem: Agentic Memory for LLM Agents (arXiv 2502.12110)](https://arxiv.org/pdf/2502.12110)** — Liu et al., 2025. Memory-Operationen als Tool-Calls; Agent entscheidet selbst über store/retrieve/update/discard.
5. **[Agentic Memory: Unified Long-Term and Short-Term Memory Management (arXiv 2601.01885)](https://arxiv.org/abs/2601.01885)** — 2026. Folge-Arbeit zu A-Mem; relevant für Mechanismen-Familien-Klassifikation in §B4.
6. **[State of AI Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026)** — mem0, Blog 2026. LOCOMO-Benchmark, fünf Mechanismen-Familien, Privacy-Governance als ungelöstes Problem.
7. **[ICLR 2026 Workshop on Memory for LLM-Based Agentic Systems (MemAgents)](https://openreview.net/forum?id=U51WxL382H)** — OpenReview 2026. Beleg: Memory-für-Agenten ist 2026 eigenes Forschungsfeld mit Workshop-Format.
8. **[LLM-empowered Knowledge Graph Construction: A Survey (arXiv 2510.20345)](https://arxiv.org/abs/2510.20345)** — 2025. Übersicht zur Reife des KG-Construction-Felds; "language-driven and generative frameworks" als Paradigma.
9. **[memweave: Zero-Infra AI Agent Memory with Markdown and SQLite — No Vector Database Required](https://towardsdatascience.com/memweave-zero-infra-ai-agent-memory-with-markdown-and-sqlite-no-vector-database-required/)** — Towards Data Science, 2025. Konkretes Pattern für FTS5 + Markdown-Memory ohne Vektor-DB. Direkt-Vorlage für unseren Phase-2-Pfad.
10. **[SQLite as a Graph Database: Recursive CTEs, Semantic Search, and Why We Ditched Neo4j](https://dev.to/rohansx/sqlite-as-a-graph-database-recursive-ctes-semantic-search-and-why-we-ditched-neo4j-1ai)** — Rohan Sharma, dev.to 2025. Praxis-Bericht: SQLite-Stack für Wiki-Skalen unter ~10⁶ Edges schlägt Neo4j auf Latenz/Ops.
11. **[Describe What You See with Multimodal Large Language Models (arXiv 2508.09789)](https://arxiv.org/pdf/2508.09789)** — Spotify Research, 2025. Multi-Modal-Caption-Pipeline; Late-Fusion-Pattern für Audio+Video.
12. **[Audio-Visual LLM for Video Understanding (ICCVW 2025)](https://openaccess.thecvf.com/content/ICCV2025W/MMFM/papers/Shu_Audio-Visual_LLM_for_Video_Understanding_ICCVW_2025_paper.pdf)** — Shu et al., ICCV-Workshop 2025. Three-Stage Multimodal-Pipeline.
13. **[second-brain: LLM-maintained personal knowledge base for Obsidian (Karpathy LLM Wiki Pattern)](https://github.com/NicholasSpisak/second-brain)** — Spisak, GitHub 2025. Konkrete Open-Source-Implementierung des Karpathy-Patterns; relevant: Nightly-Lint mit fünf Phasen (day-close, contradiction-reconcile, cross-source-pattern, orphan-heal, index-rebuild).
14. **[LLM Knowledge Bases (DAIR.AI Academy Blog)](https://academy.dair.ai/blog/llm-knowledge-bases-karpathy)** — DAIR.AI, 2025. Strukturierte Aufbereitung des Karpathy-Patterns mit Bezug auf Compiler-Analogie; Kontext für unsere Operations-Definition (ingest/query/lint).

**Quellen-Auto-Validierung:** 14 Einträge — Soll ≥ 8 — **erfüllt**.
