# ARCHITECTURE.md — System-Architektur: LLM-Personal-Knowledge-OS
> Version: 0.2 | Datum: 2026-04-18 | Status: DRAFT

---

## 1. Architektur-Überblick

Das System hat **zwei getrennte "Graphen"** — ein wichtiger konzeptueller Unterschied:

| Begriff              | Was es ist                                          | Wer schreibt    | Wo lebt es            |
|----------------------|-----------------------------------------------------|-----------------|-----------------------|
| **Knowledge Graph**  | Die Markdown-Wiki — persistentes Nutzer-Gedächtnis  | LLM-Agenten     | `wiki/` (Dateisystem) |
| **Agent Graph**      | LangGraph Zustandsmaschine — Orchestrierung         | Python-Code     | RAM (pro Lauf)        |

Der **Knowledge Graph ist der einzige persistente Zustand des Systems.** Der Agent Graph ist ephemer — er wird pro Task gestartet und endet. Alles was wichtig ist, landet im Knowledge Graph.

```
┌─────────────────────────────────────────────────────────────────┐
│                        NUTZER-KONTEXT                           │
│  Telegram · Datei-Drop in raw/ · (weitere Input-Kanäle)         │
│  Input-Typen: Text · URL · Bild · PDF · Voice · YouTube         │
│  Optional: Kontext-Hint ("interessant für Vokabel", #story, ...) │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTRACTOR                                  │
│  Format-Erkennung → Typ-spezifische Extraktion                  │
│  URL→BeautifulSoup · PDF→pdfplumber · Bild→Claude Vision        │
│  Voice→faster-whisper · YouTube→youtube-transcript-api          │
│  Ergebnis: normalisierter Text (gleiches Schema, egal was rein)  │
│  Speichert: Original → raw/sources|assets/ (permanent)          │
└────────────────────────┬────────────────────────────────────────┘
                         │ ExtractedContent (JSON)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      raw/events/                                │
│              [IMMUTABLE — Append Only]                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               SUPERVISOR — Stufe 1: Klassifikation              │
│  Liest: user_profile.md (komprimierte Nutzersignatur)           │
│  Entscheidet: Intent? Welcher Agent? Welches Modell?            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            GRAPH CONTEXT MATCH  ◄── NEU                        │
│  Anfrage → Schlüsselbegriffe extrahieren                        │
│  → index.md / SQLite durchsuchen                               │
│  → Top-N relevante Wiki-Seiten laden                            │
│  Ergebnis: graph_context (relevante Seiten als Kontext)         │
└────────────────────────┬────────────────────────────────────────┘
                         │ graph_context im State
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               SUPERVISOR — Stufe 2: Routing                     │
│  Verteilt Task + graph_context an Agenten                       │
└──────┬──────────────┬──────────────┬──────────────┬────────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
  [Ingestion]   [Language]      [Diary]         [Lint]
   Agent         Agent           Agent           Agent
   (kein GC)    (GC: verwandte  (GC: ähnliche   (kein GC)
                 Vokabeln,       Facts, Themen,
                 Brücken)        Muster)
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                         │ WikiWrite-Objekte
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           SUPERVISOR — Stufe 3: Bewertung & Freigabe            │
│  Prüft Agent-Output gegen user_profile + graph_context          │
│  Gibt Schreib-Freigabe oder sendet zur Revision                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE GRAPH                              │
│              wiki/ — Markdown-Dateien                           │
│         index.md · log.md · user_profile.md                    │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                       OBSIDIAN                                  │
│              [Read-Only für Nutzer]                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Der Knowledge Graph

### 2.1 Was der Graph ist

Der Knowledge Graph ist **kein Datenbank-Schema** und **kein Index**. Er ist eine kompilierte, interverlinkte Struktur aus Markdown-Dateien, die das Wissen und die Persönlichkeit des Nutzers repräsentiert.

Drei Eigenschaften sind entscheidend:

1. **Kompiliert, nicht retrieved.** Wissen wird einmal verarbeitet und in Struktur überführt. Beim Abruf wird nicht gesucht — es wird gelesen.
2. **Lebt in Querverweisen.** Eine VocabEntry-Seite allein hat wenig Wert. Ihr Wert entsteht durch Links zu CulturalEntries, PersonalFacts und Concepts, die ihr Bedeutung geben.
3. **Wächst und heilt sich.** Neue Inputs erweitern den Graphen. Der Lint-Agent erkennt und korrigiert strukturelle Schwächen.

### 2.2 Navigations-Einstiegspunkte

Der Graph hat zwei spezielle Dateien die als Navigationshilfe für LLMs dienen:

**`index.md`** — Content-orientiert
```markdown
## PersonalFacts (12)
- [[pf_2026-03-15_fahrrad-unfall]] — Unfall in München, story_score: 8
- [[pf_2026-02-01_erste-flamenco-show]] — Erstes Flamenco-Erlebnis, story_score: 6
...

## VocabEntries — ES (47)
- [[v_es_madrugada]] — "frühe Morgenstunden", keine direkte DE-Übersetzung
...
```

**`log.md`** — Chronologisch, append-only
```markdown
## [2026-04-18] ingest | Telegram: "war heute bei einem Flamenco-Kurs"
## [2026-04-17] lint | 3 verwaiste Seiten gefunden, 2 repariert
## [2026-04-16] query | Nutzer fragte nach Spanisch-Wörtern für Musik
```

**`user_profile.md`** — Das Nutzer-Modell (Supervisor-Kernwissen)
```markdown
# Nutzer-Profil
## Sprachprofil
- Primärsprache: Deutsch
- Aktive Zielsprachen: Spanisch (ES, MX), Englisch
- Erkannte Input-Verteilung: 60% DE, 30% ES, 10% EN (letzten 30 Tage)

## Interessen-Cluster
- Spanische Kultur / Lateinamerika (hoch)
- Soziale Interaktion / Storytelling (hoch)
- [weitere aus Graph-Analyse]

## Personal-Facts-Profil
- story_score Durchschnitt: 6.2
- Noch nicht geübte Facts mit score > 7: 3
```

### 2.3 Graph-Operationen

Es gibt genau **drei Grund-Operationen** auf dem Graphen:

#### INGEST
Neuer Rohstoff kommt rein → Graph-Kontext wird abgerufen → wird verarbeitet → Graph wird erweitert.

```
RawEvent eingelesen
    → Supervisor klassifiziert (Sprache? PersonalFact? Beides?) [Haiku]
    → Graph Context Match: Schlüsselbegriffe → Top-N relevante Wiki-Seiten laden
    → Zuständiger Agent verarbeitet MIT graph_context als Kontext [Sonnet]
    → 1–N neue oder aktualisierte Wiki-Seiten
    → index.md Update
    → log.md Eintrag
    → user_profile.md ggf. aktualisiert
```

**Der entscheidende Effekt:** Jeder neue Input wird nicht isoliert bewertet, sondern im Kontext des gesamten bisherigen Wissens des Nutzers. Ein `story_score` ist damit keine absolute Zahl — er misst den Wert des neuen Facts *relativ zu dem, was der Graph bereits kennt*.

#### QUERY
Nutzer stellt Frage → Graph wird gelesen → Antwort wird (optional) zurückgeschrieben.

```
Frage eingelesen
    → Supervisor liest index.md
    → Relevante Seiten werden geladen (kein Embedding-Lookup — nur Index-Scan)
    → Sonnet synthetisiert Antwort mit Quellen-Links
    → Optional: Antwort als neue Concept-Seite gespeichert
    → log.md Eintrag
```

#### LINT
Periodisch (täglich) → Graph-Gesundheit prüfen → Schwächen beheben.

```
Lint-Agent scannt alle Wiki-Seiten
    → Prüft Symptome (siehe SCHEMA.md §8)
    → Erstellt Fix-Tasks pro Symptom
    → Führt automatisch reparierbare Fixes aus
    → Flaggt nicht-automatisch reparierbare für Nutzer
    → log.md Eintrag mit Lint-Report
```

---

## 3. Supervisor

### 3.1 Rolle

Der Supervisor ist **kein LLM-Agent im klassischen Sinn**. Er ist ein **Routing- und Bewertungs-Layer** — er orchestriert, bewertet und priorisiert. Er hat immer den Nutzer als Maßstab.

**Supervisor-Prinzip:** *"Was würde dem Nutzer jetzt am meisten nützen?"*

### 3.2 Supervisor-Zustand (pro Lauf)

```python
class SupervisorState(TypedDict):
    raw_event: RawEvent           # Der aktuelle Input
    user_profile: dict            # Aus user_profile.md geladen (komprimiert, ~3000 Tokens)
    graph_index: str              # index.md Inhalt (Navigationshilfe)
    classified_intent: str        # "vocab" | "personal_fact" | "both" | "query" | "lint"
    graph_context: list[WikiPage] # ◄ NEU: relevante Wiki-Seiten für diesen spezifischen Input
    assigned_agents: list[str]    # Welche Agenten werden aktiviert
    agent_outputs: dict           # Ergebnisse der Agenten
    supervisor_verdict: str       # "accept" | "revise" | "reject"
    wiki_writes: list[WikiWrite]  # Zu schreibende Seiten
```

**Zwei Ebenen des Nutzer-Wissens im State:**
- `user_profile` — immer geladen, komprimiert, statisch (~80-120 Zeilen). Enthält: Sprach-Verteilung, Interessens-Cluster, story_score-Statistiken. Beantwortet: *"Wer ist der Nutzer?"*
- `graph_context` — dynamisch, per-Task, spezifisch. Enthält: die N relevantesten Wiki-Seiten für den aktuellen Input. Beantwortet: *"Was weiß der Graph schon über dieses Thema?"*

### 3.3 Supervisor-Entscheidungslogik

```
Input kommt rein
    │
    ├─ [1. Klassifikation] → Was ist das? (Haiku, günstig)
    │       ├─ Spanisches Wort/Ausdruck → Language Agent
    │       ├─ Persönliches Erlebnis → Diary Agent
    │       ├─ Beides → Beide parallel
    │       ├─ Frage des Nutzers → Query-Flow
    │       └─ Kein klarer Typ → Supervisor fragt nach (Telegram-Antwort)
    │
    ├─ [2. Graph Context Match] → Schlüsselbegriffe extrahieren → graph_reader.search()
    │       ├─ Für PersonalFact: suche ähnliche Facts, Themen-Cluster, Orte, Personen
    │       ├─ Für Vocab: suche verwandte Wörter, Bridges, CulturalEntries
    │       └─ Ergebnis: graph_context (Top 5-10 relevante Seiten)
    │
    │       Beispiel: Input "war beim Flamenco-Kurs heute"
    │       → graph_context enthält: [[pf_erste-flamenco-show]], [[c_es_flamenco]],
    │         [[v_es_duende]], [[con_spanische-kultur]]
    │       → Diary Agent erkennt: das ist Teil eines Musters → story_score steigt
    │
    ├─ [3. Ausführung] → Agenten erhalten: Task + user_profile + graph_context
    │       → Agenten arbeiten parallel wo möglich
    │
    ├─ [4. Bewertung] → Supervisor prüft Agent-Output gegen user_profile + graph_context
    │       ├─ Ist story_score konsistent mit ähnlichen Facts im graph_context?
    │       ├─ Wurden relevante Querverweise aus graph_context gezogen?
    │       ├─ Passt die Sprach-Zuordnung zur bekannten Verteilung?
    │       └─ Gibt es Widersprüche zu bestehenden Wiki-Seiten?
    │
    └─ [5. Schreiben] → Nur nach Supervisor-Freigabe landet etwas im Graphen
```

### 3.4 Supervisor als Nutzer-Anwalt

Der Supervisor kombiniert zwei Wissensquellen um den Nutzer zu verstehen:

**`user_profile.md` — die komprimierte Signatur** (~80-120 Zeilen, immer im Kontext)
- Sprach-Verteilung der letzten 30/90 Tage
- Interessens-Cluster (aus Themen-Häufigkeit im Graph)
- story_score-Durchschnitt und Schwellwerte
- Noch nicht elaborierte High-Score-Facts

**`graph_context` — das situative Gedächtnis** (dynamisch, per-Task)
- Die konkret relevanten Wiki-Seiten für den aktuellen Input
- Gibt dem Agenten nicht nur das Profil des Nutzers, sondern den echten Kontext

**Positiver Feedback-Loop:** Je reicher der Graph, desto bessere graph_context-Treffer, desto treffsicherere Bewertungen, desto besser wächst der Graph weiter.

```
Leerer Graph     → graph_context leer → score basiert nur auf user_profile
Graph mit 50 S.  → graph_context 3-5 Treffer → score informiert durch Muster
Graph mit 200 S. → graph_context 8-10 Treffer → score hochpräzise, vernetzt
```

---

## 4. Agenten

### Kommunikations-Prinzip

**Agenten kommunizieren nicht direkt miteinander.** Jegliche Koordination läuft über:
1. **LangGraph State Dict** — ephemer, pro Lauf (Supervisor teilt Kontext)
2. **Knowledge Graph** — persistent (Agenten lesen/schreiben Dateien)

Das macht das System debuggbar und erweiterbar: ein neuer Agent muss nur das Dateiformat kennen, nicht die anderen Agenten.

### 4.1 Ingestion Agent

**Zweck:** Klassifiziert und normalisiert RawEvents. Ist das Eingangs-Gateway des Systems.

**Input:** `raw/events/` Datei  
**Output:** Strukturierter Task für den Supervisor + klassifizierter Intent

**Verantwortlichkeiten:**
- Sprache des Inputs erkennen (ISO 639-1)
- Intent klassifizieren (vocab / personal_fact / query / ambiguous)
- Bei Mehrdeutigkeit: Rückfrage an Nutzer via Telegram formulieren
- Metadaten normalisieren (Timestamp, Source)

**Modell:** Claude Haiku (Klassifikation ist cheap)

### 4.2 Language Agent

**Zweck:** Verarbeitet sprachbezogene Inputs → erzeugt/aktualisiert VocabEntry, CulturalEntry, LanguageBridge.

**Input:** Klassifizierter Task vom Supervisor + relevante Wiki-Seiten aus Index  
**Output:** Neue/aktualisierte Markdown-Seiten + Anki-Export-Task (optional)

**Verantwortlichkeiten:**
- VocabEntry erstellen mit vollständigem Kontext (Übersetzungen, Konjugation, Beispielsätze, Eselsbrücke)
- Cross-Language-Bridges identifizieren und verlinken
- CulturalEntry erstellen mit Land-Kontext
- Bestehende Einträge aktualisieren wenn neue Info eintrifft
- Anki-Export triggern (via AnkiConnect REST)
- `user_language_profile.md` Input-Verteilung aktualisieren

**Modell:** Haiku für Routine-VocabEntries / Sonnet für komplexe CulturalEntries und Bridges

### 4.3 Diary Agent

**Zweck:** Extrahiert PersonalFacts, bewertet Erzählpotential, elaboriert Geschichten.

**Input:** Klassifizierter Task + PersonalFacts aus Index (für Kontext und Korrelationen)  
**Output:** Neue/aktualisierte PersonalFact-Seiten, ggf. Story-Seiten

**Verantwortlichkeiten:**
- PersonalFact aus RawEvent extrahieren
- `story_score` berechnen (0–10) nach diesen Kriterien:
  - Überraschungsmoment (0–3 Punkte)
  - Universelle Anschlussfähigkeit — "Kann jeder nachfühlen?" (0–3 Punkte)
  - Konkrete Details / Sensorisches (0–2 Punkte)
  - Pointe / Wendung (0–2 Punkte)
- Korrelationen zu bestehenden PersonalFacts suchen (Themen-Cluster)
- Facts mit `story_score > 7` für Elaboration vormerken
- Übungs-Prompts generieren (Telegram-Nachricht an Nutzer)

**Modell:** Sonnet (Nuanciertes Reasoning über Erzähl-Qualität)  
**Privacy:** Sensitivity-Tier aus SCHEMA.md §6.3 strikt beachten

### 4.4 Lint Agent

**Zweck:** Periodische Graphen-Gesundheit. Findet strukturelle Schwächen, behebt was automatisch geht.

**Input:** Alle Wiki-Seiten (batch-weise) + index.md + log.md  
**Output:** Lint-Report, reparierte Seiten, Aufgaben-Queue für Nutzer-Entscheidungen

**Verantwortlichkeiten:**
- Symptome aus SCHEMA.md §8 prüfen
- Automatisch reparierbar: fehlende Querverweise ergänzen, Index aktualisieren
- Nicht automatisch: Widersprüche flaggen, Nutzer-Entscheidung einholen (Telegram)
- Monatlicher "Graph-Health-Report" für Nutzer generieren

**Modell:** Haiku (Struktur-Checks sind cheap)  
**Trigger:** Täglich 03:00 Uhr (systemd-Timer oder Python `schedule`)

---

## 5. Provider-Strategie

### 5.1 Zwei-Modus-Betrieb

Das System kennt zwei Provider-Modi — automatische Auswahl via Umgebungsvariable:

| Modus | Bedingung | Haiku-Rolle | Sonnet-Rolle | Zweck |
|---|---|---|---|---|
| **Claude** | `ANTHROPIC_API_KEY` gesetzt | Haiku 4.5 | Sonnet 4.6 | Produktion |
| **Ollama** | kein API-Key | llama3.2 (o.ä.) | llama3.2 (o.ä.) | Lokale Tests |

Die Auswahl liegt ausschließlich in `agents/base_agent.py` — kein Agent-Code ändert sich. Agenten rufen weiterhin `_haiku()` und `_sonnet()` auf.

```python
# .env — Produktion
ANTHROPIC_API_KEY=sk-ant-...

# .env — lokale Tests (kein API-Key nötig)
OLLAMA_MODEL=llama3.2   # optional, Default: llama3.2
OLLAMA_HOST=http://localhost:11434  # optional
```

### 5.2 Qualitäts-Hinweis Ollama-Modus

Ollama/llama3.2 hält strukturierte Ausgabeformate (`key: value`) weniger zuverlässig ein als Claude. Im Test-Modus können einzelne Felder leer oder fehlformatiert sein — das ist kein Bug im Pipeline-Code, sondern ein bekanntes Modell-Limitation. Für reine Mechanik-Tests (LangGraph-Routing, WikiWrite-Objekte, graph_reader) reicht es vollständig.

Für Qualitätstests (story_score, VocabEntry-Inhalt) ist Claude API nötig.

---

## 6. LangGraph Implementierung

### 5.1 Graph-Struktur (Ingestion Flow)

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(SupervisorState)

# Nodes
workflow.add_node("classify",             ingestion_agent.classify)
workflow.add_node("fetch_graph_context",  graph_reader.fetch_context)   # ◄ NEU
workflow.add_node("language_agent",       language_agent.process)
workflow.add_node("diary_agent",          diary_agent.process)
workflow.add_node("supervisor_review",    supervisor.review)
workflow.add_node("write_to_graph",       graph_writer.write)
workflow.add_node("update_index",         index_updater.update)

# Edges
workflow.set_entry_point("classify")
workflow.add_edge("classify", "fetch_graph_context")  # immer zuerst Graph befragen

workflow.add_conditional_edges(
    "fetch_graph_context",
    supervisor.route,                     # jetzt mit graph_context im State
    {
        "vocab":         "language_agent",
        "personal_fact": "diary_agent",
        "both":          ["language_agent", "diary_agent"],  # parallel
        "query":         "query_flow",
    }
)

workflow.add_edge("language_agent",    "supervisor_review")
workflow.add_edge("diary_agent",       "supervisor_review")
workflow.add_edge("supervisor_review", "write_to_graph")
workflow.add_edge("write_to_graph",    "update_index")
workflow.add_edge("update_index",      END)
```

### 5.2 Datei-Schreib-Vertrag

Kein Agent schreibt direkt Dateien. Alle schreiben in den State:

```python
class WikiWrite(TypedDict):
    path: str           # z.B. "wiki/language/vocab/v_es_madrugada.md"
    content: str        # Vollständiger Markdown-Inhalt
    operation: str      # "create" | "update" | "append"
```

Der `graph_writer`-Node führt alle Writes nach Supervisor-Freigabe aus. Das gibt dem Supervisor die letzte Kontrolle und macht Rollbacks möglich.

### 5.3 Graph Reader — Index-Abstraktion

Der `graph_reader` ist die einzige Stelle die weiß wie der Index implementiert ist. Alle Agenten und der Supervisor rufen nur diese Schnittstelle auf:

```python
# agents/graph_reader.py
WIKI_PAGE_THRESHOLD = 150  # ab hier: SQLite statt index.md

def search_wiki(
    query: str,
    type: str | None = None,   # "PersonalFact" | "VocabEntry" | ...
    limit: int = 10,
) -> list[WikiPage]:
    if _wiki_size() < WIKI_PAGE_THRESHOLD:
        return _search_index_md(query, type, limit)   # Phase 1: einfach
    else:
        return _search_sqlite(query, type, limit)     # Phase 2: automatisch aktiv

def fetch_context(state: SupervisorState) -> SupervisorState:
    """LangGraph Node: extrahiert Schlüsselbegriffe und befüllt graph_context."""
    keywords = _extract_keywords(state["raw_event"])  # Haiku, günstig
    pages = search_wiki(query=" ".join(keywords), limit=8)
    return {**state, "graph_context": pages}
```

**Phase 1** (< 150 Seiten): `_search_index_md` — parst `index.md`, einfaches Keyword-Matching.  
**Phase 2** (≥ 150 Seiten): `_search_sqlite` — SQLite FTS5, ~150 Zeilen Python-Indexer.  
**Switch:** automatisch durch `_wiki_size()`. Der Rest des Systems merkt nichts.

---

## 6. Nutzer-Interaktion: Telegram UI-Ebenen

Telegram ist der primäre Interaktionskanal. Es bietet drei native UI-Ebenen — von einfach bis reich:

### Ebene 1 — Buttons & Polls (sofort, kein Extra-Code)

```
Conflict-Flag vom Lint-Agent:
┌─────────────────────────────────────┐
│  ⚠️ Widerspruch gefunden             │
│                                     │
│  Alt: "Flamenco-Kurs war im März"   │
│  Neu: "Flamenco-Kurs war im April"  │
│                                     │
│  [März behalten]  [April übernehmen]│
│  [Beide behalten — verschiedene]    │
└─────────────────────────────────────┘
→ InlineKeyboardMarkup mit Callback-Buttons
→ Nutzer tippt, Supervisor führt Entscheidung aus
```

```
Vokabel-Quiz vom Language-Agent:
┌─────────────────────────────────────┐
│  🇪🇸 Was bedeutet "madrugada"?       │
│                                     │
│  ○ Mittagsschlaf                    │
│  ○ Frühe Morgenstunden  ✓           │
│  ○ Sonnenuntergang                  │
│  ○ Wochenende                       │
└─────────────────────────────────────┘
→ Telegram Poll mit is_quiz=True
→ Native Auflösung mit Erklärung, kein Code nötig
```

### Ebene 2 — Konversations-Flow (mittel, ~50 Zeilen)

Für Übungs-Runden aus dem Diary-Modul: mehrstufige Konversation per Nachrichten.

```
Bot: "Erzähl mir die Geschichte mit dem Fahrradunfall in 3 Sätzen."
Nutzer: [antwortet]
Bot: "Gut. Jetzt mit einer Pointe am Ende — was war das Überraschende?"
Nutzer: [antwortet]
Bot: "story_score: 7/10 — die Pointe ist stark, der Einstieg könnte konkreter sein."
```

→ `ConversationHandler` in python-telegram-bot, State-Machine per User-Session

### Ebene 3 — Telegram Mini Apps (Upgrade-Pfad, bei Bedarf)

Wenn native Telegram-UI nicht mehr reicht: Mini Apps sind vollständige Web-Apps (HTML/CSS/JS) die direkt im Telegram-Chat öffnen — ohne separate App.

**Mögliche Nutzung:**
- Obsidian-ähnliche Graph-Visualisierung auf dem Handy
- Aufwändigere Story-Übungs-Interfaces
- Dashboard für Graph-Health-Report

**Aufwand:** ~1 Woche für ein einfaches Mini App. Kein App-Store nötig.

**Entscheidung:** Start mit Ebene 1 + 2. Ebene 3 nur wenn konkreter Bedarf entsteht.

---

## 7. Graph-Versionierung: Draft → Prod Workflow

### Das Konzept

Der Knowledge Graph läuft auf **zwei Git-Branches**:

```
draft  ← LLM schreibt hier (alle neuen/aktualisierten Wiki-Seiten)
main   ← "prod" Graph — was Obsidian liest, was zählt
```

Kein GitHub nötig. Lokales Git-Repo, Python-Script macht den Merge.

### Flow

```
LLM-Agent verarbeitet Input
    → graph_writer schreibt in draft-Branch
    → Lint-Agent prüft neue Seiten auf draft
    → Supervisor generiert Review-Summary

Supervisor → Telegram-Nachricht an Nutzer:
┌─────────────────────────────────────────┐
│  📋 3 neue Seiten warten auf Freigabe   │
│                                         │
│  • pf_2026-04-18_flamenco-kurs (neu)    │
│  • v_es_duende (aktualisiert)           │
│  • lb_es-de_duende-bridge (neu)         │
│                                         │
│  [Freigeben ✓]  [Details]  [Ablehnen ✗] │
└─────────────────────────────────────────┘

[Freigeben] → git merge draft → main (Python subprocess)
[Details]   → Bot sendet Diff-Summary der Änderungen
[Ablehnen]  → git checkout draft -- . (reset), Nutzer-Feedback optional
```

### Implementierung

```python
# graph_writer.py
import subprocess

def approve_draft() -> bool:
    """Mergt draft → main. Wird via Telegram-Callback aufgerufen."""
    result = subprocess.run(
        ["git", "merge", "draft", "--no-ff", "-m", "approved by user"],
        cwd=WIKI_ROOT, capture_output=True
    )
    return result.returncode == 0

def reject_draft() -> bool:
    """Setzt draft auf Stand von main zurück."""
    subprocess.run(["git", "checkout", "main"], cwd=WIKI_ROOT)
    subprocess.run(["git", "branch", "-D", "draft"], cwd=WIKI_ROOT)
    subprocess.run(["git", "checkout", "-b", "draft"], cwd=WIKI_ROOT)
    return True
```

### Wann Freigabe nötig?

Nicht jede Änderung braucht manuelle Freigabe — das wäre zu viel Aufwand:

| Änderungstyp                      | Freigabe nötig? | Begründung                          |
|-----------------------------------|-----------------|-------------------------------------|
| Neue VocabEntry                   | Nein            | Risikoarm, reversibel               |
| Neue CulturalEntry                | Nein            | Risikoarm                           |
| Neuer PersonalFact (`raw`)        | Nein            | Nur Extraktion, noch nicht elaboriert|
| PersonalFact (`story_score > 7`)  | Ja              | Wertvoller Inhalt, Nutzer soll wissen|
| Widerspruch-Auflösung             | Ja              | Inhaltliche Entscheidung            |
| Lint-Fix (Querverweise)           | Nein            | Strukturell, risikoarm              |
| Löschung/Archivierung             | Immer           | Destruktiv                          |

---

## 8. Trigger & Scheduling

| Trigger                    | Wann                       | Auslöser            | Flow              |
|----------------------------|----------------------------|---------------------|-------------------|
| Telegram-Nachricht         | Jederzeit (Nutzer)         | Telegram Webhook    | Ingestion         |
| Täglicher Lint             | 03:00 Uhr                  | systemd-Timer       | Lint              |
| Wöchentliche Übungs-Runde  | Sonntag 10:00 Uhr          | systemd-Timer       | Diary (Übung)     |
| Zufällige Sprachnachricht  | 1x täglich, zufällige Zeit | Python `schedule`   | Language (Push)   |
| Monatlicher Graph-Report   | 1. des Monats              | systemd-Timer       | Lint (Report)     |
| Draft-Review-Reminder      | Wenn draft > 24h alt       | Python `schedule`   | Telegram Freigabe |

---

## 9. Offene Architektur-Fragen (Backlog)

- [x] Supervisor-Granularität: user_profile (~80-120 Zeilen) + graph_context (dynamisch) — zwei Ebenen
- [x] Index-Schwellwert: graph_reader Abstraktion mit automatischem Phase 1→2 Switch bei 150 Seiten
- [x] Nutzer-UI: Telegram Ebene 1 (Buttons/Polls) + Ebene 2 (ConversationHandler); Mini Apps als Upgrade-Pfad
- [x] Graph-Versionierung: draft → main Branch-Workflow, manuelle Freigabe via Telegram für kritische Änderungen
- [x] Ollama lokal: llama3.2 als Default für `private`-Tier und als Test-Fallback. Qualitätsvergleich llama3.2 vs. mistral steht noch aus — für MVP-0/1 reicht llama3.2.
- [ ] Keyword-Extraktion für graph_context: wie viele Begriffe, welche Gewichtung (Entitäten > Verben)?
