# COMP_DIARY.md — Personal Facts Engine
> Version: 0.2 | Datum: 2026-04-18 | Status: DRAFT

---

## 0. Modul-Überblick

Die Personal Facts Engine ist das **soziale Gedächtnis** des Systems. Ihr Zweck ist nicht Archivierung — sondern Vorbereitung auf echte Gespräche. Sie extrahiert erzählungswürdige Momente, bewertet ihr Potential, trainiert den Nutzer im Erzählen, und hält die Geschichten lebendig.

### Zweck

```
Rohes Erlebnis → erzählungswürdiger Personal Fact → geübte Geschichte → soziales Kapital
```

Das Modul arbeitet in vier Betriebsmodi:

| Modus         | Trigger                                | Was passiert                                      |
|---------------|----------------------------------------|---------------------------------------------------|
| **Ingest**    | Neue Telegram-Nachricht / Event        | PersonalFact extrahieren, scoring, verlinken      |
| **Elaboration** | story_score ≥ 6, status: raw         | Fact ausarbeiten, narrative_hook schärfen          |
| **Story-Lab** | Nutzer-Anfrage oder Lint-Trigger       | Gezielte Übung einer konkreten Geschichte         |
| **Impuls**    | Täglich/zufällig, systemgetriggert    | Freies Sprechen anhand von Graph-Kombinationen    |

### Abgrenzung

- **Diary ↔ Language Agent:** Wenn ein PersonalFact einen Vokabel-Moment enthält (z.B. "der Lehrer sagte *duende*"), übergibt der Diary-Agent einen VocabEntry-Task an den Language Agent. Die Grenze liegt auf dem Satz: PersonalFacts beschreiben *Erlebnisse*, VocabEntries beschreiben *Wörter*.
- **Diary ↔ Lint Agent:** Der Lint-Agent erkennt High-Score-Facts die noch nicht geübt wurden und triggert Story-Lab. Der Diary-Agent führt Story-Lab aus.
- **Diary ↔ Supervisor:** Der Supervisor entscheidet ob ein Input ein PersonalFact ist. Der Diary-Agent entscheidet wie er ihn verarbeitet.

### Modell-Wahl

| Aufgabe                              | Modell            | Begründung                                    |
|--------------------------------------|-------------------|-----------------------------------------------|
| Fact-Extraktion aus Input            | Haiku 4.5         | Günstig, reicht für Klassifikation            |
| story_score Berechnung               | Sonnet 4.6        | Nuanciertes Reasoning über Erzählqualität     |
| Elaboration + narrative_hook         | Sonnet 4.6        | Kreatives Schreiben, Pointe herausarbeiten    |
| Impuls-Generator                     | Haiku 4.5         | Template-Kombinatorik, kein deep reasoning    |
| Story-Lab Feedback                   | Sonnet 4.6        | Coaching erfordert präzise Sprache            |
| Transkript-Qualitätsanalyse          | Sonnet 4.6        | Text-Input, Struktur- und Qualitätsbewertung  |
| Korrelations-Engine (Kandidaten)     | Haiku 4.5         | Keyword-Matching, günstiger Scan              |
| Korrelations-Engine (Cluster-Analyse)| Sonnet 4.6        | Semantische Verbindungen erkennen             |
| StyleFingerprint-Extraktion          | Sonnet 4.6        | Timing + Struktur + Muster aus einem Clip     |
| StyleProfile-Aggregation             | Haiku 4.5         | Mittelung + Konfidenz-Berechnung, günstig     |

**Privacy:** PersonalFacts mit `sensitivity: private` → ausschließlich Ollama. Kein Cloud-LLM.  
Sensitivity-Tier-Modell aus SCHEMA.md §6.3 gilt uneingeschränkt.

---

## 1. PersonalFact-Erweiterungen

Das Basis-Template aus SCHEMA.md §3.1 wird um zwei Felder erweitert:

### 1.1 Neues Feld: `social_context`

`social_context` beschreibt *wann* und *für wen* diese Geschichte erzählt wird. Das ist der Unterschied zwischen einer Anekdote die im Gedächtnis liegt und einer die nie genutzt wird.

```yaml
social_context:
  when: "Gespräche über Spanien / erste Stunden mit neuen Leuten"
  audience: "Fremde | Freunde | gemischt"
  mood: "locker | tiefgründig | humorvoll"
```

Der Diary-Agent füllt `social_context` automatisch beim Elaboration-Schritt — basierend auf `core_fact`, `tags` und dem `user_profile`. Beispiel:

```yaml
# pf_2026-04-18_flamenco-kurs-lehrer.md
social_context:
  when: "Wenn jemand fragt ob du tanzt / Spanien-Gespräche / 'was machst du so'-Fragen"
  audience: "gemischt"
  mood: "humorvoll, mit tiefgründigem Kern"
```

### 1.2 Neues Feld: `practice_log`

Append-only Liste aller Story-Lab-Versuche. Wird niemals überschrieben — nur ergänzt.

```yaml
practice_log:
  - date: 2026-04-25
    style: ironie
    score_before: 7
    score_after: 8
    timing_wps: 2.4          # Wörter/Sekunde (Whisper)
    pause_before_punchline: 1.2s
    tonal_score: {enthusiasmus: 4, natuerlichkeit: 3, ueberzeugung: 4}
    feedback_summary: "Pause vor Pointe gut. Einstieg noch zu abstrakt."
```

### 1.3 Aktualisiertes PersonalFact-Template

```markdown
---
type: PersonalFact
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: raw | elaborated | story-ready
sensitivity: public | sensitive | private
story_score: 0
tags: []
sources: [raw/events/YYYY-MM-DDTHH-MM-SS_telegram.json]
related: []
social_context:
  when: ""
  audience: "Fremde | Freunde | gemischt"
  mood: ""
practice_log: []
---

# [Einprägsamer Titel]

## Kern-Fakt
[Die rohe Tatsache in 1-2 Sätzen. Konkret, ohne Ausschmückung.]

## Kontext
- **Wann:** 
- **Wo:** 
- **Mit wem:** 
- **Stimmung/Atmosphäre:** 

## Narrative Hook
[Was macht diesen Moment potenziell erzählenswert? Überraschung? Ironie? Universelle Anschlussfähigkeit?]

## Score-Begründung
- Überraschungsmoment (0–3): 
- Anschlussfähigkeit (0–3): 
- Sensorische Details (0–2): 
- Pointe/Wendung (0–2): 
- **Gesamt:** 

## Social Context
[Automatisch befüllt durch Diary-Agent beim Elaboration-Schritt]

## Korrelationen im Graph
[Links zu thematisch verwandten Facts, CulturalEntries oder Concepts]

## Ausarbeitung
[Leer bei status:raw — befüllt bei Elaboration]

## Übungsnotizen
[Leer bis status:story-ready — Feedback aus Story-Lab-Runden]
```

---

## 2. Bootstrap-Interview

### 2.1 Zweck

Bevor der Graph genug PersonalFacts hat um sich selbst zu bereichern, braucht der Nutzer einen Seed. Das Bootstrap-Interview ist ein strukturiertes Erstkontakt-Gespräch via Telegram — 10 Fragen, die gezielt erzählungswürdige Momente hervorrufen.

**Ziel:** 10–15 PersonalFacts im ersten Gespräch anlegen. Qualität vor Quantität — lieber 8 gute als 15 flache.

### 2.2 Die 10 Fragen

Drei Kategorien, jeweils mit zunehmendem "commitment" — von leicht zu persönlich.

#### Kategorie A — Humor & Peinlichkeit (sehr anschlussfähig)

> Fragen dieser Kategorie haben natürlich hohe Anschlussfähigkeit — jeder hat peinliche Momente. Ideal als Einstieg.

1. *"Was war dein peinlichster Moment in einer sozialen Situation? Erzähl so konkret wie möglich — wo warst du, wer war dabei?"*
2. *"Wann hast du zuletzt gelacht bis der Bauch wehtut? Was war der Auslöser?"*
3. *"Was ist das Dümmste das du je aus Versehen gemacht hast — und was ist dann passiert?"*

#### Kategorie B — Überraschung & Wendung (hoher story_score-Potential)

> Fragen dieser Kategorie zielen auf Erwartungsbrüche — das wichtigste Merkmal erzählungswürdiger Momente.

4. *"Wann warst du bei etwas erst komplett skeptisch — und am Ende begeistert oder überrascht?"*
5. *"Was war der unerwartetste Moment in deinem Leben in den letzten 2 Jahren?"*
6. *"Erzähl mir von einer Situation wo ein Fremder dich überrascht, bewegt oder überrumpelt hat."*
7. *"Wann hat etwas entweder viel besser oder viel schlechter funktioniert als du gedacht hast?"*

#### Kategorie C — Fähigkeiten & Meinungen (Gesprächsstarter)

> Fragen dieser Kategorie liefern "Visitenkarten-Facts" — kurze, prägnante Fakten über den Nutzer die Gespräche öffnen.

8. *"Was kannst du, das die meisten Leute überrascht wenn sie es erfahren?"*
9. *"Was ist eine Überzeugung oder Meinung von dir die die meisten Menschen nicht teilen?"*
10. *"Was war das Erste das du dir selbst beigebracht hast — und wie hast du das gemacht?"*

### 2.3 Interview-Flow via Telegram

```
Bot: Willkommen! Ich stelle dir 10 kurze Fragen um dein persönliches Wissens-Profil
     aufzubauen. Nimm dir Zeit, antworte so konkret wie möglich.
     Du kannst per Text oder Sprachnachricht antworten.

     [Starten]

→ Frage 1 wird gesendet
→ Nutzer antwortet (Text oder Voice)
→ Bot: kurze Bestätigung + nächste Frage ("Danke! Weiter:")
→ ... nach Frage 10:
→ Bot: "Alles gespeichert. Dein Graph hat jetzt einen ersten Kern." 
       + Zusammenfassung: "X PersonalFacts angelegt, davon Y mit score ≥ 6"
```

**ConversationHandler-States:**
```python
BOOTSTRAP_STATES = {
    "INTRO":     → zeigt Erklärung + Start-Button
    "Q1"..Q10":  → zeigt Frage, wartet auf Antwort (Text oder Voice)
    "SUMMARY":   → zeigt Ergebnis-Zusammenfassung
}
```

**Voice-Antworten im Bootstrap:** Whisper transkribiert, der transkribierte Text wird als `content` in das RawEvent geschrieben — identischer Flow wie bei normalen Telegram-Inputs.

### 2.4 Verarbeitungslogik: Antwort → PersonalFact

Jede Antwort durchläuft den normalen Ingest-Flow, aber mit einem zusätzlichen Kontext-Hint:

```json
{
  "source": "telegram",
  "source_type": "bootstrap_interview",
  "question_category": "B",
  "question_index": 5,
  "content": "[Antwort des Nutzers]",
  "user_hint": "bootstrap — direkt als PersonalFact verarbeiten"
}
```

Der `user_hint: "bootstrap"` überspringt die Klassifikations-Unsicherheit — der Supervisor weiß sofort: Diary Agent, PersonalFact erstellen, `story_score` berechnen.

**Besonderheit:** Im Bootstrap-Modus werden PersonalFacts direkt auf `main`-Branch geschrieben (kein Draft-Review). Grund: Bootstrap ist eine explizit vom Nutzer initiierte Aktion — die Freigabe ist implizit.

---

## 3. story_score — Scoring-Modell im Detail

### 3.1 Die vier Dimensionen

| Dimension            | Max | Frage                                              |
|----------------------|-----|----------------------------------------------------|
| Überraschungsmoment  | 3   | Wie unerwartet war das Ereignis?                   |
| Anschlussfähigkeit   | 3   | Kann jeder das nachfühlen?                         |
| Sensorische Details  | 2   | Gibt es konkrete, sinnliche Details?               |
| Pointe / Wendung     | 2   | Gibt es einen Erwartungsbruch am Ende?             |
| **Gesamt**           | **10** |                                                 |

**Kalibrierungs-Anker:**

| Score | Bedeutung                                                        |
|-------|------------------------------------------------------------------|
| 0–3   | Nicht erzählungswürdig. Archivieren oder als Kontext-Fakt nutzen.|
| 4–5   | Interessant als Hintergrund-Info, aber kein Gesprächs-Opener.   |
| 6–7   | Solide Geschichte. Funktioniert in passenden Gesprächen.         |
| 8–9   | Starke Geschichte. Öffnet Gespräche, bleibt in Erinnerung.      |
| 10    | Reserve-Klasse. Wird kaum vorkommen — Benchmarks: 9.            |

### 3.2 Haupt-Scoring-Prompt

```
Du bewertest einen persönlichen Moment auf sein Erzählpotential.
Kontext: Der Nutzer möchte in sozialen Gesprächen interessanter werden.

Personal Fact:
---
{core_fact}

Kontext: {context}
---

Bewerte auf vier Dimensionen. Begründe jeden Score in einem Satz.

1. ÜBERRASCHUNGSMOMENT (0–3)
   0 = vorhersehbar  |  1 = leicht unerwartet  |  2 = überraschend  |  3 = verblüffend
   Frage: "Hätte man dieses Ende vorhersehen können?"

2. ANSCHLUSSFÄHIGKEIT (0–3)
   0 = sehr persönlich/nischig  |  1 = nachvollziehbar  |  2 = universell  |  3 = "das kenne ich!"
   Frage: "Kann jemand der den Nutzer nicht kennt mitfühlen?"

3. SENSORISCHE DETAILS (0–2)
   0 = abstrakt, keine Details  |  1 = ein konkretes Bild  |  2 = lebhafte Details, man ist dabei
   Frage: "Kann der Zuhörer die Szene vor sich sehen?"

4. POINTE / WENDUNG (0–2)
   [Wird durch separaten Mini-Prompt berechnet — Ergebnis hier einfügen]

Antworte im Format:
ueberraschung: [0-3] | reason: [1 Satz]
anschlussfaehigkeit: [0-3] | reason: [1 Satz]
sensorik: [0-2] | reason: [1 Satz]
pointe: [0-2] | reason: [aus Mini-Prompt]
gesamt: [Summe]
narrative_hook: [1-2 Sätze — was ist das Erzählungswürdige an diesem Moment?]
```

### 3.3 Pointe-Mini-Prompt (dedizierter Schritt)

Die Pointe ist die schwierigste Dimension — sie erfordert einen separaten Fokus-Prompt. Dieser wird *vor* dem Haupt-Scoring ausgeführt, das Ergebnis wird in den Haupt-Prompt eingefügt.

```
Du analysierst ob ein persönlicher Moment eine Pointe oder Wendung hat.

Personal Fact:
---
{core_fact}
---

Frage 1: Was erwartet ein Zuhörer am Ende dieser Geschichte — basierend auf dem Anfang?
Frage 2: Was passiert stattdessen? Gibt es einen Erwartungsbruch, eine Ironie, eine Selbstentlarvung?

Score:
2 — Echter Erwartungsbruch. Das Ende ist überraschend, ironisch, oder selbstentlarvend.
    Das hätte der Zuhörer nicht vorhergesehen.
1 — Leichte Wendung. Kleine Ironie oder unerwartetes Detail, aber Ausgang grundsätzlich absehbar.
0 — Kein Erwartungsbruch. Das Ereignis endet wie es begonnen hat.

Antworte:
score: [0/1/2]
reason: [1 Satz — was genau ist die Wendung, oder warum fehlt sie?]
potential: [Falls score < 2: Wie könnte man eine Pointe herausarbeiten? 1 konkreter Satz.]
```

**Das `potential`-Feld** ist der Einstiegspunkt für die Elaboration: wenn die Pointe schwach ist, gibt der Agent einen konkreten Hinweis wie sie gestärkt werden kann.

### 3.4 Score-Beispiele zur Kalibrierung

```markdown
Beispiel A — score: 7
core_fact: "Ich war beim ersten Flamenco-Kurs. Der Lehrer hörte mittendrin auf,
            schaute mich an und sagte: 'Du denkst noch. Hör auf zu denken.'"
→ ueberraschung: 2 (direkte Ansage des Lehrers war unerwartet)
→ anschlussfaehigkeit: 3 ("zu viel denken" kennt jeder)
→ sensorik: 1 (Tanzschule, Gruppe, aber kein starkes Bild)
→ pointe: 1 (es hat funktioniert — leichte Wendung, aber absehbar)

Beispiel B — score: 4
core_fact: "Ich habe heute im Supermarkt die falsche Kasse gewählt und musste warten."
→ ueberraschung: 1  |  anschlussfaehigkeit: 2  |  sensorik: 0  |  pointe: 1

Beispiel C — score: 9
core_fact: "Ich habe meinem Chef erklärt warum seine Idee nicht funktioniert —
            mit seiner eigenen Präsentation vom letzten Quartal als Beweis."
→ ueberraschung: 3  |  anschlussfaehigkeit: 2  |  sensorik: 1  |  pointe: 3
```

---

## 4. Elaboration-Pipeline

### 4.1 Die drei Status-Stufen

```
raw          → elaborated        → story-ready
(extrahiert)   (ausgearbeitet)     (geübt, erzählbar)
```

| Status        | Was es bedeutet                                            | Wer ändert es              |
|---------------|------------------------------------------------------------|----------------------------|
| `raw`         | Fact extrahiert, story_score berechnet, Links gesetzt      | Diary Agent (automatisch)  |
| `elaborated`  | narrative_hook scharf, social_context befüllt, Ausarbeitung| Diary Agent (auf Trigger)  |
| `story-ready` | Mindestens 1 Story-Lab-Runde abgeschlossen, score ≥ 7      | Diary Agent (nach Übung)   |

### 4.2 Wann wird elaboriert?

```
Trigger A (automatisch):  story_score ≥ 6 AND status == "raw" → sofort elaborieren
Trigger B (Lint):         status == "raw" AND age > 7 Tage → Nutzer fragen
Trigger C (Nutzer):       Explizite Anfrage via Telegram
```

Trigger B sendet:
```
Bot: "Du hast einen Moment vom [Datum] noch nicht ausgearbeitet:
     '[Titel]' (score: X)
     Soll ich ihn ausarbeiten? [Ja] [Archivieren] [Später]"
```

### 4.3 Elaboration-Prompt

```
Du arbeitest einen persönlichen Moment zu einer erzählbaren Geschichte aus.
Du hast Zugriff auf den Nutzer-Graphen: {graph_context}

Personal Fact (raw):
---
title: {title}
core_fact: {core_fact}
context: {context}
story_score: {story_score}
pointe_potential: {potential_from_mini_prompt}
---

Aufgabe:
1. Schreibe eine "Ausarbeitung" in 3-5 Sätzen — die Geschichte so erzählt wie der Nutzer
   sie einem Freund erzählen würde. Natürliche Sprache, kein Aufsatz-Stil.
2. Schärfe den narrative_hook: 1-2 Sätze die das Kern-Interessante benennen.
3. Schlage social_context vor: wann und für wen eignet sich diese Geschichte?
4. Falls pointe_potential vorhanden: baue die Pointe in die Ausarbeitung ein.
5. Suche in graph_context nach 2-3 sinnvollen Links (related).

Antworte im Format:
ausarbeitung: [3-5 Sätze, direkte Sprache]
narrative_hook: [1-2 Sätze]
social_context_when: [Situations-Beschreibung]
social_context_mood: [locker | tiefgründig | humorvoll | gemischt]
related: [Liste von Wiki-Links]
story_score_revision: [neuer Score falls Elaboration Pointe gestärkt hat, sonst leer]
```

---

## 5. Korrelations-Engine

### 5.1 Zweck

Die Korrelations-Engine erkennt thematische Muster zwischen PersonalFacts — und macht daraus sichtbares Wissen: *"Du hast 3 Erlebnisse die alle mit dem Thema 'außerhalb der Komfortzone' zu tun haben."*

Das ist wertvoller als isolierte Fakten.

### 5.2 Algorithmus

```python
# agents/diary_agent.py

def find_correlations(new_fact: WikiPage, graph_context: list[WikiPage]) -> CorrelationResult:
    """Läuft nach jedem neuen PersonalFact-Ingest."""
    
    # Schritt 1: Kandidaten aus graph_context filtern (Haiku, günstig)
    candidates = [
        p for p in graph_context
        if p.type == "PersonalFact"
        and _tag_overlap_score(new_fact.tags, p.tags) >= TAG_OVERLAP_THRESHOLD  # default: 2
    ]
    
    # Schritt 2: Semantische Cluster-Analyse auf Kandidaten (Sonnet, nur wenn nötig)
    if candidates:
        clusters = _analyze_clusters(new_fact, candidates)  # Sonnet
        return CorrelationResult(
            related_facts=candidates,
            clusters=clusters,
            concept_suggestion=_suggest_concept(clusters) if len(candidates) >= 3 else None
        )
    
    return CorrelationResult(related_facts=[], clusters=[], concept_suggestion=None)


TAG_OVERLAP_THRESHOLD = 2  # mindestens 2 gemeinsame Tags für Kandidaten-Status
CONCEPT_THRESHOLD = 3      # ab 3 korrelierten Facts → Concept-Seite vorschlagen
```

### 5.3 Cluster-Analyse-Prompt (Sonnet)

```
Du analysierst ob mehrere persönliche Momente eines Nutzers ein gemeinsames Muster haben.

Neuer Fact: {new_fact}
Verwandte Facts: {candidates}

Fragen:
1. Was verbindet diese Momente thematisch? (1 Satz)
2. Gibt es ein übergreifendes Thema oder eine Entwicklung die sich abzeichnet?
3. Hat sich die Einstellung/Reaktion des Nutzers über die Facts verändert?

Falls 3+ Facts dasselbe Kernthema teilen: Schlage einen Concept-Seiten-Titel vor.
Format: "Mein [Thema]-Weg" oder "[Thema] als roter Faden"

Antworte:
verbindung: [1 Satz]
entwicklung: [1 Satz, oder "noch nicht erkennbar"]
concept_title: [Vorschlag oder null]
concept_summary: [2-3 Sätze falls concept_title nicht null]
```

### 5.4 Automatische Concept-Seiten

Wenn `concept_suggestion` nicht null und `len(related_facts) >= CONCEPT_THRESHOLD`:

```
Supervisor → Telegram:
┌─────────────────────────────────────────────────────────┐
│  🔗 Muster erkannt                                       │
│                                                         │
│  3 Erlebnisse teilen ein Thema: "Mein Flamenco-Weg"    │
│  → pf_erste-flamenco-show                              │
│  → pf_flamenco-kurs-lehrer                             │
│  → [neuer Fact]                                         │
│                                                         │
│  Soll ich eine Concept-Seite "Mein Flamenco-Weg"        │
│  anlegen die diese Facts verbindet?                     │
│                                                         │
│  [Ja, anlegen]  [Nein]  [Titel ändern]                 │
└─────────────────────────────────────────────────────────┘
```

Concept-Seiten haben kein `story_score` — sie sind Navigations- und Bedeutungs-Anker, keine Geschichten.

### 5.5 Wöchentlicher Korrelations-Scan (Lint)

Zusätzlich zum per-Ingest-Scan läuft der Lint-Agent wöchentlich über alle PersonalFacts:

```python
def weekly_correlation_scan(all_facts: list[WikiPage]) -> list[CorrelationResult]:
    """Findet Muster die beim einzelnen Ingest nicht sichtbar waren."""
    # Alle Fact-Paare mit Tag-Overlap ≥ 2
    # Cluster-Analyse auf Gruppen ≥ 3
    # Flaggt neue Concept-Vorschläge die noch nicht existieren
```

---

## 6. Story-Lab

### 6.1 Konzept: Voice-First Coaching

Story-Lab ist kein starrer Coaching-Flow — es ist ein **Experiment-Raum**. Der Nutzer probiert denselben Fact in verschiedenen Stilen aus, nimmt sich auf (Sprachnachricht), und bekommt kombiniertes Feedback aus Timing-Analyse und Ton-Analyse.

```
Fact + Stil-Karte → Nutzer nimmt auf → Whisper + Claude Audio → Feedback → (nächster Versuch?)
```

Ziel: nicht der "perfekte" Vortrag, sondern das Finden des eigenen Stils der natürlich und stark ist.

### 6.2 Story-Lab Trigger

```
Trigger A (Lint):   story_score ≥ 7 AND status != "story-ready" AND age > 14 Tage
Trigger B (Nutzer): "üben" / "/story" via Telegram
Trigger C (Impuls-Follow-up): Nutzer antwortete auf Impuls, Fact hat score ≥ 7
```

### 6.3 Die vier Stil-Karten

Der Agent wählt eine passende Stil-Karte basierend auf den Fact-Eigenschaften — oder der Nutzer wählt manuell.

```
┌─────────────────────────────────────────────────────────┐
│  🎭 IRONIE-STIL                                          │
│  Prinzip: Erwartung aufbauen → brechen                  │
│  Struktur: "Ich dachte X... aber dann..."               │
│  Passt für: Facts mit starker Pointe (score ≥ 1)        │
│  Comedian-Referenz: Setup → Subversion → Resolution     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  ⚡ DIREKTSTIL                                           │
│  Prinzip: Pointe zuerst, dann Kontext                   │
│  Struktur: "Das Lustigste/Kurioseste: [Pointe].         │
│             Hier ist wie es dazu kam..."                │
│  Passt für: Gespräche wo Zeit fehlt, Elevator-Pitch     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  🪞 SELBSTIRONIE-STIL                                    │
│  Prinzip: Nutzer ist selbst die Pointe                  │
│  Struktur: Eigene Fehler/Naivität betonen, dann Wendung │
│  Passt für: Peinlichkeits-Facts, Lern-Momente           │
│  Sozial: baut Vertrauen auf, signalisiert Selbstbewusstsein│
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  📈 AUFBAU-STIL                                          │
│  Prinzip: Langsame Eskalation mit sensorischen Details  │
│  Struktur: Szene setzen → Spannung aufbauen → Auflösung │
│  Passt für: Facts mit hoher Sensorik (score ≥ 1)        │
│  Länger, für Gespräche wo Zeit vorhanden ist            │
└─────────────────────────────────────────────────────────┘
```

**Stil-Auswahl-Logik:**
```python
def suggest_style(fact: WikiPage) -> str:
    if fact.story_score_dimensions["pointe"] >= 2:
        return "ironie"
    elif fact.story_score_dimensions["anschlussfaehigkeit"] == 3:
        return "selbstironie"
    elif fact.story_score_dimensions["sensorik"] >= 2:
        return "aufbau"
    else:
        return "direkt"
```

### 6.4 Story-Lab ConversationHandler

```python
STORY_LAB_STATES = {
    "STYLE_PRESENT",   # Bot zeigt Fact + empfohlene Stil-Karte
    "STYLE_CONFIRM",   # Nutzer bestätigt Stil oder wählt anderen
    "AWAIT_VOICE",     # Bot wartet auf Sprachnachricht
    "ANALYSIS",        # Intern: Whisper Timing + Transkript-Qualitätsanalyse (kein User-Input)
    "FEEDBACK",        # Bot zeigt kombiniertes Feedback
    "RETRY_PROMPT",    # Bot fragt: anderer Stil? nochmal? fertig?
    "COMPARE",         # Falls ≥ 2 Versuche: Vergleich der Versionen
    "CLOSE",           # Status auf story-ready setzen, practice_log updaten
}
```

**Beispiel-Ablauf:**

```
Bot: "Übungsrunde: 'Flamenco-Kurs: Der Lehrer und das Duende' (score: 7)
     
     Empfohlener Stil: 🪞 Selbstironie — du dachtest du kannst tanzen, aber...
     
     [Diesen Stil]  [Anderen Stil wählen]  [Abbrechen]"

Nutzer: [Diesen Stil]

Bot: "Nimm dich auf. Erzähl die Geschichte im Selbstironie-Stil — 30-60 Sekunden.
     Du denkst noch. Hör auf zu denken. 🙂"
     
     [Nutzer sendet Sprachnachricht]

Bot: "⏳ Analysiere..."
     [Whisper + Claude Audio läuft intern]

Bot: "📊 Deine Version:
     
     Timing:   Pacing gut (2.1 Wörter/Sek) ✓
               Pause vor Pointe: 0.8 Sek — etwas kurz, 1.5s wäre stärker
     
     Transkript: Struktur: 4/5 ✓
               Klarheit: 3/5 — Einstieg etwas unklar
               Überzeugungskraft: 4/5 ✓
     
     Coaching: 'Lass nach dem Satz des Lehrers eine längere Stille —
                das ist der Moment der zieht.'
     
     [Anderer Stil]  [Nochmal]  [Fertig — story-ready]"

Nutzer: [Anderer Stil → Ironie]

Bot: [Ironie-Stil Instruktion...]
     [Nutzer nimmt nochmal auf]
     ...

Bot: "Vergleich:
     Versuch 1 (Selbstironie): Natürlicher, aber Pause fehlt
     Versuch 2 (Ironie):       Struktur klarer, Einstieg besser
     
     Empfehlung: Ironie-Struktur + Pausen-Timing aus Versuch 1 kombinieren."
```

### 6.5 Zweistufige Voice-Analyse

#### Stufe 1 — Whisper Timing-Analyse (lokal, kostenlos)

```python
# agents/diary_agent.py

def analyze_timing(segments: list[Segment]) -> TimingReport:
    words_per_second = [
        len(s.text.split()) / max(s.end - s.start, 0.1)
        for s in segments
    ]
    pauses = [
        segments[i+1].start - segments[i].end
        for i in range(len(segments) - 1)
    ]
    
    # Pointe-Bereich = letztes Drittel der Aufnahme
    total_duration = segments[-1].end - segments[0].start
    punchline_start = total_duration * 0.67
    
    pre_punchline_pause = max(
        [p for p, s in zip(pauses, segments[:-1]) if s.end > punchline_start],
        default=0.0
    )
    
    return TimingReport(
        avg_words_per_second=mean(words_per_second),
        pre_punchline_pause_seconds=pre_punchline_pause,
        energy_curve=words_per_second,         # steigt zum Ende?
        total_duration_seconds=total_duration,
    )
```

#### Stufe 2 — Transkript-Qualitätsanalyse (Struktur & Erzählqualität)

> **V1-Einschränkung:** Claude API unterstützt kein Audio-Input (OGG/MP3). Tonalitätswerte
> (Enthusiasmus, Natürlichkeit) sind in V1 nicht verfügbar. Stufe 2 analysiert stattdessen
> den Whisper-Transkripttext auf Erzählstruktur und Verbesserungspotential.
> Audio-Analyse folgt wenn eine Audio-API verfügbar ist.

```python
TRANSCRIPT_QUALITY_PROMPT = """
Analysiere dieses Transkript einer mündlich erzählten Geschichte.
Der Sprecher versucht einen persönlichen Moment natürlich zu erzählen.

Transkript:
---
{transcript}
---

Bewerte auf einer Skala 1–5:
- struktur:      Gibt es einen klaren Aufbau (Einstieg → Mitte → Pointe)?
- klarheit:      Ist die Geschichte verständlich ohne Vorwissen?
- ueberzeugung:  Würde ein Zuhörer der Geschichte folgen wollen?

Zusatz:
- pointe_erkennbar: Ist die Pointe/Wendung klar erkennbar im Transkript?
  (ja / schwach / nein)

Antworte im Format:
struktur: [1-5]
klarheit: [1-5]
ueberzeugung: [1-5]
pointe_erkennbar: [ja | schwach | nein]
empfehlung: [1 konkreter Satz — was würde die nächste Version stärker machen?]
"""

def analyze_transcript_quality(transcript_text: str, fact: WikiPage) -> TranscriptQualityReport:
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        messages=[{
            "role": "user",
            "content": TRANSCRIPT_QUALITY_PROMPT.format(transcript=transcript_text[:2000])
        }]
    )
    return _parse_transcript_quality_report(response.content[0].text)
```

#### Kombiniertes Feedback

```python
def generate_story_lab_feedback(
    timing: TimingReport,
    tonal: TonalReport,
    style: str,
    fact: WikiPage,
    style_profile: StyleProfile | None = None,  # aktives StyleProfile, falls gesetzt
) -> str:
    """Kombiniert Timing + Ton + StyleProfile-Vergleich zu lesbarem Feedback."""
    
    feedback_lines = []
    ref_name = f"[{style_profile.name}]" if style_profile else "[Standard]"
    ref_pause = style_profile.avg_pause_before_punchline if style_profile else 1.5
    ref_wps   = style_profile.avg_words_per_second       if style_profile else 2.2
    
    # Timing-Bewertung
    wps_delta = timing.avg_words_per_second - ref_wps
    if wps_delta > 0.4:
        feedback_lines.append(f"Pacing: {timing.avg_words_per_second:.1f} Wörter/Sek — etwas schnell. {ref_name}: {ref_wps:.1f}")
    elif wps_delta < -0.4:
        feedback_lines.append(f"Pacing: {timing.avg_words_per_second:.1f} Wörter/Sek — etwas langsam. {ref_name}: {ref_wps:.1f}")
    else:
        feedback_lines.append(f"Pacing: {timing.avg_words_per_second:.1f} Wörter/Sek ✓")
    
    # Pointe-Pause mit StyleProfile-Vergleich
    pause_delta = ref_pause - timing.pre_punchline_pause_seconds
    if pause_delta > 0.5:
        feedback_lines.append(
            f"Pause vor Pointe: {timing.pre_punchline_pause_seconds:.1f}s — "
            f"{ref_name} pausiert {ref_pause:.1f}s. Lass das {pause_delta:.1f}s länger wirken."
        )
    else:
        feedback_lines.append(f"Pause vor Pointe: {timing.pre_punchline_pause_seconds:.1f}s ✓")
    
    # StyleProfile-Kern-Muster als konkreter Tipp
    if style_profile and style_profile.confidence >= 0.5 and style_profile.key_patterns:
        feedback_lines.append(f"Stil-Tipp {ref_name}: '{style_profile.key_patterns[0]}'")
    
    # Tonal
    feedback_lines.append(f"Ton: {tonal.empfehlung}")
    
    return "\n".join(feedback_lines)
```

---

## 7. Impuls

### 7.1 Konzept

Impuls ist der Gegenpol zu Story-Lab: **kein Coaching, sondern Anregung**. Der Bot greift in den Graphen, kombiniert Elemente zu einer unerwarteten Sprech-Aufforderung, und sendet sie an den Nutzer. Antwort ist freiwillig — aber wenn geantwortet wird, fließt die Aufnahme in den Graphen zurück.

**Ziel:** Der Nutzer wird täglich zum Sprechen angeregt — über seinen Alltag, seine Sprache, seine Erlebnisse. Das Graph-Wissen bleibt lebendig, nicht nur gespeichert.

### 7.2 Die acht Kombinations-Typen

```python
IMPULS_TYPES = {

    "emotion_vocab": {
        # Graph-Zutaten: Emotion (Liste) + VocabEntry
        "description": "Spreche über einen Moment mit einer bestimmten Emotion — benutze ein Vokabel dabei",
        "example": "Erzähl 30 Sek. über einen **glücklichen** Moment — benutze dabei 'madrugada' natürlich.",
        "language": "de",  # kann auch "es" oder "mix" sein
        "duration": "30 Sekunden",
        "difficulty": "warm-up",
    },

    "image_react": {
        # Graph-Zutaten: GIF/Bild (aus Telegram-GIF-API oder raw/assets/) + Sprache
        "description": "Reagiere auf ein Bild oder GIF — auf Spanisch",
        "example": "[Bot sendet GIF] Beschreib was passiert — auf Spanisch, 20 Sekunden.",
        "language": "es",
        "duration": "20 Sekunden",
        "difficulty": "warm-up",
    },

    "fact_retell": {
        # Graph-Zutaten: PersonalFact (zufällig, score ≥ 5) + Sprache
        "description": "Erzähle einen bekannten Fact in einer anderen Sprache",
        "example": "Erzähl die Geschichte vom Flamenco-Kurs — diesmal auf Spanisch.",
        "language": "es",
        "duration": "1 Minute",
        "difficulty": "challenge",
    },

    "fact_bridge": {
        # Graph-Zutaten: 2 PersonalFacts mit niedrigem Tag-Overlap
        "description": "Finde eine Verbindung zwischen zwei scheinbar unverwandten Erlebnissen",
        "example": "Was haben dein Fahrrad-Unfall und der Flamenco-Kurs gemeinsam? 1 Minute.",
        "language": "de",
        "duration": "1 Minute",
        "difficulty": "challenge",
    },

    "situation": {
        # Graph-Zutaten: CulturalEntry (Land/Ort) + social_context eines PersonalFacts
        "description": "Improvisiere in einer konkreten sozialen Situation",
        "example": "Du bist auf einer Party in Madrid. Jemand fragt warum du Spanisch lernst. Antworte spontan.",
        "language": "mix",
        "duration": "45 Sekunden",
        "difficulty": "challenge",
    },

    "transcript_react": {
        # Graph-Zutaten: Ausschnitt aus raw/sources/ (YouTube-Transcript, Artikel)
        "description": "Erkläre einem Freund was du gerade gehört/gelesen hast",
        "example": "[Bot sendet Transcript-Ausschnitt] Erkläre das jemandem der es nicht kennt — 1 Minute.",
        "language": "de",
        "duration": "1-2 Minuten",
        "difficulty": "deep",
    },

    "debate": {
        # Graph-Zutaten: Concept + konträre Aussage
        "description": "Reagiere auf eine provokante Aussage zu einem deiner Interessen",
        "example": "Jemand sagt: 'Flamenco ist nur für alte Leute.' Antworte spontan.",
        "language": "de",
        "duration": "45 Sekunden",
        "difficulty": "challenge",
    },

    "codemix": {
        # Graph-Zutaten: 3 VocabEntries (status: elaborated) + freies Thema
        "description": "Erzähle frei — aber benutze mindestens 3 Spanisch-Wörter natürlich",
        "example": "Erzähl wie dein Tag war — benutze dabei: duende, madrugada, otra vez.",
        "language": "mix",
        "duration": "1 Minute",
        "difficulty": "warm-up",
    },
}
```

### 7.3 Impuls-Generator-Algorithmus

```python
def generate_impuls(graph_context: GraphContext, user_profile: dict) -> Impuls:
    """Wählt Typ und Zutaten, generiert konkreten Prompt-Text."""
    
    # Typ-Auswahl: gewichtet nach Situation
    hour = datetime.now().hour
    if hour < 9:
        # Morgens: einfacher Warm-Up
        impuls_type = random.choice(["emotion_vocab", "codemix", "image_react"])
    elif hour < 18:
        # Tagsüber: mittlere Schwierigkeit
        impuls_type = random.choice(["fact_retell", "situation", "debate"])
    else:
        # Abends: reflection-orientiert
        impuls_type = random.choice(["fact_bridge", "transcript_react", "codemix"])
    
    # Zutaten aus Graph
    ingredients = _select_ingredients(impuls_type, graph_context)
    
    # Prompt-Text generieren (Haiku — Template-Kombinatorik)
    prompt_text = _render_impuls_prompt(impuls_type, ingredients, user_profile)
    
    return Impuls(
        type=impuls_type,
        components=ingredients,
        prompt_text=prompt_text,
        telegram_media=_get_media(impuls_type, ingredients),
        duration_hint=IMPULS_TYPES[impuls_type]["duration"],
        difficulty=IMPULS_TYPES[impuls_type]["difficulty"],
        language=IMPULS_TYPES[impuls_type]["language"],
        graph_refs=[i.page_path for i in ingredients.values() if hasattr(i, "page_path")],
    )
```

### 7.4 Trigger & Frequenz

```
Täglich:   1 Impuls zur zufälligen Tageszeit (zwischen 08:00–20:00 Uhr)
Optional:  Nutzer kann via "/impuls" jederzeit einen neuen anfordern
Pause:     Kein Impuls wenn aktive Story-Lab-Session läuft
```

### 7.5 Analyse nach Antwort: Datenspeicherung & vollständiges Feedback

Jede Impuls-Antwort durchläuft **dieselbe Analyse-Pipeline wie Story-Lab** — inklusive vollem Feedback. Zusätzlich wird typ-spezifisch in den Graph zurückgeschrieben.

#### Schritt 1 — Immer: RawEvent speichern

```json
// raw/events/TIMESTAMP_impuls-response.json
{
  "source": "telegram",
  "source_type": "impuls_response",
  "impuls_type": "fact_retell",
  "impuls_id": "imp_20260418_143200",
  "referenced_facts": ["wiki/personal/facts/pf_2026-04-18_flamenco-kurs-lehrer.md"],
  "audio_path": "raw/assets/2026-04-18T14-32-00_voice.ogg",
  "content": "[Whisper-Transkript]",
  "processed": false
}
```

Das RawEvent ist unveränderlich — alle weiteren Schritte lesen daraus.

#### Schritt 2 — Volles Feedback (identisch zu Story-Lab)

```python
def process_impuls_response(
    voice_ogg: Path,
    impuls: Impuls,
    active_style_profile: StyleProfile | None,
) -> None:
    # Whisper: Transkript + Timing
    transcript = whisper_model.transcribe(voice_ogg)
    timing     = analyze_timing(transcript.segments)
    
    # Transkript-Qualitätsanalyse (V1: text-only; Audio-Tonalität folgt in V2)
    tonal = analyze_transcript_quality(transcript.text, impuls)
    
    # Feedback mit StyleProfile-Vergleich — kein abgeschwächtes "Light-Feedback"
    feedback = generate_story_lab_feedback(
        timing, tonal, impuls.type, active_style_profile
    )
    send_telegram_message(feedback)
    
    # Typ-spezifisches Graph-Routing (Schritt 3)
    _route_to_graph(transcript, timing, tonal, impuls)
```

#### Schritt 3 — Typ-spezifisches Graph-Routing

| Impuls-Typ | Was gespeichert wird | Wo |
|---|---|---|
| `fact_retell` | practice_log-Eintrag (timing + tonal + context) | referenzierter PersonalFact |
| `situation` / `debate` | Neuer PersonalFact falls Diary-Agent story_score ≥ 5 | wiki/personal/facts/ |
| `fact_bridge` | Korrelations-Update, ggf. Concept-Seiten-Vorschlag | Korrelations-Engine |
| `codemix` / `emotion_vocab` | VocabEntry-Nutzungsstatistik, Anki-Streak-Update | VocabEntries |
| `transcript_react` | Concept-Seiten-Anreicherung (Nutzer-Erklärung als Quelle) | wiki/concepts/ |
| `image_react` | Kein Graph-Write — nur Feedback | — |

```python
def _route_to_graph(transcript, timing, tonal, impuls: Impuls) -> None:
    match impuls.type:
        case "fact_retell":
            append_practice_log(
                fact_path=impuls.graph_refs[0],
                timing=timing, tonal=tonal,
                context=f"impuls:{impuls.type}",
            )
        
        case "situation" | "debate":
            # Improv → normaler Ingest: Diary Agent entscheidet ob PersonalFact
            diary_agent.ingest(raw_event_from_transcript(transcript, impuls))
        
        case "fact_bridge":
            correlation_agent.process_bridge_insight(
                transcript.text, impuls.graph_refs
            )
        
        case "codemix" | "emotion_vocab":
            for vocab in _find_vocab_in_transcript(transcript.text):
                update_vocab_usage(vocab)
            if impuls.type == "codemix":
                _check_codemix_completion(
                    transcript.text, impuls.components["vocab_entries"]
                )
        
        case "transcript_react":
            concept_agent.enrich_from_explanation(
                transcript.text, impuls.graph_refs
            )
```

---

## 8. Style References

### 8.1 Konzept

Style References sind Medien-Sammlungen aus denen das System einen persönlichen Stil-Benchmark extrahiert. Der Nutzer legt Clips, Transcripts oder Texte ab — das System analysiert jedes Einzelstück und aggregiert daraus ein **StyleProfile** mit steigender Konfidenz je mehr Beispiele vorhanden sind.

```
1 Clip  → StyleFingerprint (einzeln)   → confidence: low
3 Clips → StyleProfile (aggregiert)    → confidence: medium
5+ Clips → StyleProfile (konsolidiert) → confidence: high → zuverlässiger Benchmark
```

Mehr Beispiele desselben Stils = niedrigere Varianz = präziserer Benchmark für Feedback.

### 8.2 Quell-Wege

**Weg A — Datei-Drop:**
```
raw/style_refs/[name]/   ← Nutzer legt Clips hier ab
  chappelle/
    clip_01.mp4
    clip_02.mp3
    transcript_03.txt    ← auch Text-Transcripts möglich
  ted-talk/
    talk_01.mp4
```
File-Watcher (watchdog) erkennt neue Dateien → Extraktion startet automatisch.

**Weg B — Telegram:**
```
Nutzer sendet: [Video/Audio/Text] + "#stilreferenz chappelle"
→ Extractor speichert in raw/style_refs/chappelle/
→ StyleFingerprint-Extraktion startet
→ StyleProfile für "chappelle" wird aktualisiert
```

### 8.3 StyleFingerprint — Extraktion pro Clip

Jedes Einzelstück erzeugt einen `StyleFingerprint`. Unterstützte Formate:

| Format | Extraktion | Was analysiert wird |
|---|---|---|
| Video (mp4, mov) | ffmpeg → Audio → Whisper | Timing, Pacing, Pausen |
| Audio (mp3, ogg, m4a) | Whisper direkt | Timing, Pacing, Pausen |
| Text (Transcript, Artikel) | direkt | Struktur, Setup/Pointe-Ratio, Muster |
| YouTube-Link + `#stilreferenz` | youtube-transcript-api | Struktur (kein Audio-Timing) |

```python
class StyleFingerprint(TypedDict):
    source_path: str
    source_type: str                  # "video" | "audio" | "text" | "youtube"
    
    # Timing (nur bei Audio/Video, via Whisper-Timestamps)
    avg_words_per_second: float | None
    avg_pause_before_punchline: float | None
    energy_curve_slope: float | None  # positiv = steigt zum Ende
    
    # Struktur (alle Formate, via Sonnet-Analyse)
    setup_ratio: float                # Anteil Aufbau vs. Pointe (0.0–1.0)
    avg_sentence_length: float        # kürzere Sätze = direkterer Stil
    key_patterns: list[str]           # Muster die Sonnet identifiziert
    style_tags: list[str]             # z.B. ["selbstironie", "slow-burn", "callbacks"]
```

**Sonnet-Prompt für Struktur-Analyse:**
```
Analysiere dieses Stück (Transcript oder Text) auf Erzählstil.

Inhalt:
---
{content}
---

Extrahiere:
1. setup_ratio: Wie viel Prozent ist Aufbau, wie viel Auflösung/Pointe? (0.0 = nur Pointe, 1.0 = nur Aufbau)
2. avg_sentence_length: durchschnittliche Satzlänge in Wörtern (grob schätzen)
3. key_patterns: Liste von 3-5 Mustern die diesen Stil definieren.
   Format: kurze Imperative. Beispiel: "Pause nach dem Hauptsatz", "Erste Person als Selbstentwaffnung"
4. style_tags: 2-4 kurze Labels. Beispiel: ["selbstironie", "slow-burn"]

Antworte im Format:
setup_ratio: [0.0–1.0]
avg_sentence_length: [Zahl]
key_patterns: ["...", "...", "..."]
style_tags: ["...", "..."]
```

### 8.4 StyleProfile — Aggregation über mehrere Clips

Das StyleProfile aggregiert alle Fingerprints unter demselben Namen:

```python
class StyleProfile(TypedDict):
    name: str                              # z.B. "chappelle"
    sources: list[str]                     # alle beitragenden Dateipfade
    sample_count: int
    confidence: float                      # 0.0–1.0, steigt mit sample_count
    
    # Gemittelte Timing-Werte (nur wenn Audio-Samples vorhanden)
    avg_words_per_second: float | None
    avg_pause_before_punchline: float | None
    
    # Konsolidierte Struktur
    setup_ratio: float                     # Mittelwert über alle Samples
    key_patterns: list[str]               # Muster die in Mehrheit der Clips vorkommen
    style_tags: list[str]                 # Tags mit Häufigkeit ≥ 50% der Clips


CONFIDENCE_THRESHOLDS = {
    1: 0.25,   # 1 Sample  → niedrig
    3: 0.60,   # 3 Samples → medium — ab hier für Feedback nutzbar
    5: 0.85,   # 5 Samples → hoch
    8: 1.00,   # 8+ Samples → maximum
}

def aggregate_style_profile(name: str, fingerprints: list[StyleFingerprint]) -> StyleProfile:
    n = len(fingerprints)
    audio_fps = [fp for fp in fingerprints if fp["avg_words_per_second"] is not None]
    
    # Timing: nur über Audio-Samples mitteln
    avg_wps   = mean([fp["avg_words_per_second"] for fp in audio_fps]) if audio_fps else None
    avg_pause = mean([fp["avg_pause_before_punchline"] for fp in audio_fps]) if audio_fps else None
    
    # key_patterns: nur Muster die in ≥50% der Clips vorkommen
    all_patterns = [p for fp in fingerprints for p in fp["key_patterns"]]
    core_patterns = [p for p in set(all_patterns) if all_patterns.count(p) >= n * 0.5]
    
    return StyleProfile(
        name=name,
        sources=[fp["source_path"] for fp in fingerprints],
        sample_count=n,
        confidence=CONFIDENCE_THRESHOLDS.get(min(n, 8), 1.0),
        avg_words_per_second=avg_wps,
        avg_pause_before_punchline=avg_pause,
        setup_ratio=mean([fp["setup_ratio"] for fp in fingerprints]),
        key_patterns=core_patterns,
        style_tags=_majority_tags(fingerprints, threshold=0.5),
    )
```

### 8.5 StyleProfile als Wiki-Seite

Jedes StyleProfile wird als Seite im Knowledge Graph gespeichert:

```markdown
---
type: StyleProfile
created: YYYY-MM-DD
updated: YYYY-MM-DD
name: chappelle
sample_count: 5
confidence: 0.85
avg_words_per_second: 2.1
avg_pause_before_punchline: 2.3
setup_ratio: 0.62
style_tags: [selbstironie, slow-burn, callbacks]
sources:
  - raw/style_refs/chappelle/clip_01.mp4
  - raw/style_refs/chappelle/clip_02.mp3
  - raw/style_refs/chappelle/clip_03.mp4
  - raw/style_refs/chappelle/clip_04.mp4
  - raw/style_refs/chappelle/transcript_05.txt
---

# Style Reference: chappelle

## Kern-Muster
1. Pause nach dem Hauptsatz — Pointe kommt erst nach der Stille
2. Selbstentwaffnung als Einstieg — "Ich bin so jemand der..."
3. Callback zur ersten Szene am Ende
4. Kurze Hauptsätze, kein Nebensatz vor der Pointe

## Timing-Profil
- Sprechtempo: 2.1 Wörter/Sek (gemessen über 4 Audio-Samples)
- Pause vor Pointe: Ø 2.3s
- Energie-Kurve: steigt zum Ende (positiver Slope)

## Konfidenz
5 Samples → confidence: 0.85. Ab 3 weiteren Samples → maximum.
```

Lebt in `wiki/personal/style_refs/sp_[name].md`.

### 8.6 Aktives StyleProfile setzen

Der Nutzer wählt welches StyleProfile für Feedback aktiv ist:

```
Nutzer: "/stil chappelle"
Bot:    "StyleProfile 'chappelle' aktiv (confidence: 0.85, 5 Samples).
         Alle Story-Lab und Impuls-Bewertungen vergleichen jetzt mit diesem Stil."

Nutzer: "/stil"
Bot:    "Aktiv: chappelle | Verfügbar: ted-talk (3 Samples), seinfeld (1 Sample)
         [chappelle] [ted-talk] [seinfeld] [Standard]"
```

Das aktive StyleProfile wird in `user_profile.md` gespeichert:
```yaml
active_style_profile: "chappelle"   # null = Standard-Benchmark
```

### 8.7 Verknüpfung mit PersonalFacts

StyleProfiles verlinken auf PersonalFacts die mit ihnen geübt wurden — und umgekehrt:

```yaml
# practice_log Eintrag in einem PersonalFact
- date: 2026-04-25
  style: ironie
  style_profile_ref: "[[sp_chappelle]]"   # welches Profil aktiv war
  score_before: 7
  score_after: 8
  ...
```

Das erlaubt später: *"Welche Facts habe ich im Chappelle-Stil geübt, und wie hat sich der Score entwickelt?"*

---

## 9. Diary-Agent-Implementierung

### 8.1 State-Erweiterung

Der `SupervisorState` aus ARCHITECTURE.md §3.2 wird um Diary-spezifische Felder erweitert:

```python
class DiaryAgentState(TypedDict):
    # Vom Supervisor übernommen
    raw_event: RawEvent
    user_profile: dict
    graph_context: list[WikiPage]
    
    # Diary-spezifisch
    extracted_fact: dict | None        # Roh-Extraktion aus dem Input
    story_score_result: dict | None    # Ergebnis aus Scoring-Prompts
    correlation_result: CorrelationResult | None
    elaboration_result: dict | None
    impuls: Impuls | None
    
    # Output
    wiki_writes: list[WikiWrite]       # neue/aktualisierte Seiten
    telegram_messages: list[str]       # Nachrichten an Nutzer
```

### 8.2 LangGraph-Nodes (Diary Flow)

```python
# agents/diary_agent.py

diary_workflow = StateGraph(DiaryAgentState)

diary_workflow.add_node("extract_fact",       extract_fact_from_event)
diary_workflow.add_node("score_punchline",    run_punchline_mini_prompt)   # Haiku
diary_workflow.add_node("score_main",         run_main_scoring_prompt)     # Sonnet
diary_workflow.add_node("find_correlations",  find_correlations)           # Haiku + opt. Sonnet
diary_workflow.add_node("elaborate",          elaborate_if_needed)         # Sonnet, conditional
diary_workflow.add_node("write_fact",         write_personal_fact)

diary_workflow.set_entry_point("extract_fact")
diary_workflow.add_edge("extract_fact",    "score_punchline")
diary_workflow.add_edge("score_punchline", "score_main")
diary_workflow.add_edge("score_main",      "find_correlations")

diary_workflow.add_conditional_edges(
    "find_correlations",
    lambda s: "elaborate" if s["story_score_result"]["gesamt"] >= 6 else "write_fact",
    {"elaborate": "elaborate", "write_fact": "write_fact"}
)

diary_workflow.add_edge("elaborate", "write_fact")
diary_workflow.add_edge("write_fact", END)
```

### 8.3 Node-Übersicht

| Node                | Modell    | Input                          | Output                              |
|---------------------|-----------|--------------------------------|-------------------------------------|
| `extract_fact`      | Haiku     | raw_event, user_profile        | extracted_fact (Felder des Templates)|
| `score_punchline`   | Haiku     | core_fact                      | pointe_score + potential            |
| `score_main`        | Sonnet    | extracted_fact + pointe_result | story_score_result (alle Dimensionen)|
| `find_correlations` | Haiku+Sonnet | new_fact + graph_context    | correlation_result                  |
| `elaborate`         | Sonnet    | extracted_fact + graph_context | elaboration_result                  |
| `write_fact`        | —         | alle results                   | WikiWrite-Objekte                   |

---

## 10. Offene Fragen (Backlog)

- [ ] **Ollama für `sensitivity: private`:** Welche Scoring-Qualität liefert llama3.2 vs. mistral für PersonalFacts? Kalibrierungs-Test nötig.
- [x] **Bootstrap-Timing:** Aufgeteilt auf mehrere Tage — 3-4 Fragen pro Tag. Antwortqualität steigt wenn Nutzer Zeit hat nachzudenken. ConversationHandler merkt sich fortschritt in user_profile.md (`bootstrap_progress: 4/10`).
- [ ] **Impuls-Frequenz:** 1x täglich könnte zu viel sein für manche Tage. Kill-Switch "Impuls pausieren" via Telegram-Befehl einbauen?
- [ ] **Story-Lab Gamification:** story_score-Entwicklung über Zeit als Motivations-Signal sichtbar machen? (z.B. "Dein Durchschnitt ist in 30 Tagen von 5.8 → 7.1 gestiegen")
- [ ] **Impuls-GIFs:** Telegram-GIF-API (getAnimations) oder eigene kuratierte Liste? Kuratiert vermeidet unangemessene Treffer.
- [ ] **Codemix-Bewertung:** Wie genau prüfen ob Spanisch-Wörter *natürlich* eingebettet sind, nicht nur mechanisch eingefügt?
- [ ] **Mehrsprachiger Story-Lab:** Wenn Nutzer weitere Sprachen lernt — fact_retell in Französisch etc. Generisch halten oder Sprache hardcoden?
