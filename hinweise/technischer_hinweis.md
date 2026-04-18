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
| `LintAgent._apply_auto_fixes()` sind Stubs | Lint läuft, repariert aber nichts | MVP-2 |
| AnkiConnect nicht implementiert | Vokabel-Export funktioniert nicht | MVP-2 |
| Kein LLM-Retry bei Timeout/Fehler | Pipeline bricht bei Ollama-Timeout ab | MVP-1 |
| graph_reader Phase 2 (SQLite) ungetestet | Risiko bei > 30 Seiten | MVP-1 |
| bot.py kein Error-Handling | Telegram-Bot crasht bei Fehlern | MVP-1 |
| LangGraph Reducer für parallel routing | Möglicher Datenverlust bei "both"-Intent | MVP-1 |

---

## Was der Engineer vom Product Owner braucht

1. **Entscheidung API-Key** — ohne Key kein MVP-1
2. **Klarheit über MVP-Scope** — was ist "done" für MVP-1? Nur Text-Telegram, kein Voice?
3. **doc/-Struktur** — welche Dateien in doc/ sind noch relevant? (`prompt.md`, `start.md`, `NEXT_SESSION_PROMPT.md` sehen wie Überbleibsel aus)
4. **Branch-Konvention** — sessions/009 sagt "Branch: main" aber es heißt `master`. Einmal festlegen.
