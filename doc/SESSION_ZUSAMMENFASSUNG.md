# SESSION_ZUSAMMENFASSUNG.md — Kompakte Session-Historie
> Erstellt: Session 010 (2026-04-19) | Autor: Product Owner
> Zweck: Schneller Überblick über den Verlauf des Projekts. Für Details siehe `sessions/NNN_YYYY-MM-DD.md`.

---

## Phase 1 — Foundation (Sessions 001–003)

### Session 001 — Architektur-Grundentwurf (2026-04-15)
- **Deliverable:** Erste Version von `ARCHITECTURE.md`
- **Kernentscheidungen:** Stack (Python + LangGraph + Claude API), Karpathy-Wiki-Prinzip (kompiliertes Markdown statt RAG), Obsidian als Frontend, Telegram als Input-Kanal.
- **Wichtigste Erkenntnis:** Single-User-Knowledge-Graph muss kein Vector-Store sein. LLMs navigieren Markdown + Wiki-Links nativ — das skaliert für einen Nutzer.

### Session 002 — COMP_DIARY spezifizieren (2026-04-16)
- **Deliverable:** `COMP_DIARY.md` v0.x — Personal-Facts-Engine vollständig ausgeformt.
- **Kernentscheidungen:** `story_score` vierdimensional, Elaboration-Pipeline (raw/elaborated/practiced), Korrelations-Engine bei ≥3 verwandten Facts, Bootstrap-Interview mit 10 Fragen.
- **Wichtigste Erkenntnis:** Story-Potential ist differenzierbar (Originalität ≠ Pointe ≠ Erzählpotential). Dedizierte Pointe-Mini-Prompts liefern stabilere Werte als ein Monolith-Scoring.

### Session 003 — Schema + COMP_LANGUAGE + Scaffold (2026-04-17)
- **Deliverable:** `SCHEMA.md` v0.3 (Verfassung), `COMP_LANGUAGE.md` v0.1, initiales Code-Scaffold.
- **Kernentscheidungen:** Sechs Kern-Entitäten (PersonalFact, VocabEntry, CulturalEntry, LanguageBridge, Concept, StyleProfile), Sensitivity-Tier-Modell (public→Haiku / sensitive→Sonnet / private→Ollama), Draft→Main Git-Workflow.
- **Wichtigste Erkenntnis:** Sensitivity-Tier ist nicht nur Privacy, sondern auch Kosten-Steuerung und Provider-Routing in einem Attribut.

---

## Phase 2 — Implementation (Sessions 004–006)

### Session 004 — GE-001 & COMP_SERVICES (2026-04-17)
- **Deliverable:** `COMP_SERVICES.md` — ServiceDefinition als eigenständige Entität, erstes Gedankenexperiment (GE-001).
- **Kernentscheidungen:** Services (Workshops, Kurse) eigene Entität statt Sub-Typ von PersonalFact.
- **Wichtigste Erkenntnis:** Das Gedankenexperiment-Format (`sessions_gedankenexperiment/`) erlaubt kontrollierte Scope-Erweiterung ohne Mainline-Unterbrechung.

### Session 005 — Requirements, main_workflow, bot, DiaryAgent (2026-04-17)
- **Deliverable:** `requirements.txt`, `main_workflow.py`, `bot.py`, `agents/diary_agent.py` — erster lauffähiger Code.
- **Kernentscheidungen:** Supervisor-Pipeline dreistufig (classify → graph_context → route), Agent-Set (IngestionAgent, DiaryAgent, LanguageAgent, LintAgent), UI-Ebenen (Buttons / Conversation / Mini Apps).
- **Wichtigste Erkenntnis:** `main_workflow.py` als einziger Graph-Builder hält Routing-Logik lokal und debugbar.

### Session 006 — init_wiki, LanguageAgent, LintAgent (2026-04-18)
- **Deliverable:** `scripts/init_wiki.py`, `agents/language_agent.py`, `agents/lint_agent.py`, Story-Lab-Stil-Referenzen.
- **Kernentscheidungen:** StyleProfile mit `context_profiles` (Stil pro Kontext), Style References aus YouTube-Clips, 4 Stil-Karten pro Fact.
- **Wichtigste Erkenntnis:** Nutzer haben nicht *einen* Stil — kontext-abhängige Profile sind realitätsnäher und coaching-kompatibel.

---

## Phase 3 — Quality Control (Sessions 007–008)

### Session 007 — Quality-Control-Brief vorbereiten (2026-04-18)
- **Deliverable:** QK-Brief mit 7 Fragen an externen Reviewer-Agent.
- **Kernentscheidungen:** QK-Prozess formalisieren (nach jedem Meilenstein).
- **Wichtigste Erkenntnis:** Offene Fragen gezielt formulieren schlägt generisches "Review this" — die Qualität der Antwort hängt an der Qualität der Frage.

### Session 008 — 7 QK-Entscheidungen getroffen (2026-04-18)
- **Deliverable:** `QUALITY_CONTROL_008.md` mit 7 Entscheidungen (QK-1 bis QK-7).
- **Kernentscheidungen:**
  - **QK-1 (kritischer Bug):** Claude API unterstützt **kein Audio** — Tonalitätswerte (Enthusiasmus, Natürlichkeit, Überzeugung) aus V1 gestrichen. Story-Lab V1 ist textbasiert.
  - **QK-2:** MVP dreistufig (MVP-0 Mechanik / MVP-1 Telegram-Ingest / MVP-2 Voice+Anki+Lint).
  - **QK-3:** COMP_SERVICES auf Phase 3.
  - **QK-4:** graph_reader zweiphasig (Tag-Overlap, dann SQLite ab ≥30 Seiten).
  - **QK-5:** `llama3.2` als Private-Tier-Default.
  - **QK-6:** "both"-Intent über LangGraph `Send()` parallel.
  - **QK-7:** Haiku-only-Ansatz verworfen — Sonnet für Scoring+Elaboration nötig.
- **Wichtigste Erkenntnis:** Der Audio-API-Bug war ein stiller Feature-Killer. Ohne QK wäre V1 gegen die Wand gefahren.

---

## Phase 4 — MVP-0 (Session 009)

### Session 009 — MVP-0 erreicht (2026-04-19)
- **Deliverable:** Lauffähige Pipeline mit Ollama-Fallback, Bug-Fixes P1–P4, Engineer→PO Handover-Dokument (`hinweise/technischer_hinweis.md`).
- **Kernentscheidungen:** Zwei-Provider-Strategie (Claude + Ollama-Fallback), MVP-0 formal abgeschlossen.
- **Wichtigste Erkenntnis:** Ollama-Fallback macht das System offline-fähig und Entwicklung key-frei. Unerwartetes Privacy-Nebenprodukt: `sensitivity:private`-Facts verlassen nie das Gerät.
- **Technische Schuld offen:** LintAgent-Stubs, AnkiConnect fehlt, Bot-Error-Handling, LangGraph `Annotated`-Reducer für "both"-Routing, graph_reader Phase 2 ungetestet.

---

## Phase 5 — PO-Review (Session 010)

### Session 010 — PO-Review (2026-04-19, aktuelle Session)
- **Deliverable:** `INKONSISTENZEN.md`, `ENTSCHEIDUNGEN.md`, `SESSION_ZUSAMMENFASSUNG.md` (dieses Dokument), `CHANCEN.md`.
- **Kernentscheidungen:** doc/-Struktur bleibt flach (ENT-036), Überbleibsel-Dateien nach `hinweise/archiv/` (ENT-037), MVP-1-Blocker ist API-Key (ENT-038).
- **Wichtigste Erkenntnis:** Nach 9 Engineering-Sessions hat sich in `doc/` eine Serie kleiner Nummerierungs- und Konsistenz-Fehler aufgestaut (14 ID'd Probleme). Regelmäßige PO-Review-Zyklen verhindern, dass Nutzer und zukünftige Engineer-Sessions gegen veraltete Angaben laufen.

---

## Muster über alle Sessions

**Was konstant funktioniert hat:**
- Sessions-als-Gedächtnis-System: jede Session hat klaren Brief + Ergebnisnotizen + Git-Commit.
- Quality-Control als wiederkehrender Zyklus (nicht einmalig).
- Scope-Schutz durch explizite Ablehnungen (GE-001 auf Phase 3, Haiku-only verworfen, Audio gestrichen).

**Was sich als Schwachstelle zeigt:**
- Doku-Drift: nach Umbau werden abhängige Stellen (Nummern, Typen, Referenzen) nicht alle aktualisiert.
- Branch-Naming inkonsistent (master vs. main) — in S011 final auf `master` festgelegt (ENT-039).
- "Überbleibsel"-Dateien (prompt.md, start.md, NEXT_SESSION_PROMPT.md) blieben über 9 Sessions unaufgeräumt in `doc/`.

**Empfehlung für kommende Sessions:**
- Ende jeder Session: Grep-Check auf Referenzen zu geänderten Dateien.
- PO-Sessions als festen Zyklus (z.B. alle 5 Engineering-Sessions).
