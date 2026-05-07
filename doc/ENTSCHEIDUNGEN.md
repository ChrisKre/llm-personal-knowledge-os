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
| Routing | ENT-029, ENT-047, ENT-048 |
| Prozess & Dokumentation | ENT-023, ENT-034, ENT-035, ENT-036, ENT-037, ENT-046 |
| UX-Radar / Telegram-UX | ENT-040, ENT-041, ENT-042, ENT-043, ENT-045, ENT-049 |
| Anki-Export (MVP-2-Zweitwelle) | ENT-050, ENT-051, ENT-052 |
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

---

## Session 020 — MVP-2 Voice-Trocken-Test + Vocab-Policy (2026-04-22)

### [ENT-047] VocabEntry-Hint-Gate: Extraktion nur bei Hint oder deutsch-dominantem Input
- **Entschieden:** 2026-04-22 (Session 020, PO-Beschluss nach Architekt-Eskalation [020a_eskalation_es-vocab.md](../sessions/020a_eskalation_es-vocab.md))
- **Entscheidung:** LanguageAgent erzeugt VocabEntries + LanguageBridges nur wenn **eine** der beiden Bedingungen zutrifft:
  1. `user_hint` enthält `#vocab` **oder** `vokabel` (case-insensitive Substring), **oder**
  2. `raw_event.language_detected == "de"` (deutsch-dominanter Input — bestehendes Verhalten, extrahiert eingestreute Fremdwörter).

  Bei reinen Fremdsprach-Inputs (`language_detected == "es"` o.ä.) ohne Hint: Intent wird im Supervisor von `both`/`vocab` auf `personal_fact` **downgedowngradet** — der Input landet als "hat Spanisch geübt"-Fact, nicht als Vokabel-Flut. Gate sitzt auf Routing-Ebene in [agents/supervisor.py](../agents/supervisor.py), nicht in `language_agent.py` — spart damit auch die parallele `both`-Send-Last.
- **Begründung:** Dry-Run-Messung in Session 020 ([020a §Konkrete Daten](../sessions/020a_eskalation_es-vocab.md)) auf einer 9-Sekunden-ES-Voice ("Hoy aprendí una palabra nueva en español, madrugada..."): **15 VocabEntries + 6 Bridges** — überwiegend Funktionswörter (`la`, `en`, `del`, `una`, `hoy`). Kosten: ~$0.15/Voice → bei 1–3 ES-Voices/Tag = **$4.50–13.50/Monat** = 45–270% des $5–10-Monatsbudgets ([ENT-033](../doc/ENTSCHEIDUNGEN.md)). Zusätzlich: 22 Wiki-Dateien pro Nachricht, demoralisierende I1-Bestätigung ("22 Seiten erstellt — la, en, del…"), Anki-Kartenflut sobald MVP-2-Zweitwelle ([ENT-044](../doc/ENTSCHEIDUNGEN.md)) aktiv wird. Die Hint-Regel spiegelt den realen Lern-Workflow: spontan Sprache üben ≠ Vokabel festhalten. Verworfene Alternativen: Stopword-Filter + Hard-Cap (DE/EN/ES-Listen-Wartung, arbiträrer Cap); neuer `language_practice`-Intent (zu viel Chirurgie ohne Nutzungsdaten — kann später nachgeholt werden); Bug akzeptieren (Budget- und Vertrauensrisiko zu hoch).
- **Auswirkung:** Architekt setzt um in Session 021: Gate in [agents/supervisor.py:71-103](../agents/supervisor.py#L71-L103) (~10 Zeilen), nutzt erstmals das bislang ungenutzte `language_detected`-Feld (räumt Befund #1 aus 020a mit ab). Hint-Matching: case-insensitive Substring, nichts weiter (`#vocab` / `vokabel`) — Erweiterungen erst nach Live-Evidenz. Keine zusätzlichen LLM-Calls, keine Schema-Änderung, kein neuer Agent. Bereits vermüllte Vokabeln in `wiki/language/vocab/` (15 ES-Funktionswörter vom 2026-04-21, siehe [log.md](../log.md)) werden in Session 021 aufgeräumt. Für MVP-2-Zweitwelle (Anki-Export) ist diese Policy Voraussetzung.
- **Status:** beschlossen, Umsetzung ausstehend (Session 021)

---

## Session 021 — PO-Freigabe (2026-05-04)

### [ENT-048] ENT-047-Auslegung: Hint-Gate nur bei gesetztem `language_detected`
- **Entschieden:** 2026-05-04 (PO-Antwort auf Architekt-F1 in [Session 021](../sessions/021_2026-04-22.md))
- **Entscheidung:** Das Hint-Gate aus [ENT-047](#ent-047-vocabentry-hint-gate-extraktion-nur-bei-hint-oder-deutsch-dominantem-input) feuert **ausschließlich**, wenn `raw_event.language_detected` gesetzt UND ungleich `"de"` ist. Fehlendes Feld (`None`/leer) führt **nicht** zum Downgrade — der Text-Pfad bleibt unverändert.
- **Begründung:** `language_detected` wird heute nur vom Whisper-Pfad ([ENT-044](#ent-044-mvp-2-erstes-feature-voice-ingest)) gesetzt; Text-Inputs haben das Feld leer. Eine strenge Lesart von ENT-047 würde alle DE-Text-Mixes downgraden — klarer Regressionsfall (Bsp.: Nutzer tippt "Heute Wort: ensimismado gelernt" → Vokabel würde unterdrückt). Der primäre Bug aus 020a ist die Voice-ES-Flut; die wird mit dieser Lesart vollständig gefangen. Restrisiko reines-ES-Tippen bleibt offen, aber praktisch selten und nicht das Eskalations-Triggerszenario.
- **Auswirkung:** Architekt setzt das Gate exakt mit dieser Bedingung um (Downgrade nur bei `language_detected` gesetzt UND != "de" UND kein Hint). Wenn Live-Evidenz ein Muster für reines-ES-Tippen zeigt, kommt ein Folge-ENT mit `language_detected`-Setter im Text-Pfad (z.B. `langdetect` oder Sonnet-Klassifikation). Heute nicht.
- **Status:** final

### [ENT-049] Zweit-Oberflächen-Strategie: Telegram bleibt primär, CLI/Discord/E-Mail vorgemerkt für MVP-3
- **Entschieden:** 2026-05-04 (PO-Antwort auf [UX-Radar 002](../sessions_ux/ux_002_neuer-blickwinkel.md), Feedback in [sessions_ux/feedback_001.md](../sessions_ux/feedback_001.md))
- **Entscheidung:** Telegram bleibt einziger primärer Eingabe- und Ausgabe-Kanal in MVP-1/MVP-2 ([ENT-004](#ent-004-telegram-als-primärer-input-kanal) bestätigt). Drei Zweit-Oberflächen werden formal **vorgemerkt**, aber **nicht jetzt** gezogen:
  1. **CLI-Companion** (`pks <text>`): Inbound-Desktop, ~1–2 Tage Aufwand, ruft `run_ingest` direkt. Frühestens MVP-3, Trigger = PO-Selbstbeobachtung im Live-Betrieb.
  2. **Discord-Outbound:** reicher Render-Kanal für [ENT-045](#ent-045-proaktiver-kanal-grundsätzlich-freigegeben-opt-in)-Proaktivität (Wochen-Replay, Morgen-Kaffee, Cluster-Puls). Embeds + Reactions. Frühestens MVP-3, gekoppelt an ENT-045-Aktivierung.
  3. **E-Mail-Outbound:** Archiv-Schicht für Monats-Digest, maximale Markdown-Portabilität. Frühestens MVP-3, gekoppelt an ENT-045-Aktivierung.
- **Begründung:** [UX-Radar 002](../sessions_ux/ux_002_neuer-blickwinkel.md) belegt: Telegram-Voice-Ingest ist heute Kern-Use-Case ([ENT-044](#ent-044-mvp-2-erstes-feature-voice-ingest)) und wird von keinem Kandidaten besser bedient — Discord schwächt Voice-Ingest, Obsidian-Plugin zwingt Hintergrund-Daemon, Web-App sprengt Budget. Die drei vorgemerkten Adapter sind **strikt parallel** — kein Lock-in, kein Schema-Impact, kein Bruch des WikiWrite-Vertrags. Vormerkung verhindert, dass die Frage in 6 Monaten von vorne diskutiert werden muss. Verworfene/nicht-vorgemerkte Kandidaten (Web-App, Obsidian-Plugin, Raycast als eigener Pfad, VS-Code, Browser-Extension, Apple Shortcuts, Slack) bleiben im Radar mit dokumentiertem Verdict — kein Pin.
- **Auswirkung:** UX ergänzt einen `📌 MVP-3-Vormerkung`-Anhang am Ende von [ux_002_neuer-blickwinkel.md](../sessions_ux/ux_002_neuer-blickwinkel.md) mit der Triade CLI/Discord/E-Mail. Kein Code-Impact, kein Architekt-Auftrag heute. Bei ENT-045-Implementierung ist Discord-Outbound der Default-Render-Kandidat fürs Wochen-Replay. CLI-Companion läuft unabhängig — wird aktiviert, sobald Desktop-Ingest spürbares Schmerzbild zeigt.
- **Status:** final (Strategie-Vormerkung), Umsetzung gekoppelt an ENT-045 bzw. PO-Trigger

---

## Session 022 — Anki-Export-Kickoff (2026-05-07)
> MVP-2-Zweitwelle. PO-Beschlüsse zur Anki-Export-Architektur. Voraussetzung: [ENT-047](#ent-047-vocabentry-hint-gate-extraktion-nur-bei-hint-oder-deutsch-dominantem-input)/[ENT-048](#ent-048-ent-047-auslegung-hint-gate-nur-bei-gesetztem-language_detected) live (Wiki ist sauber). Keine Code-Lieferung in S022 — Architekt setzt in S023 um.

### [ENT-050] Anki-Export: Scope, Quell-Selektion, Trigger, Format
- **Entschieden:** 2026-05-07 (Session 022, PO-Beschluss — MVP-2-Zweitwelle-Kickoff)
- **Entscheidung:** Anki-Export ist ein **on-demand-Output-Pfad**, kein automatischer Hook am Wiki-Write. Konkrete Festlegungen:
  1. **Quell-Selektion:** Eine Anki-Karte pro `VocabEntry` mit `status: elaborated`. `status: raw` wird übersprungen (unfertig). `status: practiced` wird ebenfalls exportiert (sobald SRS-Lebenszyklus eingeführt ist — heute existiert noch keiner).
  2. **Bridges werden NICHT exportiert** — siehe [ENT-051](#ent-051-anki-card-schema-front-back-tags) für Begründung.
  3. **Kein PersonalFact-Verlinkungs-Filter** — alle elaborierten VocabEntries fliegen mit. Manuelle Markierung via Hint ist nicht nötig: das Hint-Gate aus [ENT-047](#ent-047-vocabentry-hint-gate-extraktion-nur-bei-hint-oder-deutsch-dominantem-input) sorgt bereits dafür, dass nur intentional erfasste Vokabeln in `wiki/language/vocab/` landen.
  4. **Trigger:** CLI on-demand. Vorschlag (Architekt mag den finalen Pfad wählen): `python scripts/export_anki.py [--out PATH] [--since YYYY-MM-DD]`. Kein Hook am `graph_writer`, kein Scheduler. Passt zu [ENT-049](#ent-049-zweit-oberflächen-strategie-telegram-bleibt-primär-cli-discord-e-mail-vorgemerkt-für-mvp-3): Anki-Export ist kein Input-Kanal, sondern ein Output-Pfad — CLI ist legitim, auch wenn ENT-049 CLI-Inbound für MVP-3 markiert.
  5. **Format:** `.apkg`-Paket via [genanki](https://github.com/kerrickstaley/genanki). Begründet: Single-Datei-Import-Erfahrung in Anki, native GUID-Unterstützung (Voraussetzung für [ENT-052](#ent-052-anki-card-identität-und-re-export-stabilität)), Python-nativ, kein Server. CSV-Alternative wäre primitiver, aber ohne stabile GUIDs — Re-Export-Pfad würde brechen.
  6. **Deck-Struktur:** Ein Deck `PKS::Sprachen::Spanisch::Vokabeln`. Mehrsprachigkeit ist heute nicht nötig (nur ES) — wenn EN/andere Sprachen dazukommen, kommt eine Erweiterungs-ENT.
- **Begründung:** Single-User-System, Wiki ist Source-of-Truth, Anki ist Lern-Adapter. On-demand-Trigger erlaubt dem Nutzer, Export-Zeitpunkte selbst zu kontrollieren (z.B. wöchentlich). Kein automatischer Hook = keine versehentliche SRS-State-Verwirrung durch Halb-fertige `raw`-Karten. `status: elaborated` als Filter ist die Qualitätsschwelle: Eselsbrücke + Beispielsätze sind das, was eine Karte lernwert macht — `raw` hätte beides nicht.
- **Auswirkung:** Architekt setzt in Session 023 um. Aufwand: ~1 Tag Skript + Tests. Neue Dependency: `genanki` (in `requirements.txt` aufnehmen). **Kein Schema-Impact** — der `anki_id`-Slot existiert bereits im VocabEntry-Frontmatter ([ENT-005](#ent-005-schema-v03-entitäts-ontologie)) und wird in [ENT-052](#ent-052-anki-card-identität-und-re-export-stabilität) befüllt. **Kein LLM-Call**, **kein Budget-Impact** — reines Markdown-Parsen + Datei-Generierung.
- **Status:** beschlossen, Umsetzung ausstehend (Session 023)

---

### [ENT-051] Anki-Card-Schema: Front, Back, Tags
- **Entschieden:** 2026-05-07 (Session 022, PO-Beschluss)
- **Entscheidung:** Card-Felder werden aus dem `VocabEntry`-Markdown deterministisch gerendert:
  - **Front:** ES-Wort (z.B. `madrugada`). **Genus-Präfix** (`la`/`el`) wenn aus `## Grammatik > Genus` parsbar (z.B. `la madrugada`, `el duende`). Wenn nicht parsbar: Wort allein. **Keine Difficulty auf Front** — gehört auf Tag.
  - **Back:**
    1. DE-Übersetzung (erster Eintrag aus `## Übersetzungen > **DE:**`).
    2. **Erster** Beispielsatz aus `## Beispielsätze` (kontextueller Lernanker, fett gehoben).
    3. Eselsbrücke aus `## Eselsbrücke` (volle Übernahme — sie ist der individuell wertvollste Teil und meist 2–4 Zeilen lang).
  - **Tags:**
    - 1:1 aus dem Frontmatter-`tags`-Array.
    - Plus `language::es` (für Filter in Anki).
    - Plus CEFR-Niveau (`difficulty::B1`, `difficulty::C1` etc.) aus dem Frontmatter-Feld `difficulty`. **CEFR ersetzt einen `story_score`-Tag** — VocabEntries haben per [ENT-008](#ent-008-story_score-vierdimensionales-scoring-modell) keinen `story_score` (das ist PersonalFact-only).
- **Bridges nicht in Karte:** Eine `LanguageBridge` ist kontrastives Wiki-Wissen (z.B. „flamenco/Flamenco ist ein Cognate") — sie hat keinen sinnvollen Front/Back-Schnitt für Karteikarten. Wer mehr Kontext zu einem Wort will, klickt vom Anki-Back den Obsidian-Link zur VocabEntry-Datei (siehe ENT-052: optionaler Obsidian-Backlink im Back-Feld). Brücken-Export wäre ein nachgeschobenes Feature, das den Lerner nicht durch SRS lernt, sondern Kontext-Refresh ist — nicht Scope MVP-2.
- **Begründung:** Karteikarten sollen sehr fokussiert sein — *eine* Bedeutung vorne, *ein* Beispiel + Eselsbrücke hinten. Mehrere Beispielsätze auf der Karte verwässern die Recall-Präzision; sie bleiben in Obsidian erreichbar. Die Eselsbrücke ist handgeschmiedet pro Wort (LLM-elaboriert) und damit der individuellste Lernhebel — sie gehört unbedingt auf die Karte. CEFR-Tag erlaubt dem Nutzer in Anki, gezielt B1-Karten oder C1-Karten zu üben (Niveau-Filter ist in Anki ein häufiger Workflow).
- **Auswirkung:** Architekt entscheidet, ob Genus-Parsing aus Markdown-Body machbar/robust ist — wenn fragil, ist Front = Wort allein akzeptabel (kein Eskalations-Trigger). Tags werden 1:1 ausgegeben (Anki erlaubt Multi-Word-Tags mit Unterstrich, also `Spanisch-Kultur` → `Spanisch-Kultur`). Wenn ein Frontmatter-Feld fehlt (z.B. `difficulty: null` in einer alten Datei), wird der entsprechende Tag schlicht weggelassen — kein Fehler, kein Default-Fallback.
- **Status:** beschlossen, Umsetzung ausstehend (Session 023)

---

### [ENT-052] Anki-Card-Identität und Re-Export-Stabilität
- **Entschieden:** 2026-05-07 (Session 022, PO-Beschluss)
- **Entscheidung:** Stabile Karten-GUIDs via `anki_id`-Frontmatter-Slot — der existiert bereits in [ENT-005](#ent-005-schema-v03-entitäts-ontologie):
  1. **Erster Export einer Karte:** Skript generiert eine deterministische GUID aus dem Wiki-Slug: `sha1("pks-vocab-" + slug).hexdigest()[:16]` (z.B. für `v_es_madrugada` → fester 16-Zeichen-String). Wert wird in das `anki_id`-Frontmatter-Feld der `.md`-Datei zurückgeschrieben. Genanki nutzt diesen Wert als `Note.guid`.
  2. **Re-Export einer bereits exportierten Karte:** `anki_id` ist bereits gesetzt → Skript liest und wiederverwendet ihn. Anki erkennt die Karte am GUID und **überschreibt Front/Back/Tags**. **SRS-State (Intervall, Ease, Lapses) bleibt vollständig erhalten** — das ist die zentrale Eigenschaft, die genanki über `Note.guid` garantiert.
  3. **Wiki-Datei wird umbenannt** (z.B. Slug-Korrektur): `anki_id` bleibt im Frontmatter erhalten → der neue Slug nutzt den alten anki_id-Wert → Anki-Karte bleibt dieselbe. **Resilienz gegen Slug-Änderungen.**
  4. **Wiki-Datei wird gelöscht:** Skript macht in MVP-2 **keine** Aktion gegen Anki (kein Auto-Delete). Die zugehörige Anki-Karte bleibt — der Nutzer löscht manuell oder ignoriert sie. Ein optionaler `--prune`-Modus, der verwaiste Anki-Karten markiert/löscht, ist [CHANCEN]-Kandidat für MVP-3, kein Scope heute.
  5. **Eselsbrücke wird im Wiki überarbeitet:** Re-Export aktualisiert das Back-Feld in Anki, GUID bleibt → SRS-Verlauf intakt. Genau das gewünschte Verhalten.
- **Begründung:** SRS-State-Verlust ist der einzige echte Anti-Pattern-Fall im Anki-Workflow — alles andere ist reparabel. Eine deterministische GUID aus dem Slug + Persistenz im Frontmatter ist der einzige Weg, der gegen *alle* drei Veränderungs-Achsen (Inhalt, Slug, Re-Export-Reihenfolge) stabil bleibt. Genanki unterstützt das nativ via `Note.guid` ohne Workaround. Alternative (random UUIDs ohne Frontmatter-Persistenz) würde bei jedem Re-Export neue Karten erzeugen — Duplikate, SRS-Verlust. Klares NO-GO.
- **Auswirkung:** Skript schreibt in das Wiki-Frontmatter zurück (erster und einziger schreibender Output-Pfad bisher außerhalb des Agent-Flows). Architekt entscheidet, ob das mit der bestehenden Frontmatter-Schreibe-Funktion in [graph_writer.py](../graph_writer.py) wiederverwendet werden kann oder ein dedizierter `frontmatter_patch`-Helper sinnvoll ist. **Kein Konflikt mit Draft→Master-Workflow ([ENT-007](#ent-007-draft--master-git-workflow-für-llm-writes))** — die `anki_id`-Schreibung ist deterministisch, nicht-LLM, nicht-halluzinationsanfällig; ein direkter Master-Write ist gerechtfertigt. (Wenn Architekt anders sieht: eskalieren.) Optional empfohlen: Im Anki-Back-Feld einen Obsidian-Backlink (`obsidian://open?vault=repos&file=wiki/language/vocab/v_es_madrugada`) anhängen, damit der Lerner aus Anki direkt zur Wiki-Quelle springen kann — kontextueller Mehrwert ohne Zusatzkomplexität.
- **Status:** beschlossen, Umsetzung ausstehend (Session 023)
