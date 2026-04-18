# INKONSISTENZEN.md — Dokumentations-Health-Check
> Erstellt: Session 010 (2026-04-19) | Autor: Product Owner
> Ergebnis eines Scans aller Dateien in `doc/` nach Nummerierungsfehlern, veralteten Aussagen und Widersprüchen zu nachträglich getroffenen Entscheidungen.

---

## Übersicht

| ID | Datei | Schwere | Empfehlung |
|---|---|---|---|
| INK-001 | ARCHITECTURE.md | hoch | korrigieren |
| INK-002 | ARCHITECTURE.md | mittel | korrigieren |
| INK-003 | COMP_DIARY.md | hoch | korrigieren |
| INK-004 | COMP_DIARY.md | hoch | korrigieren |
| INK-005 | COMP_DIARY.md | hoch | korrigieren |
| INK-006 | COMP_DIARY.md | mittel | korrigieren |
| INK-007 | COMP_SERVICES.md | hoch | korrigieren |
| INK-008 | COMP_SERVICES.md | niedrig | korrigieren |
| INK-009 | SCHEMA.md | mittel | ergänzen |
| INK-010 | SCHEMA.md | niedrig | schließen |
| INK-011 | doc/prompt.md | hoch | archivieren |
| INK-012 | doc/start.md | hoch | archivieren |
| INK-013 | doc/NEXT_SESSION_PROMPT.md | hoch | archivieren |
| INK-014 | sessions/* | mittel | korrigieren |

---

## [INK-001] ARCHITECTURE.md — Doppelte §6 (Nummerierungskonflikt)

- **Was steht da:**
  - Zeile 390: `## 6. LangGraph Implementierung`
  - Zeile 474: `## 6. Nutzer-Interaktion: Telegram UI-Ebenen`
  - Zwei eigenständige Hauptabschnitte tragen beide die Nummer **6**.
- **Was stimmt nicht:** In Session 009 wurde §5 "Provider-Strategie" neu eingefügt. Dabei wurde die folgende Abschnittsnummerierung nur teilweise durchgereicht. §7 existiert nicht, §8 und §9 sind aber vorhanden — d.h. die Nummerierung springt von zweimal §6 direkt auf §7 "Graph-Versionierung" (Zeile 538), §8 "Trigger & Scheduling" (Zeile 613), §9 "Offene Architektur-Fragen" (Zeile 626).
- **Empfehlung:** korrigieren. Umbenennen: §6 LangGraph → bleibt §6, §6 Nutzer-Interaktion → **§7**, §7 Graph-Versionierung → **§8**, §8 Trigger & Scheduling → **§9**, §9 Offene Fragen → **§10**.

## [INK-002] ARCHITECTURE.md — Falsche Sub-Nummerierung in §6 LangGraph

- **Was steht da:** In §6 "LangGraph Implementierung" (ab Zeile 390) tragen die Unterabschnitte die Nummern `### 5.1 Graph-Struktur`, `### 5.2 Datei-Schreib-Vertrag`, `### 5.3 Graph Reader — Index-Abstraktion` (Zeilen 392, 430, 443).
- **Was stimmt nicht:** Die Sub-Nummerierung stammt noch aus der Zeit, als LangGraph §5 war. Muss auf §6 angepasst werden.
- **Empfehlung:** korrigieren → `### 6.1`, `### 6.2`, `### 6.3`.

## [INK-003] COMP_DIARY.md — Falsche Sub-Nummerierung in §9

- **Was steht da:** In §9 "Diary-Agent-Implementierung" (Zeile 1213) heißen die Sub-Abschnitte `### 8.1 State-Erweiterung`, `### 8.2 LangGraph-Nodes`, `### 8.3 Node-Übersicht` (Zeilen 1215, 1238, 1267).
- **Was stimmt nicht:** §8 ist bereits "Style References" (Zeile 993) mit §8.1–§8.7. Die §9-Unterabschnitte müssen auf §9.x umgeschrieben werden.
- **Empfehlung:** korrigieren → `### 9.1`, `### 9.2`, `### 9.3`.

## [INK-004] COMP_DIARY.md — Überbleibsel der `tonal_score`-Felder

- **Was steht da:** §1.2 "practice_log" (Zeile 88): `tonal_score: {enthusiasmus: 4, natuerlichkeit: 3, ueberzeugung: 4}`. §6.5 (Zeile 726): Funktionssignatur enthält `tonal: TonalReport`.
- **Was stimmt nicht:** Entscheidung QK-1 (Session 008): Claude API unterstützt kein Audio — Tonalitätswerte sind **nicht implementierbar** in V1. Die Datenstruktur muss widerspiegeln, was V1 tatsächlich liefert: `TranscriptQualityReport` (textbasiert). In §6.5 ist bereits ein Hinweiskasten vorhanden, aber die Code-Signatur wurde nicht angepasst.
- **Empfehlung:** korrigieren. `tonal_score` in §1.2 löschen oder als `transcript_quality: {pausen, wortwahl, bogen}` ersetzen. Signatur `tonal: TonalReport` → `transcript_quality: TranscriptQualityReport` ändern.

## [INK-005] COMP_DIARY.md — "Claude Audio" in Prozessbeschreibungen

- **Was steht da:**
  - Zeile 517: `Fact + Stil-Karte → Nutzer nimmt auf → Whisper + Claude Audio → Feedback → (nächster Versuch?)`
  - Zeile 613: `[Whisper + Claude Audio läuft intern]`
- **Was stimmt nicht:** "Claude Audio" existiert in der verwendeten API nicht. Die V1-Pipeline ist: Whisper-Transkript → Text-Analyse mit Sonnet (kein Audio-Input).
- **Empfehlung:** korrigieren. "Claude Audio" → "Whisper + Claude Sonnet (Text-Analyse)".

## [INK-006] COMP_DIARY.md — §6.1 "Voice-First Coaching" widerspricht V1-Scope

- **Was steht da:** §6.1 Überschrift "Voice-First Coaching" (Zeile 512).
- **Was stimmt nicht:** V1 liefert keinen Voice-First-Coaching, sondern Text-basiertes Coaching mit Whisper-Transkript. Der Titel weckt falsche Erwartungen.
- **Empfehlung:** korrigieren. "Voice-First Coaching" → "Story-Lab Coaching (V1: text-basiert)". Den darunter bestehenden Hinweiskasten aus §6.5 zusätzlich am Anfang von §6.1 platzieren.

## [INK-007] COMP_SERVICES.md — Verweis auf "Whisper + Claude Sonnet Audio"

- **Was steht da:** Zeile 320: `Identisch zur Story-Lab Voice-Analyse (COMP_DIARY §6.5): Whisper + Claude Sonnet Audio.`
- **Was stimmt nicht:** Gleicher Widerspruch wie INK-005. Es gibt kein "Claude Sonnet Audio".
- **Empfehlung:** korrigieren → "Whisper-Transkript + Claude Sonnet Text-Analyse".

## [INK-008] COMP_SERVICES.md — Status-Zeile veraltet

- **Was steht da:** Zeile 2: `> Version: 0.1 | Datum: 2026-04-18 | Status: ENTWURF (GE-001)`
- **Was stimmt nicht:** Entscheidung QK-3 (Session 008) verschob COMP_SERVICES auf **Phase 3** (nach MVP-1). Der Status sollte das widerspiegeln.
- **Empfehlung:** korrigieren → `Status: ENTWURF — MVP-2/Phase 3 (nach Session 008 QK-3)`.

## [INK-009] SCHEMA.md — Fehlende ServiceDefinition-Entität in §3

- **Was steht da:** §3 "Entitäts-Ontologie" (Zeile 52) listet PersonalFact, VocabEntry, CulturalEntry, LanguageBridge, Concept, StyleProfile. Keine `ServiceDefinition`.
- **Was stimmt nicht:** COMP_SERVICES.md (GE-001) führt `ServiceDefinition` als eigenständige Entität mit Schema und Workflow ein. Das muss auch im zentralen Schema verankert sein.
- **Empfehlung:** ergänzen. Neuer Unterabschnitt §3.7 (oder an passender Stelle) "ServiceDefinition" mit Kurzfassung + Link auf COMP_SERVICES.md.

## [INK-010] SCHEMA.md — Offene Frage zu Ollama-Modell veraltet

- **Was steht da:** §9 Zeile 344: `[ ] Ollama-Setup definieren: welches lokale Modell für private-Tier? (llama3.2 vs. mistral)`
- **Was stimmt nicht:** Entscheidung QK-5 (Session 008) legt **`llama3.2`** als Standard fest (mit Fallback-Optionen). Die Checkbox sollte entsprechend abgehakt bzw. der Text aktualisiert werden.
- **Empfehlung:** schließen. `[x] Ollama-Setup: llama3.2 (Default, QK-5 S008)` + Verweis auf ENTSCHEIDUNGEN.md.

## [INK-011] doc/prompt.md — Überbleibsel

- **Was steht da:** Ursprünglicher "Senior Systems Architect"-Rollenprompt aus Projektbeginn (prä-Session 001).
- **Was stimmt nicht:** Wird nirgends mehr referenziert. Kein Session-Brief verweist darauf. Gehört nicht in `doc/` (Projekt-Dokumentation), sondern in `hinweise/` (Kontext-Archiv) oder `archiv/`.
- **Empfehlung:** archivieren → verschieben nach `hinweise/archiv/initial_prompt.md`.

## [INK-012] doc/start.md — Überbleibsel

- **Was steht da:** Rohe Nutzer-Notizen aus der Konzept-Phase vor Session 001.
- **Was stimmt nicht:** Historisches Quellmaterial, kein Teil der lebenden Doku. Inhalte sind in ARCHITECTURE.md, SCHEMA.md, COMP_*.md kodifiziert.
- **Empfehlung:** archivieren → verschieben nach `hinweise/archiv/start_notes.md`.

## [INK-013] doc/NEXT_SESSION_PROMPT.md — Überbleibsel

- **Was steht da:** Session-Übergabe-Brief für Session 002 ("COMP_DIARY.md schreiben").
- **Was stimmt nicht:** Aufgabe lange erledigt (Session 002). Das Session-Handover-Muster ist seit Session 003 durch `sessions/NNN_YYYY-MM-DD.md` ersetzt — dieser Platzhalter ist obsolet.
- **Empfehlung:** archivieren → verschieben nach `hinweise/archiv/next_session_prompt_002.md` oder löschen.

## [INK-014] Sessions — Verweise auf Branch "main" trotz echtem Branch `master`

- **Was steht da:** Sessions 008 und 009 sprechen mehrfach von "Branch main" / "Merge in main".
- **Was stimmt nicht:** Der echte Default-Branch heißt `master`.
- **Empfehlung:** korrigieren. In zukünftigen Session-Briefs durchgehend `master` nennen; alternativ Branch **umbenennen** zu `main` (`git branch -m master main` + Remote-Update) — Empfehlung des PO: **umbenennen zu `main`**, da neues Projekt und `main` heute Konvention ist. Entscheidung offen — siehe ENTSCHEIDUNGEN.md ENT-039 (offen).

---

## Nicht betroffen (geprüft, in Ordnung)

- `COMP_LANGUAGE.md` v0.1 — konsistent, keine Nummerierungsfehler
- `KNOWLEDGE_GRAPH.md` v0.2 — konsistent
- `QUALITY_CONTROL_008.md` — Schnappschuss, bleibt unverändert
- `index.md`, `log.md` — Teil des Live-Graphen, nicht Teil von `doc/`
