# Next Session Prompt — LLM-Personal-Knowledge-OS

## Kontext: Was ist dieses Projekt?

Du arbeitest als Senior Systems Architect an einem persönlichen KI-Wissenssystem namens **LLM-Personal-Knowledge-OS**. Das System basiert auf Karpathys LLM-Wiki-Konzept: ein persistenter, sich selbst heilender Knowledge Graph in Obsidian, der von LLM-Agenten gepflegt wird — kein klassisches RAG, sondern kompiliertes, vernetztes Wissen.

**Tech Stack (entschieden):**
- Python + Claude API (Haiku für Bulk, Sonnet für Synthesis, Ollama für private Daten)
- LangGraph für Agenten-Orchestrierung
- Markdown-Dateien + Git als Wissensspeicher (kein Datenbank-Backend nötig bis ~150 Seiten)
- Obsidian als Read-Only UI
- Telegram Bot als primärer Input-Kanal (Text, URL, Bild, PDF, Voice, YouTube)

**Nutzer:** Hat Programmiererfahrung. Spricht Deutsch als Muttersprache, lernt Spanisch. Breite Interessen: KI/Tech, Gesundheit, Musik, Fotografie, Esport.

---

## Fertige Dokumentation (in `doc/`)

Alle folgenden Dateien sind vollständig und konsistent — lies sie bevor du antwortest:

- **`SCHEMA.md`** — Entitäts-Ontologie (PersonalFact, VocabEntry, CulturalEntry, LanguageBridge, Concept, RawEvent), Frontmatter-Standard, Dateinamen-Konventionen, Tech Stack mit Sensitivity-Tier-Modell (public→Haiku, sensitive→Sonnet+PII-Strip, private→Ollama), Selbstheilungs-Symptome
- **`ARCHITECTURE.md`** — Zwei-Graphen-Konzept (Agent Graph ephemer / Knowledge Graph persistent), Supervisor in 3 Stufen (Klassifikation → Graph Context Match → Routing), LangGraph-Implementierung, Draft→Main Git-Branch-Workflow für Nutzer-Freigabe, Telegram UI-Ebenen (Buttons/Polls → ConversationHandler → Mini Apps)
- **`KNOWLEDGE_GRAPH.md`** — Extractor-Pipeline (alle Formate → normalisierter Text), vollständige Seiten-Templates mit konkreten Beispielen (duende/Flamenco-Kurs), kompletter Ingest-Walkthrough, Linking-Strategie, Lint-Algorithmus mit 6 Symptomen, Graph-Wachstumsphasen

---

## Kernkonzepte die du kennen musst

**Graph Context Match:** Vor jeder Agenten-Ausführung werden aus dem Index die Top-N relevantesten Wiki-Seiten für den aktuellen Input geladen (`graph_context`). Der Agent bewertet nie isoliert — immer im Kontext des bestehenden Graphen. Das ist der wichtigste Architektur-Entscheid.

**Zwei State-Ebenen:**
- `user_profile.md` (~80-120 Zeilen) — komprimierte Nutzer-Signatur, immer im Kontext
- `graph_context` — dynamisch per Task, die konkret relevanten Wiki-Seiten

**Draft→Main Workflow:** LLM schreibt immer auf `draft`-Branch. Kritische Änderungen (story_score > 7, Widersprüche, Löschungen) brauchen Nutzer-Freigabe via Telegram-Button → Python macht `git merge`.

**Extractor-Layer:** Sitzt zwischen Telegram-Receiver und Ingestion-Agent. Normalisiert alle Input-Formate (URL/PDF/Bild/Voice/YouTube) in dasselbe JSON-Schema. Pipeline sieht immer nur Text. Zwei Modi: Quick-Save (kein Hinweis) vs. Process-Now (mit Nutzer-Hinweis).

---

## Was jetzt fehlt — Nächste Schritte

### Priorität 1: `COMP_DIARY.md` schreiben
Das innovativste Modul. Noch nicht dokumentiert. Kernaufgabe: **Personal Facts Engine** — Extraktion erzählungswürdiger Momente, story_score-Scoring, Elaboration und Übungsroutinen für soziale Interaktionen.

Wichtige offene Fragen dazu:
- **Bootstrap-Interview:** Welche 10 Fragen stellt der Bot initial um erste PersonalFacts zu seeden?
- **Scoring-Modell im Detail:** Die 4 Dimensionen (Überraschung 0-3 / Anschlussfähigkeit 0-3 / Sensorik 0-2 / Pointe 0-2) sind definiert — aber wie genau berechnet der Diary-Agent die Pointe? Was ist der Prompt?
- **Übungsroutine:** Wie sieht eine konkrete Übungsrunde via Telegram aus? ConversationHandler-Flow?
- **Korrelations-Engine:** Wie findet der Diary-Agent thematische Cluster zwischen bestehenden Facts?

### Priorität 2: `COMP_LANGUAGE.md` schreiben
Spanisch/Mehrsprachig-Modul. Anki-Integration via AnkiConnect REST. Zufällige Push-Nachrichten. Empfehlungssystem basierend auf Graph-Inhalt.

### Priorität 3: Python-Projekt-Scaffold
Nach den Docs: die Projektstruktur anlegen, erste Agenten implementieren.

### Priorität 4: Bestehende Clippings verarbeiten
In `raw/Wiki/Clippings/` liegen bereits 11 Web-Clips (Karpathy-Artikel, Musik, CS2, Gesundheit). Diese als ersten echten Ingest-Test nutzen.

---

## Offene technische Entscheidungen

1. **Ollama-Modell** für `sensitivity: private` — llama3.2 vs. mistral (Qualität vs. Speed)
2. **Concept-Seiten-Schwellwert** — ab 3 Seiten mit gleichem Tag auto-erstellen? Nutzer bestätigt?
3. **Widerspruchs-Filter** — wie viel Tag-Überschneidung zwischen zwei PersonalFacts triggert Haiku-Prüfung?
4. **Bootstrap-Interview** — 10 konkrete Fragen definieren

---

## Interaktions-Symbole des Nutzers

- `(?)text(?)` → Frage / Best-Practice gesucht
- `(!)text(!)` → kritische Anforderung
- `[TODO]` → technische Lücke füllen
