# SCHEMA.md — Die Verfassung des LLM-Personal-Knowledge-OS
> Version: 0.3 | Datum: 2026-04-18 | Status: DRAFT

---

## 1. Systemphilosophie

Dieses System ist **kein Notiz-Tool**. Es ist ein persistentes, kompiliertes Gedächtnis des Nutzers — gepflegt von LLMs, navigierbar durch Obsidian, getriggert durch den Alltag.

Drei Axiome:
1. **Rohdaten sind heilig.** Sie werden niemals verändert — nur gelesen und verarbeitet.
2. **Der Graph gehört der KI.** Menschen schreiben keine Wiki-Seiten manuell. Die KI schreibt, der Mensch liest und korrigiert.
3. **Jede Interaktion ist potentielle Erkenntnis.** Der Supervisor bewertet jeden Input auf Graphrelevanz.

---

## 2. Verzeichnisstruktur

```
knowledge-os/
│
├── raw/                        # [IMMUTABLE] Rohdaten — KI liest, nie schreibt
│   ├── events/                 # Telegram-Inputs, Trigger-Nachrichten (JSON + MD)
│   ├── sources/                # Artikel, PDFs, Web-Clips (Obsidian Web Clipper)
│   ├── assets/                 # Bilder, Audio (lokal gespeichert)
│   └── style_refs/             # Stil-Referenz-Medien (IMMUTABLE)
│       └── [name]/             # je Referenz: chappelle/, ted-talk/, ...
│
├── wiki/                       # [LLM-OWNED] Kompiliertes Wissen
│   ├── personal/               # Personal Facts, Diary-Einträge
│   │   ├── facts/              # Einzelne PersonalFact-Seiten
│   │   ├── stories/            # Ausgearbeitete Geschichten/Pointen
│   │   └── style_refs/         # StyleProfile-Seiten (sp_[name].md)
│   ├── language/               # Mehrsprachiges Vokabular, Grammatik, Kultur
│   │   ├── vocab/              # Einzelne VocabEntry-Seiten (alle Sprachen)
│   │   ├── grammar/            # Grammatik-Konzepte (je Sprache)
│   │   ├── culture/            # Personen, Orte, Kulturstichworte (je Land/Region)
│   │   └── bridges/            # Cross-Language-Korrelationen & Kognaten
│   └── concepts/               # Allgemeine Konzepte, Themen, Querverweise
│
├── templates/                  # Markdown-Templates für jeden Entitätstyp
├── agents/                     # Python-Agenten-Code
├── workflows/                  # Workflow-Definitionen (LangGraph)
│
├── SCHEMA.md                   # Diese Datei — Systemverfassung
├── index.md                    # [LLM-MAINTAINED] Inhaltsverzeichnis aller Wiki-Seiten
└── log.md                      # [LLM-MAINTAINED] Append-only Operationslog
```

---

## 3. Entitäts-Ontologie

Die folgenden Typen sind die Grundbausteine des Graphen. Jede Wiki-Seite gehört zu genau einem Typ.

### 3.1 `PersonalFact`
> Ein erzählungswürdiges Ereignis, eine Beobachtung oder Eigenschaft des Nutzers.

**Felder:**
- `title`: Kurzer, einprägsamer Titel
- `date`: Datum des Ereignisses (nicht der Erfassung)
- `context`: Wo/Wann/Mit wem
- `core_fact`: Die rohe Tatsache in 1-2 Sätzen
- `narrative_hook`: Die potentielle Pointe / das Interessante daran
- `related_facts`: Links zu anderen PersonalFacts
- `story_score`: 0–10, wie erzählungswürdig (LLM-bewertet)
- `status`: `raw` | `elaborated` | `story-ready`

### 3.2 `VocabEntry`
> Ein Wort oder Ausdruck in einer beliebigen Zielsprache — mit vollständigem Lernkontext und sprachlichen Brücken zu anderen bekannten Sprachen.

**Felder:**
- `word`: Das Zielwort
- `language`: ISO 639-1 Code (`es`, `en`, `de`, `fr`, ...) — **aus dem Graphen abgeleitet**
- `translations`: Map von Sprache → Übersetzung  
  ```yaml
  translations:
    de: "Mitternacht"
    en: "early morning hours"
  ```
- `conjugation`: Verb-Konjugation (falls Verb, sprachspezifisch)
- `example_sentences`: 3 Beispielsätze in der Zielsprache
- `mnemonic`: Eselsbrücke (LLM-generiert, nutzt bekannte Sprachen des Nutzers)
- `cross_language_bridges`: Kognaten, Faux-amis oder semantische Parallelen zu anderen Sprachen
  ```yaml
  cross_language_bridges:
    - lang: en
      word: "madrugada"
      note: "No direct English cognate — concept gap worth knowing"
    - lang: de
      word: "Morgendämmerung"
      note: "Similar feeling, different time window"
  ```
- `anki_id`: ID der korrespondierenden Anki-Karte (nach Export)
- `difficulty`: `A1` bis `C2` (CEFR, sprachspezifisch)
- `related_words`: Links zu verwandten VocabEntries (auch sprachübergreifend)

**Sprach-Erkennung aus dem Graph:**
Der Language-Agent analysiert periodisch die Sprach-Verteilung in `raw/events/` und `raw/sources/` und aktualisiert ein `user_language_profile.md` — dieses steuert welche Sprachen in `translations` und `cross_language_bridges` priorisiert werden.

### 3.3 `CulturalEntry`
> Eine Person, ein Ort, ein Ereignis oder ein Kulturstichwort — **nicht auf eine Sprache/Region beschränkt**, aber immer mit geografischem und sprachlichem Kontext.

**Felder:**
- `name`: Name der Entität
- `type`: `person` | `place` | `event` | `cultural-concept`
- `country`: ISO 3166-1 alpha-2 Code (`ES`, `MX`, `US`, `GB`, `DE`, ...)
- `language_context`: Primäre Sprache(n) der Entität (ISO 639-1 Liste)
- `summary`: 3-5 Satz-Zusammenfassung
- `why_relevant`: Warum relevant für diesen Nutzer? (LLM-personalisiert aus Graph-Kontext)
- `cross_cultural_links`: Verbindungen zu Entitäten anderer Kulturen/Länder
  ```yaml
  cross_cultural_links:
    - entry: "[[c_gabriel-garcia-marquez]]"
      note: "Beide prägen magischen Realismus — Brücke ES ↔ CO"
  ```
- `sources`: Links zu Quellen in `raw/sources/`
- `related_entries`: Links zu anderen CulturalEntries

### 3.3.1 `LanguageBridge`
> Spezieller Entitätstyp für explizite Verbindungen zwischen Sprachen — z.B. Kognaten, Faux-amis, strukturelle Parallelen, kulturelle Konzepte ohne Äquivalent.

Lebt in `wiki/language/bridges/`. Wird vom Language-Agent automatisch erzeugt wenn Korrelationen entdeckt werden.

**Felder:**
- `type`: `cognate` | `faux-ami` | `concept-gap` | `structural-parallel`
- `languages`: Liste der involvierten Sprachen
- `entries`: Links zu den beteiligten VocabEntries
- `insight`: Die lernrelevante Erkenntnis in 1-2 Sätzen

### 3.4 `Concept`
> Ein abstraktes Thema oder Wissensgebiet (domänenübergreifend).

**Felder:**
- `title`: Konzeptname
- `summary`: Verdichtete Erklärung
- `connections`: Links zu allen Entitäten, die dieses Konzept berühren
- `open_questions`: Offene Fragen — Einladung zur weiteren Erkundung

### 3.5 `RawEvent`
> Ein unverarbeiteter Input (Telegram-Nachricht, manueller Trigger). Lebt in `raw/events/`.

**Felder:**
- `timestamp`: ISO 8601
- `source`: `telegram` | `manual` | `scheduled`
- `content`: Rohtext oder strukturiertes JSON
- `processed`: `true` | `false`
- `wiki_refs`: Links zu erzeugten/aktualisierten Wiki-Seiten

### 3.6 `StyleProfile`
> Aggregiertes Stil-Profil einer Redner-/Comedian-Referenz. Entsteht durch Aggregation mehrerer `StyleFingerprints` aus `raw/style_refs/[name]/`. Lebt in `wiki/personal/style_refs/sp_[name].md`.

**Felder:**
- `name`: Bezeichner der Referenz (z.B. `"chappelle"`, `"ted-talk"`)
- `sample_count`: Anzahl beitragender Clips/Transcripts
- `confidence`: 0.0–1.0 (Schwellwerte: 1→0.25, 3→0.60, 5→0.85, 8→1.00)
- `avg_words_per_second`: Sprechtempo-Mittelwert (nur wenn Audio-Samples vorhanden)
- `avg_pause_before_punchline`: Ø Pause vor der Pointe in Sekunden (nur Audio)
- `setup_ratio`: Mittelwert Aufbau vs. Pointe über alle Samples (0.0–1.0)
- `key_patterns`: Kern-Muster die in ≥50% der Clips vorkommen
- `style_tags`: Labels mit Häufigkeit ≥50% der Clips
- `sources`: Pfade zu allen beitragenden Dateien in `raw/style_refs/[name]/`

**Ab wann nutzbar für Feedback:** ab `confidence >= 0.60` (≥3 Samples).

**Verknüpfung:** StyleProfiles verlinken nicht auf andere Wiki-Entitäten, aber PersonalFact-`practice_log`-Einträge referenzieren das jeweils aktive StyleProfile via `style_profile_ref`.

### 3.7 System-Dateien (`user_profile.md`, `index.md`, `log.md`)

Diese drei Dateien sind **keine Wiki-Entitäten** — sie haben keinen `type:`-Eintrag im Frontmatter und leben direkt im Repo-Root neben `SCHEMA.md`. Sie werden ausschließlich von Agenten geschrieben.

#### `user_profile.md` — Komprimierte Nutzersignatur

Immer im Supervisor-Kontext geladen (~80–120 Zeilen). Template:

```markdown
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Nutzer-Profil

## Sprachprofil
- Primärsprache: de
- Aktive Zielsprachen: [es, en]
- Input-Verteilung (30 Tage): de: 60%, es: 30%, en: 10%
- Input-Verteilung (90 Tage): de: 65%, es: 25%, en: 10%

## Interessen-Cluster
- [Cluster-Name] (hoch | mittel | niedrig) — [Basis: N Seiten]

## Personal-Facts-Profil
- Gesamt: N PersonalFacts
- story_score Durchschnitt: X.X
- High-Score Facts (≥7) ungeübt: N
- Zuletzt elaboriert: YYYY-MM-DD

## Bootstrap
bootstrap_progress: N/10
bootstrap_complete: true | false
bootstrap_started: YYYY-MM-DD

## Style
active_style_profile: "[name]" | null

## Schwellwerte (System-Defaults, überschreibbar)
concept_threshold: 3
story_score_elaborate_threshold: 6
story_score_review_required: 7
stale_raw_days: 7
```

#### `index.md` — Inhaltsverzeichnis aller Wiki-Seiten

Append-only pro Entitätstyp. Format wie in ARCHITECTURE.md §2.2 beschrieben.

#### `log.md` — Chronologisches Operationslog

Append-only. Format: `## [YYYY-MM-DDTHH:MM] operation | Kurzbeschreibung`

---

## 4. Dateinamen-Konventionen

| Entitätstyp    | Prefix  | Format                               | Beispiel                              |
|----------------|---------|--------------------------------------|---------------------------------------|
| PersonalFact   | `pf_`   | `pf_YYYY-MM-DD_kebab-title.md`       | `pf_2026-03-15_fahrrad-unfall.md`     |
| VocabEntry     | `v_`    | `v_[lang]_kebab-wort.md`             | `v_es_madrugada.md`, `v_en_serendipity.md` |
| CulturalEntry  | `c_`    | `c_[cc]_kebab-name.md`               | `c_mx_frida-kahlo.md`, `c_us_jazz.md` |
| LanguageBridge | `lb_`   | `lb_[lang1]-[lang2]_kebab-topic.md`  | `lb_es-en_faux-amis-embarazada.md`    |
| Concept        | `con_`  | `con_kebab-concept.md`               | `con_storytelling-struktur.md`        |
| RawEvent       | —       | `YYYY-MM-DDTHH-MM-SS_source.json`    | `2026-04-18T09-32-11_telegram.json`   |
| StyleProfile   | `sp_`   | `sp_[name].md`                       | `sp_chappelle.md`, `sp_ted-talk.md`   |

---

## 5. Frontmatter-Standard (YAML)

Jede Wiki-Seite beginnt mit diesem YAML-Block:

```yaml
---
type: PersonalFact | VocabEntry | CulturalEntry | Concept
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: raw | elaborated | story-ready | archived
tags: []
sources: []       # Links zu raw/sources/ oder raw/events/
related: []       # Interne Wiki-Links [[andere-seite]]
---
```

---

## 6. Tech Stack

### 6.1 Komponenten-Übersicht

| Komponente         | Technologie                  | Begründung                                      |
|--------------------|------------------------------|-------------------------------------------------|
| LLM-Core           | Claude API (Anthropic)       | Beste Reasoning-Qualität für Synthesis-Tasks    |
| Bulk-Operationen   | Claude Haiku 4.5             | Günstig für Lint, Indexierung, Klassifikation   |
| Agenten-Framework  | LangGraph (Python)           | Explizite Zustandsmaschinen, debuggbar          |
| Input-Trigger      | python-telegram-bot          | Friction-freie Rohdaten-Eingabe                 |
| Anki-Integration   | AnkiConnect (REST)           | Lokale Anki-API, kein Cloud-Overhead            |
| Wissensspeicher    | Markdown-Dateien + Git       | Obsidian-kompatibel, versioniert, portabel      |
| UI / Navigation    | Obsidian                     | Graph View, Dataview, kostenlos                 |
| Suche (ab ~200 S.) | qmd oder sqlite-fts5         | BM25-Suche über Markdown, lokal                 |

### 6.2 Erweiterbarkeit

Das System ist **plugin-architektonisch** aufgebaut. Neue Features folgen diesem Muster:

```
agents/
├── base_agent.py          # Abstrakte Basisklasse — Interface-Vertrag
├── supervisor.py          # Zentrale Orchestrierung
├── language_agent.py      # Modul: Sprache
├── diary_agent.py         # Modul: Diary/Personal Facts
└── [neue_komponente].py   # Neue Agenten folgen demselben Interface
```

**Neue Schnittstellen** (Input-Kanäle) sind isoliert vom Graphen:
- WhatsApp → eigener Receiver, schreibt in `raw/events/` → selber Pipeline wie Telegram
- Web-UI → Flask/FastAPI-Endpoint → selbe `raw/events/` Pipeline
- Scheduled-Jobs → Python `schedule`-Library oder systemd-Timer → selber Agent-Aufruf

**Prinzip:** Alles was Daten in `raw/events/` schreibt, ist kompatibel. Der Graph-Kern ändert sich nie.

### 6.3 LLM-Kosten-Strategie (Sensitivity-Tier-Modell)

Personal Facts sind sensitiv, Vokabeln nicht. Daher drei Tiers:

| Tier | Datenkategorie                        | Modell              | Kosten (ca.)         | Begründung                          |
|------|---------------------------------------|---------------------|----------------------|-------------------------------------|
| 1    | VocabEntry, CulturalEntry, Concepts   | Claude Haiku 4.5    | ~$0.001/Seite        | Nicht-sensitiv, Bulk OK             |
| 2    | Synthesis, Story-Crafting, Bridges    | Claude Sonnet 4.6   | ~$0.01/Seite         | Braucht gutes Reasoning             |
| 3    | PersonalFacts mit `sensitivity: high` | Ollama (lokal)      | $0.00                | Verlässt nie das Gerät              |

**Sensitivity-Tag** in jedem PersonalFact-Frontmatter:
```yaml
sensitivity: public | sensitive | private
```
- `public` → Haiku/Sonnet
- `sensitive` → Sonnet, aber Anonymisierung vor API-Call (PII-Stripping)  
- `private` → nur lokales Modell (Ollama: `llama3.2` oder `mistral`)

**Geschätzte Monatskosten** bei täglichem Gebrauch: **$3–8/Monat** (überwiegend Haiku für Lint + Indexierung, Sonnet nur für tiefe Synthesis).

---

## 7. LLM-Instruktions-Konventionen

Jeder Agent erhält seinen Kontext in dieser Reihenfolge:
1. `SCHEMA.md` (diese Datei) — Systemregeln
2. `index.md` — aktueller Graphzustand
3. Aufgaben-spezifische Modul-Datei (`COMP_LANGUAGE.md`, `COMP_DIARY.md`, etc.)
4. Relevante Wiki-Seiten (vom Supervisor ausgewählt)
5. Der konkrete Task

---

## 8. Selbstheilungs-Definition ("Was ist ein kranker Graph?")

Ein **Lint-Pass** (täglich, durch Supervisor getriggert) prüft:

| Symptom                          | Diagnose               | Heilung                                      |
|----------------------------------|------------------------|----------------------------------------------|
| Wiki-Seite hat keine `related:`  | Verwaiste Seite        | LLM sucht und ergänzt Querverweise           |
| `status: raw` älter als 7 Tage  | Unverarbeiteter Input  | Agenten-Task: elaborieren oder archivieren   |
| Widerspruch zwischen zwei Facts  | Inkonsistenz           | LLM flaggt, Nutzer entscheidet               |
| `story_score` > 7, nie geübt    | Verschwendetes Potential| Diary-Agent schlägt Übungsrunde vor          |
| VocabEntry ohne Anki-Karte       | Lernlücke              | Language-Agent triggert Anki-Export          |

---

## 9. Offene Fragen (Backlog)

- [ ] Wie granular soll der Supervisor das Nutzerprofil modellieren?
- [ ] Brauchen wir eine SQLite-DB für strukturierte Queries auf PersonalFacts?
- [ ] Wie Konfliktauflösung bei Widersprüchen im Graph gestalten (LLM-Flag vs. Auto-Merge)?
- [x] Datenschutz: Sensitivity-Tier-Modell implementiert (public/sensitive/private → Haiku/Sonnet/Ollama)
- [ ] Ollama-Setup definieren: welches lokale Modell für `private`-Tier? (llama3.2 vs. mistral)
- [ ] `user_language_profile.md` Schema definieren — wie oft aktualisiert, welche Schwellwerte?
