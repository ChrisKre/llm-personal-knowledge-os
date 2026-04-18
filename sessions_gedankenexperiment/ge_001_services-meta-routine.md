# Gedankenexperiment GE-001 — Services Meta-Routine
> Art: Gedankenexperiment | Branch: `experiment/ge-001-services-meta-routine`
> Erstellt: 2026-04-18 | Keine Implementierung erwartet — reines Architekturdenken

---

## Was ist ein Gedankenexperiment in diesem System?

Diese Session hat einen anderen Modus als normale Sessions:

- **Kein Code schreiben.** Keine WikiWrites. Keine Stubs.
- **Ziel:** Architektur durchdenken, Machbarkeit einschätzen, offene Fragen aufdecken.
- **Output:** Ein strukturiertes Architektur-Dokument (`doc/COMP_SERVICES.md` als Entwurf) das als Entscheidungsgrundlage für spätere Implementierungs-Sessions dient.
- **Läuft auf:** Branch `experiment/ge-001-services-meta-routine` — kein Einfluss auf `master`.

---

## Pflichtlektüre vor Beginn

```
doc/SCHEMA.md §3.6          → StyleProfile-Entität (das Zielobjekt dieses Experiments)
doc/ARCHITECTURE.md §4      → Agenten-Architektur (Kommunikations-Prinzip, LangGraph)
doc/COMP_DIARY.md §8        → StyleProfile vollständig (Fingerprint, Aggregation, Aktiv-Setzen)
doc/COMP_LANGUAGE.md §7     → Schnittstellen-Modell (wie zwei Module verbunden werden)
```

Die anderen Docs (`KNOWLEDGE_GRAPH.md`, `COMP_DIARY.md §1-7`) sind Kontext — lies sie wenn Fragen entstehen.

---

## Systemkontext (Kurzfassung)

**Was ist dieses System?**
LLM-Personal-Knowledge-OS: ein persistentes, kompiliertes persönliches Wissens- und Persönlichkeitssystem. Kein RAG — vernetzte Markdown-Seiten, gepflegt von LLM-Agenten, navigierbar über Obsidian. Basiert auf Karpathys LLM-Wiki-Konzept.

**Stack (final):**
- Python + Claude API: Haiku 4.5 (Bulk), Sonnet 4.6 (Synthesis), Ollama (private)
- LangGraph — explizite Zustandsmaschinen
- Markdown + Git — Wissensspeicher
- Telegram Bot — primärer Input-Kanal
- AnkiConnect REST — Vokabel-Export

**Nutzer-Profil:**
- Deutsch (Muttersprache), lernt Spanisch
- Interessen: KI/Tech, Gesundheit, Musik, Fotografie, Esport (CS2), Krypto
- Programmiererfahrung vorhanden

**Aktuell implementierter Scaffold (`agents/`):**
```
base_agent.py           FERTIG — Basisklasse
supervisor.py           FERTIG — classify/route/review
graph_reader.py         VOLLIMPL — Phase 1 (index.md), Phase 2 Stub
graph_writer.py         FERTIG — WikiWrite-Execution, Draft→Main
diary_agent.py          STUB — LangGraph-Struktur vorhanden, Nodes NotImplementedError
language_agent.py       STUB — LangGraph-Struktur vorhanden, Nodes NotImplementedError
lint_agent.py           STUB — Datentypen vorhanden, run_lint NotImplementedError
extractors/             VOLLIMPL — alle 5 Format-Handler implementiert
```

**Noch nicht angelegt:** `requirements.txt`, `main_workflow.py`, `bot.py` (Telegram-Grundgerüst).

---

## Das StyleProfile — Kontext für dieses Experiment

StyleProfile ist das Ziel-Objekt dieses Gedankenexperiments. Kurze Wiederholung:

```
StyleProfile = aggregierter Stil-Benchmark aus Medien-Clips
  → entsteht aus StyleFingerprints (Timing + Struktur pro Clip)
  → Felder: avg_words_per_second, avg_pause_before_punchline, setup_ratio,
             key_patterns (≥50% der Clips), style_tags, confidence (0.0–1.0)
  → wird genutzt für: Story-Lab-Feedback, Impuls-Feedback (Vergleich mit Nutzer-Performance)
  → confidence-Schwellwerte: 1 Sample→0.25, 3→0.60, 5→0.85, 8→1.00
  → aktiv gesetzt via: /stil [name] in Telegram → in user_profile.md gespeichert
```

**Das Problem mit dem aktuellen Modell:**
Heute wird StyleProfile nur aus *externen Referenzen* aufgebaut (Chappelle, TED-Talk etc.). Der Nutzer ahmt einen fremden Stil nach. Das ist ein Anfang — aber kein komplettes Bild. Ein StyleProfile das *nur* aus Referenz-Clips besteht kann nicht erkennen:
- Wie der Nutzer *wirklich* spricht (in verschiedenen Kontexten)
- Welche Themen seinen Stil verändern (Krypto-Fachsprache vs. Smalltalk)
- Wie sein Stil sich über Zeit entwickelt

Die Kernhypothese dieses Experiments: **Domänen-spezifische Service-Routinen könnten das StyleProfile von außen anreichern** — durch kontextspezifische Übungssituationen die der aktuellen Diary/Language-Pipeline nicht zugänglich sind.

---

## Das Gedankenexperiment: Services Meta-Routine

### Kernfrage

> Ist es möglich, ein System zu bauen das **eigenständig neue Service-Module** erstellt, deployed und mit dem Knowledge Graph verbindet — basierend auf dem Inhalt der Knowledgebase selbst?

Das zerfällt in zwei Teilfragen:

**Teilfrage A — Machbarkeit der autonomen Implementierung:**
Kann ein Agent (z.B. Claude Code, ein LangGraph-Agent mit Code-Schreib-Fähigkeit) dieses Repo — oder Teile davon — eigenständig implementieren? Was sind die Grenzen?

**Teilfrage B — Services-Architektur:**
Wie muss ein `ServiceRoutine`-Modul aussehen damit:
1. Neue Services aus dem Knowledge-Graph-Inhalt *generiert* werden (Nutzer-Interessen → Service-Ideen)
2. Services das StyleProfile *anreichern* (neue Dimensionen, mehr Kontext)
3. Das System sich über Zeit *selbst erweitert* (neue Services werden deployed ohne Entwickler-Eingriff)

---

## Konkrete Beispiele (Ausgangspunkt — zu analysieren und zu erweitern)

Die folgenden Beispiele sind erste Ideen. **Du sollst sie nicht nur analysieren — du sollst sie auf Architektur-Tauglichkeit prüfen, Lücken aufzeigen und 3-5 weitere vorschlagen die zum Nutzer-Profil passen.**

### Beispiel 1: Crypto-Service
**Graph-Basis:** Wenn der Graph CulturalEntries oder Concepts zu Krypto/Trading enthält:
- **Signal-Routine:** Nutzer kommentiert ein Chart-Muster per Sprachnachricht → wird transkribiert → in PersonalFact überführt ("Ich erkläre Trading-Muster unter Druck gut/schlecht")
- **Pattern-Quiz:** Bot sendet Bild eines Candlestick-Musters → Nutzer erklärt auf Spanisch oder Deutsch → Timing/Ton analysiert → StyleProfile-Eintrag für "Erklär-Stil unter Fachkontext"

*Offene Fragen für dieses Beispiel:*
- Woher kommen die Chart-Bilder? (Externe API, kuratiert, generiert?)
- Ist "Krypto-Sprache" ein eigener style_tag im StyleProfile oder ein separater Dimension?
- Wie wird "Erklärqualität" gemessen — nur Timing oder auch inhaltliche Korrektheit?

### Beispiel 2: Movie-Service
**Graph-Basis:** Wenn der Graph PersonalFacts zu Filmen oder CulturalEntries zu Regisseuren/Filmen enthält:
- **Zitat-Erkennung:** Bot sendet Filmzitat → Nutzer ordnet zu → Bot fragt "Erkläre warum der Charakter das gesagt hat" → Sprachantwort → StyleProfile-Eintrag für "Erklär-Stil bei emotionalem Kontext"
- **Hintergrundgeschichten:** Research-Routine findet Trivia zu Filmen aus dem Graph → präsentiert als Impuls

*Offene Fragen:*
- Brauchen wir eine Research-Routine die externe APIs abfragt (IMDB, Wikipedia)? Wie passt das zur "alles lokal"-Philosophie?
- Wie werden Film-Zitate kuratiert — manuell, generiert, oder via Knowledgebase?

### Beispiel 3: Sprach-Service (Erweiterung des bestehenden Language-Moduls)
**Graph-Basis:** Bestehendes Language-Modul + VocabEntries:
- **Konversations-Simulation:** Nutzer führt simuliertes Gespräch auf Spanisch in einem Kontext aus dem Graph (Flamenco-Kurs, Madrid-Trip) → komplette Sprachanalyse
- **Themen-Debate:** Nutzer debattiert ein Concept aus dem Graph auf der Zielsprache

*Frage: Ist das eine Erweiterung des Language-Agents oder ein eigenständiger Service?*

### [TODO für die LLM] Weitere Beispiele
Analysiere das Nutzer-Profil (KI/Tech, Gesundheit, Musik, Fotografie, Esport/CS2, Krypto, Spanisch) und schlage **3-5 weitere Service-Ideen** vor. Kriterium: sie müssen (a) aus Graph-Inhalt ableitbar sein und (b) das StyleProfile in einer neuen Dimension bereichern die Diary/Language allein nicht abdeckt.

---

## Architekturfragen (bitte strukturiert beantworten)

### F1: Service-Entität

Welche neue Entität(en) braucht das SCHEMA.md? Mindestanforderungen:
- `ServiceDefinition`: Wie beschreibt man einen Service formal? (Trigger, Zutaten aus dem Graph, Output-Typ, StyleProfile-Verbindung)
- `ServiceInstance`: Eine konkrete Ausführung eines Services (RawEvent-ähnlich, aber service-spezifisch)

Vorschlag bitte als Frontmatter-Template — konsistent mit den bestehenden Entitäts-Typen in SCHEMA.md §3.

### F2: Meta-Routine Architektur

Wie funktioniert die "Meta-Routine" die neue Services erfindet?

```
Graph-Inhalt (PersonalFacts, Concepts, CulturalEntries)
    → Meta-Agent analysiert Nutzer-Interessen-Cluster
    → generiert ServiceDefinition-Vorschläge
    → Nutzer bestätigt via Telegram
    → ???
```

Was passiert nach der Bestätigung? Wer *implementiert* den neuen Service?
- Option A: Meta-Agent schreibt Python-Code (Claude Code / Agenten mit Code-Tools)
- Option B: Meta-Agent instanziiert einen vordefinierten Template-Service mit neuen Parametern
- Option C: Meta-Agent erstellt nur die `ServiceDefinition` als Wiki-Seite; Entwickler implementiert

Analysiere alle drei Optionen auf: Machbarkeit heute, Risiken, Wartbarkeit.

### F3: StyleProfile-Verbindung

Wie genau reichert ein Service das StyleProfile an? Drei mögliche Mechanismen:
- **Neuer style_tag:** Service identifiziert Stil-Muster die der bestehende Story-Lab nie sieht (z.B. "Erklär-Stil unter Zeitdruck")
- **Neue Dimension im StyleFingerprint:** Nicht nur Timing + Struktur, sondern z.B. "Fachsprache-Einsatz" oder "emotionale Reaktions-Latenz"
- **Kontextueller Benchmark:** Service zeigt ob StyleProfile stabil ist oder sich je nach Domäne ändert (Krypto vs. Smalltalk → anderer Stil?)

Welcher Mechanismus ist am saubersten in das bestehende Schema integrierbar ohne SCHEMA.md zu zerreißen?

### F4: Teilfrage A — Autonome Implementierung

**Ist es realistisch, dass Claude Code (oder ein ähnlicher Coding-Agent) dieses Repo — oder wesentliche Teile davon — eigenständig implementiert?**

Bitte einschätzen:
1. Was kann heute (2026) ein Coding-Agent (Claude Code, Cursor, Aider) realistisch allein implementieren? Was sind die Grenzen?
2. Welche Teile dieses Repos sind gut geeignet für autonome Implementierung (klare Specs, wenig Abhängigkeiten)?
3. Welche Teile sind schlecht geeignet (emergentes Verhalten, unklar spezifiziert, externe APIs)?
4. Welches Workflow-Modell wäre sinnvoll? (Vollautonomer Agent? Agent + Mensch-Review-Loop? Agent für Stubs, Mensch für Logik?)

### F5: Session-Management für Services

Jeder Service braucht seinen eigenen Konversations-Flow mit dem Nutzer. Heute gibt es:
- `ConversationHandler` für Story-Lab (in python-telegram-bot)
- Einfache Polls/Buttons für Lint-Tasks

Wie skaliert das mit 5, 10, 20 Services? Optionen:
- Option A: Jeder Service hat seinen eigenen `ConversationHandler` (linear wachsende Komplexität)
- Option B: Generischer `ServiceConversationHandler` der eine `ServiceDefinition` als Config erhält
- Option C: Telegram Mini App als generische UI für alle Services

### F6: Wie lernt das System welche Services es braucht?

```
Graph hat 50 PersonalFacts → viele zum Thema "Krypto"
    → Meta-Agent erkennt: Krypto-Cluster ≥ Schwellwert
    → schlägt Crypto-Service vor
```

Was ist der Schwellwert? (N Facts, N Tags, confidence-Level?)
Wie verhindert man, dass das System zu viele irrelevante Services vorschlägt?
Gibt es einen "Service-Lifecycle" (aktiv → inaktiv → archiviert)?

---

## Offene Technische Fragen (bitte adressieren)

1. **Wer deployt neue Services?** Wenn Option A (Agent schreibt Code): wie testet der Agent den Code bevor er deployt? Welche Guardrails?
2. **Wie werden Services dokumentiert?** Soll `doc/COMP_SERVICES.md` ein wachsendes Dokument sein das der Meta-Agent selbst erweitert?
3. **Logging für Services:** Jede Service-Ausführung erzeugt Events. Wie verhält sich das zu `log.md`? Eigene Service-Logs oder alles in `log.md`?
4. **Rückwärtskompatibilität:** Wenn ein Service das StyleProfile-Schema erweitert (neue Felder) — wie upgraden bestehende StyleProfile-Seiten?
5. **Kosten-Kontrolle:** Services könnten täglich viele Haiku/Sonnet-Calls auslösen. Wie Budget-Kontrolle einbauen?

---

## Erwarteter Output dieser Session

Bitte liefere ein strukturiertes Dokument mit:

### 1. Machbarkeits-Einschätzung (F4)
Ehrliche Bewertung: Was ist heute realistisch, was ist Science-Fiction. Keine Übertreibungen in beide Richtungen.

### 2. Vorgeschlagene Architektur (COMP_SERVICES.md Entwurf)
- `ServiceDefinition`-Entität (SCHEMA-konformes Template)
- Meta-Routine-Architektur (welche Option für F2, warum)
- StyleProfile-Verbindungs-Mechanismus (welche Option für F3, warum)
- Session-Management-Ansatz (welche Option für F5, warum)

### 3. Service-Katalog (erste Version)
- Die 3 Beispiele bewertet (Architektur-tauglich? Anpassungen nötig?)
- 3-5 neue Vorschläge mit kurzer Begründung warum sie zum Nutzer-Profil passen

### 4. Kritische Risiken
Was sind die Top-3-Risiken dieses Konzepts die eine Implementierung scheitern lassen könnten?

### 5. Empfehlung: Nächste konkrete Schritte
Was wäre der kleinste sinnvolle erste Schritt der realen Wert liefert ohne das gesamte Meta-Routing-System bauen zu müssen? (Pareto-Prinzip: 20% Aufwand, 80% des Nutzens)

---

## Rahmenbedingungen für das Denken

- **Konsistenz mit bestehendem System:** Alle Vorschläge müssen mit SCHEMA.md, ARCHITECTURE.md und dem WikiWrite-Vertrag kompatibel sein. Keine "wir reißen alles ab"-Vorschläge.
- **Kosten-Bewusstsein:** Das System läuft lokal auf einem Windows-PC. Monatliches LLM-Budget: ~$5-10. Services die täglich viele teure Sonnet-Calls auslösen sind nicht sinnvoll.
- **Nutzer-Friction:** Jeder Service der mehr als 2 Minuten Setup pro Nutzung kostet wird nicht genutzt. Einfachheit zuerst.
- **Keine Halluzinations-Falle:** Wenn du eine Frage nicht beantworten kannst, sag es direkt. "Ich weiß nicht wie X funktioniert" ist besser als eine falsche Antwort die in der Implementierung scheitert.
