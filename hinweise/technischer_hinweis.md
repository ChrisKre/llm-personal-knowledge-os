# Technischer Hinweis — Engineer → Product Owner
> Erstellt: Ende Session 009 (2026-04-19) | Autor: Engineering
> Zweck: Kritische technische Punkte die der Product Owner kennen muss — vor seiner Arbeit am Projekt.

---

## Status: Was funktioniert (Stand 2026-04-19)

**MVP-0 ist erreicht.** Die Pipeline läuft vollständig durch:
- Input → Klassifikation → Graph Context → DiaryAgent → Supervisor → WikiWrite
- Getestet mit Ollama (llama3.2), kein API-Key nötig
- Ergebnis: `intent=personal_fact`, `supervisor=accept`, 1 WikiWrite mit `story_score: 5`

**Was noch NICHT getestet wurde:**
- Language Agent (VocabEntry-Erstellung) — Code existiert, ungetestet
- `intent="both"` Parallel-Routing — Code korrekt, nie gelaufen
- graph_reader Phase 2 (SQLite) — wird erst bei ≥ 30 Wiki-Seiten aktiv
- Alle Writes mit `--write` Flag (bisher nur dry-run)

---

## Kritische technische Punkte für den Product Owner

### 1. API-Key ist der kritische Pfad zu MVP-1
Ollama reicht für Mechanik-Tests. Für echten Betrieb (korrekte story_scores, vollständige VocabEntries, nuancierte Supervisor-Entscheidungen) ist **Anthropic API-Key zwingend**.

- Kosten: Haiku ~$0.25/1M Tokens (sehr günstig für den Use Case)
- Sonnet ~$3/1M Tokens (nur für story_score + Elaboration verwendet)
- Schätzung: < $1/Monat bei normalem Privatnutzer-Volumen

**Entscheidung nötig:** Wann wird der API-Key beschafft?

### 2. Ollama-Qualitäts-Limitation ist bekannt und akzeptiert
llama3.2 hält strukturierte `key: value`-Ausgabeformate nicht zuverlässig ein. Folge: einzelne Felder in WikiWrite-Objekten können leer oder fehlformatiert sein.

Das ist **kein Bug** im Systemcode — es ist eine Modell-Limitation.
Für Production → Claude API. Für Mechanik-Tests → Ollama ausreichend.

### 3. Python 3.14 ist riskant
Das System läuft auf Python 3.14 (neueste Version, 2025). Viele Data-Science-Libraries haben noch keine stabilen Wheels für 3.14.

**Empfehlung:** Bei Problemen auf Python 3.11 oder 3.12 downgraden (bewährt, stabil).
Aktuell funktioniert alles — aber bei zukünftigen `pip install` könnten Kompilierungsfehler auftreten.

### 4. State-Merging bei parallelem Routing (bekannte Schwäche)
Bei `intent="both"` werden DiaryAgent und LanguageAgent parallel via LangGraph `Send()` gestartet. LangGraph mergt die States danach, aber ohne explizite Reducer-Definitionen können `wiki_writes`-Listen überschrieben statt zusammengeführt werden.

**Auswirkung:** "both"-Intent könnte nur den Output eines Agents behalten.
**Für MVP-1:** Kein Blocker — "both" tritt selten auf.
**Für Production:** Muss mit LangGraph `Annotated`-Reducern gelöst werden.

### 5. Audio-Pipeline ist V1-Stumpf
Das Kern-Feature "Story-Lab Coaching" hat in V1 eine funktionale Lücke: Claude verarbeitet kein Audio. Tonalitätswerte (Enthusiasmus, Natürlichkeit, Überzeugung) sind **nicht implementierbar** mit der aktuellen Claude API.

Was V1 liefert: Whisper-Timing + Transkript-Strukturanalyse (Text-basiert).
Was fehlt: Ton-Coaching auf Basis der echten Stimme.

**Bedeutung für den Product Owner:** Story-Lab in V1 ist ein "abgespecktes Feature". Das muss im MVP-Scope-Briefing klar kommuniziert werden.

---

## Chancen die der Product Owner kennen sollte

**Offline-First durch Ollama:** Das System ist komplett offline-fähig für `sensitivity:private`-Daten. Das ist ein unerwarteter Privacy-Vorteil — alle persönlichen/sensiblen Facts werden nie an einen Cloud-Provider gesendet.

**Graph wächst selbstverstärkend:** Je mehr Daten, desto bessere graph_context-Treffer, desto präzisere Scores. Der erste Monat ist der schwächste — danach steigt die Qualität automatisch.

**Obsidian sofort nutzbar:** Das Wiki ist ab der ersten WikiWrite-Datei in Obsidian lesbar. Kein zusätzliches Setup nötig.

---

## Technische Schulden (Backlog für PO-Radar)

| Schuld | Auswirkung | Priorität |
|---|---|---|
| `LintAgent._apply_auto_fixes()` sind Stubs | Lint läuft, repariert aber nichts | MVP-2-Zweitwelle (BL-07) |
| Kein LLM-Retry bei Timeout/Fehler | Pipeline bricht bei Ollama-Timeout ab | MVP-1 |
| graph_reader Phase 2 (SQLite) ungetestet | Risiko bei > 30 Seiten | MVP-2-Zweitwelle (BL-09) |
| bot.py kein Error-Handling | Telegram-Bot crasht bei Fehlern | MVP-1 |
| LangGraph Reducer für parallel routing | Möglicher Datenverlust bei "both"-Intent | MVP-1 |

> **Gestrichen (Workshop S025, 2026-05-08):** "AnkiConnect nicht implementiert" — obsolet seit [ENT-050](../doc/ENTSCHEIDUNGEN.md#ent-050-anki-export-scope-quell-selektion-trigger-format) (genanki-Pfad gewählt, nicht AnkiConnect).

---

## 7. Vom Workshop S025 aufgedeckte Schulden (Stand 2026-05-08)

> Quelle: [workshop/05_po_synthesis.md](../workshop/05_po_synthesis.md), [workshop/04_qm.md §Aktualisierungs-Vorschlag](../workshop/04_qm.md). Vom PO in S025-Phase 5 (Synthese) aufgenommen.

### Neue Schulden (vom Workshop aufgedeckt)

| Schuld | Auswirkung | Backlog-Bezug |
|---|---|---|
| **Index-Drift `index.md` ↔ Filesystem** — Index meldet 18 PFs, FS hat 10. Kein `index_updater`-Modul-Pfad existiert (Phantom in ARCHITECTURE.md §6.1). | Phase-1-Retrieval ist faktisch nur Slug-Token-Match; jede `graph_reader`-Suche liefert potenziell tote Treffer. | **BL-04** (C1 Index-Reparatur), MVP-2.5 Schritt 2 |
| **`ARCHITECTURE.md §6.3` widerspricht Code + ENT-027** — Threshold-Wert `150` vs. `30`. | Doku-konsistent vor BL-09 (FTS5-Build). Doku-Schuld, nicht funktional. | **BL-11**, niedrige Priorität |
| **`agents/graph_reader.py:3-4` Header-Kommentar widerspricht Z.20 derselben Datei** — Threshold `150` vs. `30` (QM-Bonus-Befund). | Interne Datei-Inkonsistenz, kein Funktions-Risiko. | **BL-11**, mit Threshold-Fix bündeln |
| **`agents/index_updater.py` ist Phantom** — referenziert in ARCHITECTURE.md §6.1 als LangGraph-Node, existiert nicht im Repo. | Nicht funktional kritisch, weil C1 (BL-04) das mit `scripts/rebuild_index.py` ablöst. Doku-Update Pflicht. | **BL-11** + BL-04 deckt es ab |
| **Drei `_split_frontmatter`-Implementierungen verteilt** — `export_anki.py:79-98` regex, `language_agent.py:423-459` f-string-dedent, geplanter `rebuild_index.py`-Pfad. | Wartbarkeits-Risiko: Bug-Fixes müssen drei Stellen treffen. | **BL-03 + BL-04** etabliert `agents/frontmatter.py`-Helper als Single-Source. |

### Behobene Schulden (durch Workshop-Vorschläge, sobald implementiert)

| Schuld | Wird behoben durch | Status |
|---|---|---|
| `LintAgent._apply_auto_fixes()` sind Stubs (alt-Eintrag oben) | BL-07 (C3 Lint-Auto-Fixes) | wartet auf BL-03 + BL-04 |
| graph_reader Phase 2 (SQLite) ungetestet (alt-Eintrag oben) | BL-09 (C2 SQLite-FTS5-Build) | wartet auf BL-04 + BL-11 |
| L1, L5, L7 aus [Workshop 01 §A3](../workshop/01_ai_research.md) — Lint-Stub, Konsolidierung, Backlink-Symmetrie | BL-07 | wartet auf BL-03 |
| L2, L3 — Index-Drift + Slug-Summaries | BL-04 | wartet auf BL-03 |
| L4 — Phase-2-FTS5 nie getestet | BL-09 | wartet auf BL-04 |
| L6 — Frontmatter-Schuld auf 7 Vocab-Files | BL-03 | abgeschlossen in S026 (commit BL-03) |

### Nicht erledigte Schulden (bleiben Backlog, vom Workshop nicht berührt)

- "kein LLM-Retry bei Timeout/Fehler" — MVP-1-Schuld, bleibt offen.
- "bot.py kein Error-Handling" — MVP-1-Schuld, bleibt offen.
- "LangGraph Reducer für parallel routing" — MVP-1-Schuld, bleibt offen (`Annotated`-Reducer-Refactor).

### Workshop-Output-Verweise (für Detail-Kontext)

- Workshop-Charta: [workshop/README.md](../workshop/README.md)
- Phase 1 (AI-Research): [workshop/01_ai_research.md](../workshop/01_ai_research.md)
- Phase 2 (UX): [workshop/02_ux.md](../workshop/02_ux.md)
- Phase 3 (Architekt): [workshop/03_architect.md](../workshop/03_architect.md)
- Phase 4 (QM): [workshop/04_qm.md](../workshop/04_qm.md)
- Phase 5 (PO-Synthese): [workshop/05_po_synthesis.md](../workshop/05_po_synthesis.md)
- Backlog: [workshop/backlog.md](../workshop/backlog.md)
- ENT-Updates aus S025: ENT-053, ENT-054, ENT-055, ENT-056 (revidiert ENT-007) in [doc/ENTSCHEIDUNGEN.md](../doc/ENTSCHEIDUNGEN.md)
- CHANCEN-Updates aus S025: §7.1 LazyGraphRAG, §7.2 Discord-Replay, §7.3 E2E-Tests in [doc/CHANCEN.md](../doc/CHANCEN.md)

---

## 8. Vom Workshop 02 aufgedeckte Schulden (Stand 2026-07-04)

> Quelle: workshop_02/03_qm.md §Aktualisierungs-Vorschlag, vom PO in S030-Phase 4 (Synthese) übernommen. Backlog: workshop_02/backlog.md.

### Neue Schulden (vom Workshop-02-QM aufgedeckt, Code-verifiziert)

| Schuld | Auswirkung | Backlog-Bezug |
|---|---|---|
| **FTS5-Switch bereits scharf, läuft auf `index.md`-Fallback** — `_wiki_size()` (`graph_reader.py:268`) zählt 37 Dateien > `WIKI_PAGE_THRESHOLD=30`; `search_wiki` routet bereits in `_search_sqlite`, das mangels `wiki_index.db` auf `_search_index_md` zurückfällt. Der echte FTS5-Query-Körper (`graph_reader.py:219-254`) ist ungetestet und aktiviert sich beim ersten DB-Bau. | Beim BL-09-Lauf endet der Fallback — ungetesteter Pfad wird live. **BL-09 ist Pflicht-Pre-Req des laufenden Ingestion-Betriebs (BL-19), nicht des Batches**; liefert mit Test gegen echte DB + TopicPage-/Health-Zeilen. | BL-09 (Scope erweitert, QK-22) |
| **`rebuild_index.SECTION_SPECS` kennt weder TopicPage noch die Health-Ad-hoc-Typen** (`HealthProtocol`/`HealthReview`/`DeepResearchPrompt`) — 15 Health-Seiten sind heute index-/graph_context-blind. | TopicPage-Aufnahme ist Batch-Merge-**kritisch** (R9): ohne sie findet `search_wiki(page_type="TopicPage")` nichts und der laufende Betrieb legt stumm Duplikate an. | **BL-14 + BL-15** — Schema-Schritt **vor** Batch (QM-Auflage 5) |
| **Idempotenz-Lücke der geplanten Batch-Ingestion** — Ledger auf Clip-Granularität kann bei Multi-Topic-Teilabbruch Themen-Seiten still verlieren (R4). | Stiller Datenverlust ohne Fehler; Lehre S029 (Repair-Pfad nicht fixpunkt-stabil). | **BL-17** (Stufe 5 atomar, QK-17a + Teilabbruch-Testfall) |

### Korrektur bestehender Einträge

- **BL-01 (`graph_writer.py`-Branch-Bug `main`→`master`) ist erledigt** — S026, commit `e4d2f28`; `reject_draft()` nutzt `master`. In `workshop_02/02_architect.md §B5/§D2` fälschlich als offene Pre-Req geführt — in künftigen Briefs nicht mehr einplanen.
- **Die zweite neue Schuld (Index-Blindheit TopicPage/Health-Typen) ist seit S031 erledigt** (BL-14+BL-15): `SECTION_SPECS` kennt `TopicPages` + `Human-Owned (health)`, `graph_reader` beide Mappings; 14 Health-Seiten tragen `owner: human` und sind index-/graph_context-sichtbar. Rest-Lücke: `antwort_deepresearch.md` (kein Frontmatter — PO-Entscheid ausstehend, siehe sessions/031).
- Der Alt-Eintrag „graph_reader Phase 2 (SQLite) ungetestet — Risiko bei > 30 Seiten" (Tabelle oben) ist präzisiert: die 30 sind **bereits überschritten** (37), das System läuft im Fallback — siehe erste neue Schuld.

### Notiz

- Der Draft→Master-Workflow (ENT-007/056) ist für die Clippings-Ingestion **reaktiviert**: der Sonnet-Freitext-Merge zu Gesundheitsthemen ist der ENT-056-§3-Trigger — Beschluss **ENT-059** (S030, revidiert ENT-056 partiell). Die §4-Liste deterministischer Direct-Master-Writes bleibt gültig.

---

## 6. Kostenmessung — API-Verbrauch (Stand Session 017)

`_call_claude()` in `agents/base_agent.py` loggt Token-Verbrauch und Kosten nach jedem LLM-Call.

### Preistabelle (USD, Stand 2026-04)

| Modell | Input / 1M | Output / 1M | Rolle |
|---|---|---|---|
| claude-haiku-4-5 | $0.80 | $4.00 | Classify, Detect, Review |
| claude-sonnet-4-6 | $3.00 | $15.00 | Vocab-Erstellung, Story-Score, Elaboration |

### Session-017-Messung (ca. 15 Test-Ingest-Calls)

Aus Log-Ausgaben (repr. Auswahl):

| Call | Modell | In | Out | Kosten |
|---|---|---|---|---|
| classify | haiku | ~120 | ~8 | $0.00013 |
| detect_words | haiku | ~180 | ~15 | $0.00021 |
| create_vocab | sonnet | ~500 | ~350 | $0.00675 |
| supervisor review | haiku | ~300 | ~120 | $0.00072 |

**Schätzung Normalnutzung:** 1 Text-Input mit `intent=both` ≈ $0.012–0.020 (1–2 Cent).
Bei 30 Inputs/Monat: ca. **$0.40–0.60/Monat**. Sehr günstig.

**Session-Kosten** werden im Log als `session=$X.XXXX` mitgeführt.

---

## Was der Engineer vom Product Owner braucht

1. **Entscheidung API-Key** — ohne Key kein MVP-1
2. **Klarheit über MVP-Scope** — was ist "done" für MVP-1? Nur Text-Telegram, kein Voice?
3. **doc/-Struktur** — welche Dateien in doc/ sind noch relevant? (`prompt.md`, `start.md`, `NEXT_SESSION_PROMPT.md` sehen wie Überbleibsel aus)
4. **Branch-Konvention** — sessions/009 sagt "Branch: main" aber es heißt `master`. Einmal festlegen.
