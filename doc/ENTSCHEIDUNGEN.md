# ENTSCHEIDUNGEN.md — Zentrale Entscheidungs-Historie
> Erstellt: Session 010 (2026-04-19) | Autor: Product Owner
> Zweck: Alle projektweit wirksamen Entscheidungen an einer Stelle, chronologisch + thematisch auffindbar. Quellen: sessions/001–009, QUALITY_CONTROL_008.md, hinweise/technischer_hinweis.md.

**Lesehinweis:** Jede Entscheidung hat eine stabile ID (`ENT-NNN`). Wenn eine Entscheidung revidiert wird, bleibt die alte Nummer erhalten und bekommt Status `revidiert` mit Verweis auf die Neuentscheidung.

---

## Index nach Thema

| Thema | Entscheidungen |
|---|---|
| Stack & Runtime | ENT-001, ENT-033 |
| Datenmodell (Knowledge Graph) | ENT-002, ENT-005, ENT-009 |
| Tooling (Obsidian, Telegram) | ENT-003, ENT-004, ENT-018 |
| Sensitivity / Providers | ENT-006, ENT-028, ENT-031 |
| Agent-Architektur | ENT-013, ENT-014, ENT-015 |
| Knowledge-Graph-Ops | ENT-007, ENT-027 |
| Scoring & Elaboration | ENT-008, ENT-010, ENT-011 |
| Story-Lab / Impuls | ENT-019, ENT-020, ENT-021, ENT-022, ENT-024 |
| Services (GE-001) | ENT-012, ENT-026 |
| MVP-Scope | ENT-025, ENT-030, ENT-032, ENT-038, ENT-044 |
| Routing | ENT-029 |
| Prozess & Dokumentation | ENT-023, ENT-034, ENT-035, ENT-036, ENT-037, ENT-046 |
| UX-Radar / Telegram-UX | ENT-040, ENT-041, ENT-042, ENT-043, ENT-045 |
| Offene Entscheidungen | ENT-039 |

---

## Foundation (Sessions 001–003)

### [ENT-001] Stack: Python + LangGraph + Claude API
- **Entschieden:** 2026-04-15 (Session 001)
- **Entscheidung:** Projekt-Stack ist Python 3.x, LangGraph für State-Machines, Anthropic Claude API als LLM-Provider.
- **Begründung:** LangGraph erlaubt explizite Zustandsmodellierung für Supervisor-Routing. Claude ist der präferierte Anbieter des Nutzers. Python hat das beste Ökosystem für LLM + Obsidian-Interop.
- **Auswirkung auf Implementierung:** `agents/`, `main_workflow.py`, `bot.py` sind alle in Python. Pipelines nutzen LangGraph `StateGraph`.
- **Status:** final

### [ENT-002] Karpathy-Wiki-Prinzip: kompiliertes Markdown statt RAG
- **Entschieden:** 2026-04-15 (Session 001)
- **Entscheidung:** Kein RAG, kein Vektor-Store. Wissen liegt als hand-gepflegte (bzw. LLM-gepflegte) Markdown-Dateien vor, navigierbar über `index.md` und Wiki-Links.
- **Begründung:** Single-User-Szenario — Graph-Größe bleibt überschaubar. LLMs navigieren Markdown/Links nativ. Keine Embedding-Drift, keine Chunk-Artefakte.
- **Auswirkung:** Alle Entitäten sind `.md`-Dateien mit YAML-Frontmatter. `graph_reader` liest direkt das Dateisystem.
- **Status:** final

### [ENT-003] Obsidian als Frontend-Editor/Viewer
- **Entschieden:** 2026-04-15 (Session 001)
- **Entscheidung:** Obsidian ist der Standard-Viewer/Editor für den Wiki-Graphen.
- **Begründung:** Native Unterstützung für Wiki-Links, Backlinks, Tags; plattformübergreifend; keine Server-Infrastruktur nötig.
- **Auswirkung:** Dateinamen und Link-Syntax folgen Obsidian-Konventionen (`[[Page Name]]`).
- **Status:** final

### [ENT-004] Telegram als primärer Input-Kanal
- **Entschieden:** 2026-04-15 (Session 001)
- **Entscheidung:** User-Inputs laufen via Telegram-Bot in die Pipeline.
- **Begründung:** Auf allen Geräten verfügbar; Audio-, Text-, Bild-Support out-of-the-box; Nutzer verwendet es täglich.
- **Auswirkung:** `bot.py` ist der Entry-Point. UI-Ebenen 1–3 (Buttons / Conversation / Mini Apps) sind in ARCHITECTURE.md §7 spezifiziert.
- **Status:** final

### [ENT-005] Schema v0.3: Entitäts-Ontologie
- **Entschieden:** 2026-04-17 (Session 003)
- **Entscheidung:** Sechs Kern-Entitäten: `PersonalFact`, `VocabEntry`, `CulturalEntry`, `LanguageBridge`, `Concept`, `StyleProfile`. Später um `ServiceDefinition` (GE-001) ergänzt.
- **Begründung:** Deckt Personal-Knowledge + Spanischlernen + Stil-Meta-Ebene ab, ohne Überabstrahierung.
- **Auswirkung:** Jede Entität hat festes YAML-Frontmatter (SCHEMA.md §3). Agenten schreiben typisierte Wiki-Writes.
- **Status:** final (ergänzt durch ENT-012)

### [ENT-006] Sensitivity-Tier-Modell (Provider-Routing)
- **Entschieden:** 2026-04-17 (Session 003)
- **Entscheidung:** Jeder Fact bekommt ein `sensitivity`-Attribut: `public` → Haiku, `sensitive` → Sonnet (mit PII-Scrubbing), `private` → lokales Ollama.
- **Begründung:** Privacy-by-default für persönliche Fakten; Kosten-Optimierung für Trivialfälle; Qualität für komplexe Supervisor-Urteile.
- **Auswirkung:** `providers/` oder äquivalente Abstraktion wählt Modell per Tier. Siehe ARCHITECTURE.md §5.
- **Status:** final

### [ENT-007] Draft → Master Git-Workflow für LLM-Writes
- **Entschieden:** 2026-04-17 (Session 003)
- **Entscheidung:** Agent-Writes landen zuerst im `draft`-Branch; Merge in `master` nur nach Lint + (optionaler) User-Freigabe.
- **Begründung:** LLM-Halluzinationen dürfen den produktiven Graphen nicht direkt verunreinigen. Obsidian liest `master`.
- **Auswirkung:** `graph_writer.py` hat Draft/Prod-Modus. Ein Konflikt-Trigger erzeugt Freigabe-Prompt im Telegram-Bot.
- **Status:** final

### [ENT-008] story_score: vierdimensionales Scoring-Modell
- **Entschieden:** 2026-04-16 (Session 002, COMP_DIARY.md §3)
- **Entscheidung:** Jede PersonalFact erhält einen `story_score` 1–5 basierend auf vier Dimensionen: Originalität, Erzählpotential, Lernpotential, Pointe-Qualität.
- **Begründung:** Trennschärfe zwischen "belanglos" und "erzählbar"; ermöglicht Priorisierung für Elaboration und Story-Lab.
- **Auswirkung:** `DiaryAgent` ruft Scoring-Prompt + separate Pointe-Mini-Prompt. Werte werden in Frontmatter persistiert.
- **Status:** final

### [ENT-009] Elaboration-Pipeline mit 3 Status
- **Entschieden:** 2026-04-16 (Session 002, COMP_DIARY.md §4)
- **Entscheidung:** Facts durchlaufen `raw → elaborated → practiced`. Elaboration (Ausarbeitung) wird bei `story_score ≥ 4` automatisch ausgelöst.
- **Begründung:** Nicht jeder Fact verdient LLM-Ausarbeitung. Hohe Story-Scores profitieren am meisten.
- **Auswirkung:** Scheduler triggert Elaboration-Prompt. `practice_log` trackt Story-Lab-Übungen.
- **Status:** final

### [ENT-010] Korrelations-Engine
- **Entschieden:** 2026-04-16 (Session 002, COMP_DIARY.md §5)
- **Entscheidung:** Wenn ≥3 semantisch verwandte Facts auftreten, erzeugt der `LintAgent` automatisch eine `Concept`-Seite als Cluster-Überschrift.
- **Begründung:** Bottom-up-Emergenz von Themen — Nutzer muss keine Hierarchie vordenken.
- **Auswirkung:** Wöchentlicher Korrelations-Scan; Sonnet-Prompt für Cluster-Labelling.
- **Status:** final

### [ENT-011] Bootstrap-Interview mit 10 Fragen
- **Entschieden:** 2026-04-16 (Session 002, COMP_DIARY.md §2)
- **Entscheidung:** Neuer Nutzer durchläuft beim Erststart 10 fest definierte Lebenskontext-Fragen; Antworten werden als `PersonalFact`s mit `source: bootstrap` persistiert.
- **Begründung:** Kaltstart-Problem: Korrelationen und Kontext-Treffer werden erst mit ≥ 20 Facts sinnvoll.
- **Auswirkung:** Eigener ConversationHandler in `bot.py`; Fragen-Katalog in COMP_DIARY §2.2.
- **Status:** final

---

## Implementation (Sessions 004–006)

### [ENT-012] GE-001: ServiceDefinition als eigenständige Entität
- **Entschieden:** 2026-04-17 (Session 004, doc/COMP_SERVICES.md)
- **Entscheidung:** Dienstleistungen (Workshops, Kurse, Services) werden als eigene Entität `ServiceDefinition` modelliert, nicht als PersonalFact.
- **Begründung:** Services haben eigene Struktur (Anbieter, Zielgruppe, Ablauf, Preise). PersonalFact-Schema würde explodieren.
- **Auswirkung:** Eigenes YAML-Schema; eigener Agent-Flow. **Revidiert** in Scope durch ENT-026 (Phase 3).
- **Status:** final (Modell), Scope revidiert

### [ENT-013] Supervisor-Pipeline dreistufig
- **Entschieden:** 2026-04-17 (Session 005, ARCHITECTURE.md §3)
- **Entscheidung:** Supervisor läuft in 3 Phasen: `classify` (Intent) → `graph_context` (relevante Seiten) → `route` (Agent-Wahl + Gate-Entscheidung).
- **Begründung:** Klare Trennung von Intent-Erkennung, Kontext-Beschaffung und Routing macht Supervisor testbar und debugbar.
- **Auswirkung:** Drei Nodes in `main_workflow.py`. Supervisor-State enthält `intent`, `graph_context`, `decision`.
- **Status:** final

### [ENT-014] Agent-Set festgelegt
- **Entschieden:** 2026-04-17 (Session 005)
- **Entscheidung:** Vier Kern-Agenten: `IngestionAgent` (Parsing), `DiaryAgent` (PersonalFacts + Story-Lab), `LanguageAgent` (VocabEntries), `LintAgent` (Graph-Hygiene). Supervisor-Layer davor.
- **Begründung:** Domain-Separation: Sprache ≠ Tagebuch ≠ Housekeeping.
- **Auswirkung:** Ordner `agents/` mit einer Datei pro Agent.
- **Status:** final

### [ENT-015] main_workflow.py als LangGraph-Einstieg
- **Entschieden:** 2026-04-17 (Session 005)
- **Entscheidung:** Einziger LangGraph-`StateGraph`-Aufbau liegt in `main_workflow.py`; `bot.py` ruft nur `workflow.invoke(state)`.
- **Begründung:** Ein Graph pro Pipeline hält Flow-Debugging lokal.
- **Auswirkung:** `bot.py` bleibt dünn; `main_workflow.py` ist Single-Source-of-Truth für Routing.
- **Status:** final

### [ENT-016] init_wiki.py — Wiki-Initialisierung
- **Entschieden:** 2026-04-18 (Session 006)
- **Entscheidung:** Ein Bootstrap-Skript legt `index.md`, `log.md` und Ordnerstruktur (`Wiki/PersonalFacts/`, etc.) an.
- **Begründung:** Reproduzierbarer Kaltstart; Tests brauchen ein frisches Wiki.
- **Auswirkung:** `scripts/init_wiki.py` existiert und wird im Test-Setup aufgerufen.
- **Status:** final

### [ENT-017] LintAgent mit Auto-Fix-Stubs
- **Entschieden:** 2026-04-18 (Session 006)
- **Entscheidung:** `LintAgent` hat Detektoren für verwaiste Seiten, fehlende Backlinks, Duplikate. Auto-Fixes sind erst als Stubs implementiert.
- **Begründung:** Detektion zuerst — damit man weiß, was repariert werden muss. Fixes in MVP-2.
- **Auswirkung:** `LintAgent._apply_auto_fixes()` sind no-ops; Technische Schuld erfasst in hinweise/technischer_hinweis.md.
- **Status:** final

### [ENT-018] Telegram UI-Ebenen gestaffelt
- **Entschieden:** 2026-04-17 (Session 005, ARCHITECTURE.md §7)
- **Entscheidung:** Drei UI-Ebenen im Bot: (1) Buttons+Polls, (2) ConversationHandler, (3) Telegram Mini Apps. Start mit Ebene 1.
- **Begründung:** Komplexität progressiv steigern; Mini Apps erst bei echtem Bedarf.
- **Auswirkung:** MVP-1 nutzt ausschließlich Ebene 1 + 2.
- **Status:** final

---

## Story-Lab, Impuls, Style (Sessions 002, 005, 006)

### [ENT-019] Impuls-Typen: 8 Kombinationen
- **Entschieden:** 2026-04-16 (Session 002, COMP_DIARY.md §7.2)
- **Entscheidung:** Impuls-System kombiniert 4 Impuls-Arten × 2 Antworttypen = 8 Muster (z.B. "Fact-Erinnerung + kurze Antwort", "Vocab-Abfrage + volle Story").
- **Begründung:** Abwechslung im täglichen Telegram-Impuls; differenzierte Auswertung pro Muster.
- **Auswirkung:** Impuls-Generator wählt Muster rotierend; `analyze_impuls_answer` schreibt differenzierte `practice_log`-Einträge.
- **Status:** final

### [ENT-020] StyleProfile mit context_profiles
- **Entschieden:** 2026-04-18 (Session 005/006, COMP_DIARY.md §8.4)
- **Entscheidung:** Nutzer hat nicht *einen* Stil, sondern mehrere kontext-abhängige Profile (z.B. "mit Freunden", "mit Fremden", "Spanisch"). `StyleProfile` enthält `context_profiles: []`.
- **Begründung:** Realistische Nutzerrealität; Story-Lab-Coaching braucht Kontext-Wahl.
- **Auswirkung:** Coaching-Trigger fragt "In welchem Kontext willst du üben?" vor Story-Lab-Start.
- **Status:** final

### [ENT-021] Style References via YouTube-Clips
- **Entschieden:** 2026-04-18 (Session 006, COMP_DIARY.md §8)
- **Entscheidung:** Nutzer kann YouTube-Clips (z.B. Chappelle-Stand-Up) als Referenz-Stil ins System einspeisen. Whisper-Transkript + LLM-Analyse erzeugt `StyleFingerprint`.
- **Begründung:** Konkrete Referenzen sind greifbarer als abstrakte Stil-Attribute.
- **Auswirkung:** `raw/style_refs/` als Input-Ordner; Extraktions-Skript.
- **Status:** final

### [ENT-022] Story-Lab: 4 Stil-Karten pro Fact
- **Entschieden:** 2026-04-18 (Session 005, COMP_DIARY.md §6.3)
- **Entscheidung:** Zu jedem story-wertigen Fact generiert das System 4 verschiedene Erzählvarianten ("Stil-Karten"), aus denen der Nutzer wählt.
- **Begründung:** Expliziter Stil-Vergleich beschleunigt Lernen.
- **Auswirkung:** Generierung in DiaryAgent, Präsentation via Telegram-Buttons.
- **Status:** final

---

## Quality Control (Session 007 → 008)

### [ENT-023] Quality-Control-Prozess etabliert
- **Entschieden:** 2026-04-18 (Session 007)
- **Entscheidung:** Nach jedem größeren Meilenstein wird ein QK-Brief mit offenen Fragen an einen spezialisierten Reviewer-Agent gereicht. Erste Runde: 7 Fragen.
- **Begründung:** Architektur-Entscheidungen verdienen externe Prüfung; verhindert Blindspots.
- **Auswirkung:** `doc/QUALITY_CONTROL_NNN.md` wird pro QK-Runde angelegt.
- **Status:** final

### [ENT-024] Audio-API-Bug → V1 ohne Ton-Coaching (QK-1)
- **Entschieden:** 2026-04-18 (Session 008, QUALITY_CONTROL_008 QK-1)
- **Entscheidung:** Da Claude API (Stand 2026-04) **kein Audio-Input** unterstützt, werden Tonalitätswerte (Enthusiasmus, Natürlichkeit, Überzeugung) aus V1 gestrichen. V1 liefert textbasierte Transkript-Analyse.
- **Begründung:** Kein Weg, die Feature mit aktuellen APIs zu bauen. Whisper liefert Transkript, Sonnet analysiert Text.
- **Auswirkung:** `TonalReport` → `TranscriptQualityReport`. Doku-Stellen in S011 vollständig nachgezogen (INK-004/005/006/007); Code (`agents/`) enthielt keine entsprechenden Symbole.
- **Status:** final

### [ENT-025] MVP dreistufig: MVP-0 / MVP-1 / MVP-2 (QK-2)
- **Entschieden:** 2026-04-18 (Session 008, QK-2)
- **Entscheidung:**
  - **MVP-0:** Pipeline-Mechanik läuft (Ollama-basiert, Test-Script)
  - **MVP-1:** Echter Text-Ingest via Telegram (Claude API nötig)
  - **MVP-2:** Voice + Anki + Lint-Auto-Fixes
- **Begründung:** Klare Schnitte; ermöglicht frühe Validierung ohne API-Kosten.
- **Auswirkung:** Alle Session-Briefs referenzieren diese Stufen. MVP-0 in Session 009 erreicht.
- **Status:** final

### [ENT-026] COMP_SERVICES auf Phase 3 (QK-3)
- **Entschieden:** 2026-04-18 (Session 008, QK-3)
- **Entscheidung:** Der ServiceDefinition-Workflow (GE-001) wird erst **nach MVP-1** (also in Phase 3 / MVP-2 oder später) implementiert.
- **Begründung:** Kein klarer Nutzer-Trigger vor MVP-1. Scope-Schutz.
- **Auswirkung:** COMP_SERVICES.md Status-Zeile muss aktualisiert werden (siehe INK-008).
- **Status:** final

### [ENT-027] graph_reader zweiphasig (QK-4)
- **Entschieden:** 2026-04-18 (Session 008, QK-4)
- **Entscheidung:** Phase 1: einfacher Tag-Overlap-Matcher über `index.md`. Phase 2: SQLite + FTS5. Umschaltung bei **≥ 30 Wiki-Seiten** automatisch.
- **Begründung:** Tag-Overlap reicht für kleine Graphen; FTS5 wird erst bei Volumen nötig.
- **Auswirkung:** `agents/graph_reader.py` hat zwei Pfade; Threshold als Konstante.
- **Status:** final

### [ENT-028] Ollama-Modell `llama3.2` als Default (QK-5)
- **Entschieden:** 2026-04-18 (Session 008, QK-5)
- **Entscheidung:** Für `sensitivity: private` wird standardmäßig `llama3.2` verwendet. `mistral` bleibt Fallback-Option.
- **Begründung:** `llama3.2` ist performant auf Consumer-Hardware und liefert akzeptable Qualität für Privacy-Tier-Facts.
- **Auswirkung:** `.env` Default setzen. Siehe INK-010 (SCHEMA.md-Ecke muss aktualisiert werden).
- **Status:** final

### [ENT-029] "both"-Intent via LangGraph Send() (QK-6)
- **Entschieden:** 2026-04-18 (Session 008, QK-6)
- **Entscheidung:** Bei `intent="both"` (Ingest löst DiaryAgent **und** LanguageAgent aus) wird LangGraph `Send()` für parallele Node-Ausführung genutzt.
- **Begründung:** Blockierendes Sequenzial würde Laufzeit verdoppeln; Parallel ist semantisch korrekt.
- **Auswirkung:** Zu prüfende Schwäche: State-Merging kann `wiki_writes`-Listen überschreiben. Muss in MVP-1 mit `Annotated`-Reducern gelöst werden (siehe technischer_hinweis.md §4).
- **Status:** final, technische Schuld offen

### [ENT-030] Haiku-only-Ansatz verworfen (QK-7)
- **Entschieden:** 2026-04-18 (Session 008, QK-7)
- **Entscheidung:** Sonnet bleibt für `story_score` und Elaboration nötig. Haiku alleine wäre qualitativ unzureichend.
- **Begründung:** Haiku macht unsaubere JSON-Outputs bei Scoring; Elaboration verliert Nuance.
- **Auswirkung:** Zwei-Modell-Strategie bleibt; Kosten-Schätzung ca. <$1/Monat bei normalem Privatnutzer-Volumen.
- **Status:** final

---

## Session 009 — MVP-0

### [ENT-031] Zwei-Provider-Strategie: Claude + Ollama-Fallback
- **Entschieden:** 2026-04-19 (Session 009)
- **Entscheidung:** Jeder LLM-Aufruf versucht zuerst den konfigurierten Claude-Pfad (per sensitivity-Tier). Ohne API-Key → automatischer Fallback auf Ollama.
- **Begründung:** MVP-0 sollte ohne Kosten testbar sein; lokale Entwicklung ohne Key praktisch.
- **Auswirkung:** `test_ingest.py` läuft ohne API-Key; echter Betrieb erfordert Key weiterhin.
- **Status:** final

### [ENT-032] MVP-0 erreicht
- **Entschieden:** 2026-04-19 (Session 009)
- **Entscheidung:** Meilenstein MVP-0 formal abgeschlossen: Pipeline läuft Input → Klassifikation → DiaryAgent → Supervisor → WikiWrite mit `story_score: 5`.
- **Begründung:** Alle 4 Architekturfehler aus QK-Review behoben (P1-P4); Dry-Run grün.
- **Auswirkung:** Nächste Session startet MVP-1-Scope.
- **Status:** final

### [ENT-033] Python 3.14 als Runtime (mit Risiko)
- **Entschieden:** 2026-04-19 (Session 009, technischer_hinweis.md §3)
- **Entscheidung:** Entwicklung erfolgt auf Python 3.14.
- **Begründung:** Neueste Version; läuft derzeit.
- **Auswirkung:** Fallback-Empfehlung bei pip-Problemen: Downgrade auf 3.11/3.12.
- **Status:** final, Risiko dokumentiert

### [ENT-034] Bug-Fixes P1–P4 aus QK-Review
- **Entschieden:** 2026-04-19 (Session 009)
- **Entscheidung:** Die vier von der QK identifizierten Architekturfehler wurden in Session 009 repariert (Details in sessions/009).
- **Begründung:** Blockieren MVP-0 ohne Fix.
- **Auswirkung:** Kein Rework in MVP-1 nötig.
- **Status:** final

### [ENT-035] Engineer→PO Handover-Dokument
- **Entschieden:** 2026-04-19 (Session 009)
- **Entscheidung:** Am Ende jeder Engineering-Session schreibt der Engineer einen technischen Hinweis-Brief an den Product Owner (`hinweise/technischer_hinweis.md`).
- **Begründung:** Explizite Übergabe; versteckt keine technischen Risiken in Session-Protokoll.
- **Auswirkung:** PO liest diesen Brief als erstes bei PO-Sessions.
- **Status:** final

---

## Session 010 — PO-Review

### [ENT-036] doc/-Struktur bleibt flach
- **Entschieden:** 2026-04-19 (Session 010)
- **Entscheidung:** Keine Unterordner in `doc/`. Alle Dateien bleiben flach; Dateinamen selbsterklärend (`COMP_*.md`, `*_CONTROL_*.md`).
- **Begründung:** Mit aktuell ~10 Dateien ist Hierarchie Overkill. Flacher Namensraum ist in Obsidian einfacher zu verlinken. Umbenennungsaufwand (Link-Updates) nicht gerechtfertigt.
- **Auswirkung:** Keine Bewegung von Dateien; nur Überbleibsel werden ausgelagert (ENT-037).
- **Status:** final

### [ENT-037] Überbleibsel-Dateien → hinweise/archiv/
- **Entschieden:** 2026-04-19 (Session 010)
- **Entscheidung:** `doc/prompt.md`, `doc/start.md`, `doc/NEXT_SESSION_PROMPT.md` werden nach `hinweise/archiv/` verschoben. Inhalte bleiben als historische Referenz erhalten.
- **Begründung:** Keine Referenzen aus lebender Doku; nur historische Bedeutung.
- **Auswirkung:** `doc/` enthält nur noch aktuell wartbare Dateien. Siehe INK-011/012/013.
- **Status:** final (Umsetzung folgt nach PO-Bestätigung)

### [ENT-038] MVP-1-Blocker: Anthropic API-Key
- **Entschieden:** 2026-04-19 (Session 010)
- **Entscheidung:** MVP-1 kann nicht ohne Anthropic API-Key gestartet werden. PO beschafft den Key vor Session 011.
- **Begründung:** Ollama-Qualität reicht nicht für story_score-Kalibrierung und Supervisor-Entscheidungen in echtem Betrieb.
- **Auswirkung:** Session 011 hängt an Key-Beschaffung. Erwartete Kosten <$1/Monat.
- **Status:** offen (Beschaffung ausstehend)

---

## Session 015 — Team-Meeting UX-Radar (2026-04-19)

### [ENT-040] I1 (Inhaltliche Bestätigung): in MVP-1-Scope aufgenommen
- **Entschieden:** 2026-04-19 (Session 015, PO-Beschluss)
- **Entscheidung:** I1 wird in den MVP-1-Scope aufgenommen — Umsetzung **nach Phase-6-Abschluss**, inline innerhalb der Phase-6-Session, keine eigene Implementierungs-Session.
- **Begründung:** Macht den Qualitätsunterschied zwischen Ollama- und Claude-Lauf für den Nutzer unmittelbar sichtbar. Kein Schema-Impact, kein neuer LLM-Call — reine Python-Formatierung auf existierenden State-Feldern (`graph_context`, `wiki_writes`, `story_score`).
- **Auswirkung:** [bot.py:123-124](../bot.py#L123-L124) — statt `w["path"].split("/")[-1]` wird ein Title + story_score + 1-Zeile-graph_context-Render ausgegeben. Implementierung: Architekt in Phase 6.
- **Status:** beschlossen, Umsetzung ausstehend (nach Phase 6)

### [ENT-041] I6 (Menschlichere Fehler): in MVP-1-Scope aufgenommen
- **Entschieden:** 2026-04-19 (Session 015, PO-Beschluss)
- **Entscheidung:** I6 wird in den MVP-1-Scope aufgenommen — Umsetzung **nach Phase-6-Abschluss**, inline in Phase-6-Session.
- **Begründung:** `⚠️ Systemfehler. Log geprüft.` ist funktional korrekt, aber uneinladend. Reine Formatierungsänderung ohne Kosten-Impact; Exception weiterhin vollständig ins Log.
- **Auswirkung:** [bot.py:131-133](../bot.py#L131-L133) + [bot.py:261-265](../bot.py#L261-L265) — menschlichere Fehlermeldung + InlineKeyboard mit "Nochmal versuchen" / "Details" / "Egal". QM: Exception bleibt im Log, Nutzermeldung wird handlungsorientiert.
- **Status:** beschlossen, Umsetzung ausstehend (nach Phase 6)

### [ENT-042] UX-Radar I1–I10: Klassifikation offiziell bestätigt
- **Entschieden:** 2026-04-19 (Session 015, Team-Beschluss)
- **Entscheidung:** Die von der UX-Kollegin vorgeschlagene Einteilung der zehn Radar-Ideen wird unverändert bestätigt: I1+I6 als MVP-1-Politur (nach Phase 6), I2 bei reproduzierbarem `intent=ambiguous`, I3/I4/I5/I8 frühestens MVP-2, I7 erst mit Update-Pfad in LangGraph, I9 nur bei belegtem Mobile-Schmerz, I10 nach ≥5 realen Bootstraps.
- **Begründung:** UX-Einteilung ist konservativ und projektkonform. Expliziter Beschluss verhindert, dass der Radar im Limbo bleibt.
- **Auswirkung:** [sessions_ux/ux_001_initial-radar.md](../sessions_ux/ux_001_initial-radar.md) gilt als offiziell klassifiziert. Keine Idee außerhalb der beschlossenen Einordnung vorzuziehen ohne neuen PO-Beschluss.
- **Status:** final

### [ENT-043] `telegram_state`-Architektur: Option A (Feld in `user_profile.md`)
- **Entschieden:** 2026-04-19 (Session 015, Architekt-Empfehlung, PO bestätigt)
- **Entscheidung:** Wenn I4 (Pinned Dashboard) oder I5 (Morgen-Kaffee) implementiert werden, wird persistenter Telegram-Zustand als dedizierter `telegram_state:`-YAML-Block am Ende von `user_profile.md` gespeichert — klar von persönlichen Facts getrennt.
- **Begründung:** Graph-nativ, kein neuer Artefakt-Typ, ein einziger Integer (Pinned-Message-ID) oder kleines YAML-Block belastet die Datei nicht merklich. Option B (eigene `.state/`-Datei) würde einen neuen Artefakt-Typ einführen, der nicht in Obsidian navigierbar wäre.
- **Auswirkung:** Gilt als Richtlinie für UX-Ausarbeitung (I4/I5). Kein Code-Impact heute — I4/I5 sind frühestens MVP-2 (ENT-042).
- **Status:** final (Architektur-Präferenz, Umsetzung erst bei I4/I5)

---

### [ENT-039] Branch-Namen-Konvention: `master` vs. `main`
- **Entschieden:** 2026-04-20 (Session 011, Nutzer-Entscheidung)
- **Entscheidung:** `master` bleibt. PO-Empfehlung (Umbenennung zu `main`) wurde verworfen — bestehende Briefe und Doku-Stellen ziehen auf `master` nach.
- **Begründung:** Vermeidet einmaligen Remote-Umbenennungsaufwand und Default-Branch-Umstellung; Doku-Korrektur war ohnehin nötig (INK-014).
- **Auswirkung:** Sessions 008/009, ARCHITECTURE §8, COMP_DIARY §2.4, ENT-007 und SESSION_ZUSAMMENFASSUNG auf `master` korrigiert. Zukünftige Briefs nennen ausschließlich `master`.
- **Status:** final

---

## Session 019 — MVP-2-Kickoff (2026-04-20)

### [ENT-044] MVP-2 Erstes Feature: Voice-Ingest
- **Entschieden:** 2026-04-20 (Session 019, PO-Beschluss nach Nutzer-Bestätigung "Voice=ja")
- **Entscheidung:** Erstes MVP-2-Feature ist **Voice-Ingest** (Sprachnachricht → Whisper-Transkript → Ingest-Pipeline). Anki-Export wandert auf MVP-2-Zweitwelle und wird nach Voice-Ingest-Abnahme geplant.
- **Begründung:** Nutzer schickt regelmäßig Sprachnachrichten an Telegram (PO-Rückfrage in S019 bestätigt). `agents/extractors/audio_extractor.py` ist bereits implementiert (faster-whisper, lokal, kostenlos); `faster-whisper>=1.0.0` steht in `requirements.txt`; bot.py-Voice-Handler ruft `_extractor.extract(dest)` korrekt auf — d.h. kein Neu-Bau, sondern **Verify + Iterate** (Echtfehler-Test, Sprach-Detection DE/ES, lange Nachrichten, Hintergrund). Aufwand deutlich kleiner als im Session-018-Brief (2–3h) geschätzt — eher 1–2h + Edge-Cases.
- **Auswirkung:** Architekt prüft in Session 020 den vollständigen Voice-Pfad end-to-end. Whisper-Modell "small" (CPU/int8) bleibt Default; kein API-Call, keine zusätzlichen Kosten. Anki-Export (Platzhalter in `language_agent.schedule_anki`) bleibt in MVP-2 im Scope, aber als Zweitwelle nach Voice-Abnahme.
- **Status:** beschlossen, Umsetzung ausstehend (Session 020)

### [ENT-045] Proaktiver Kanal: grundsätzlich freigegeben, opt-in
- **Entschieden:** 2026-04-20 (Session 019, PO-Beschluss)
- **Entscheidung:** Der Bot darf **unaufgefordert Nachrichten senden**, sobald I5 (Morgen-Kaffee) oder ENT-019-Impulse implementiert werden — aber nur unter vier nicht-verhandelbaren Bedingungen: (1) **Opt-in** per expliziter Nutzerwahl (kein Default-An), (2) **24h-TTL** pro Impuls (unbeantwortete Impulse werden verworfen, nicht gestapelt), (3) **Pausier-Kommando** (z.B. `/pause 7d`) ohne Friction, (4) **Haiku-only** für Impuls-Generierung zur Kosten-Eindämmung.
- **Begründung:** CHANCEN §1.4 und §2.3 — das System ist konzeptuell zweiseitig; ein reiner Postkasten verschenkt die "Gewohnheit-stapeln"-Wirkung. Aber UX-Radar §3.2 I5 mahnt ausdrücklich: "Ritual muss Nein können". Die vier Bedingungen übersetzen das in Policy.
- **Auswirkung:** Gilt als Rahmen für alle zukünftigen proaktiven Features (ENT-019 Impulse, I4 Pinned Dashboard, I5 Morgen-Kaffee). Scheduler-Implementierung ist Architektur-Entscheidung (APScheduler im Bot-Prozess vs. externer Cron) — nicht hier festgelegt.
- **Status:** final (Policy), konkrete Implementierung erst bei Feature-Trigger

### [ENT-046] UX-Radar-Dokumentationsform: ENT-Einträge in ENTSCHEIDUNGEN.md
- **Entschieden:** 2026-04-20 (Session 019, PO-Beschluss zu E3 aus S018-Brief)
- **Entscheidung:** Beschlüsse zu UX-Radar-Ideen werden ausschließlich als ENT-Einträge in `doc/ENTSCHEIDUNGEN.md` dokumentiert. Der UX-Radar (`sessions_ux/ux_001_initial-radar.md`) bleibt **unverändert als Radar** — nichts wird dort inline ergänzt. Kein separates `ux_001_po-response.md`.
- **Begründung:** ENT-040/041/042/043 haben bereits demonstriert, dass ENT-Einträge der richtige Ort sind — sie sind numeriert, stabil, chronologisch und themen-indiziert. Ein zweites Dokument wäre Doppelspur. Das PO-Rollenprofil verlangt explizit "ENT-* Stabilität" als nicht-verhandelbares Prinzip — alles andere würde das unterlaufen.
- **Auswirkung:** Zukünftige UX-Radare (ux_002, ux_003, ...) werden genauso behandelt: Radar bleibt Radar, Beschlüsse wandern nach ENT-NNN mit expliziter Rück-Referenz auf die Radar-ID.
- **Status:** final
