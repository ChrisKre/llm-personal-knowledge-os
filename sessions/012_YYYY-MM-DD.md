# Session 012 — MVP-1: Echter Text-Ingest via Telegram (wartet auf API-Key)
> Datum: TBD (sobald Anthropic API-Key vorliegt) | Typ: **IMPLEMENTIERUNG** | Vorgänger: Session 011 (Cleanup)
> Konvention: sessions/NNN.md = am Ende von Session N geschrieben, Brief für Session N+1
> **Dateiname beim Start umbenennen:** `012_YYYY-MM-DD.md` mit echtem Datum.

---

## Was Session 011 war

Session 011 war eine **Cleanup-Session**. Die 14 vom PO in S010 identifizierten Inkonsistenzen wurden mechanisch abgearbeitet — Doku und Code in einen sauberen Zustand gebracht, bevor MVP-1 startet.

**Wichtigste Ergebnisse:**
- ARCHITECTURE.md & COMP_DIARY.md: Nummerierung konsistent (§1–§10 in ARCH, §9.x in DIARY).
- Audio-Reste eliminiert: `tonal_score` → `transcript_quality`, `TonalReport` → `TranscriptQualityReport`, "Claude Audio" → "Claude Sonnet (Text-Analyse)" — alle Stellen tragen `# V1: text-only — ENT-024`-Hinweis. Code (`agents/`) war nie betroffen (Symbole existierten nicht).
- SCHEMA.md §3.7 `ServiceDefinition` ergänzt; System-Dateien jetzt §3.8.
- COMP_SERVICES.md Status-Zeile auf `ENTWURF — MVP-2/Phase 3 (QK-3)`.
- SCHEMA.md §9 Ollama-Frage geschlossen.
- **Branch-Entscheidung:** `master` bleibt (ENT-039 final). Alle Doku-Stellen und sessions/008+009 nachgezogen.
- `doc/prompt.md`, `doc/start.md`, `doc/NEXT_SESSION_PROMPT.md` → `hinweise/archiv/` mit Mini-README.
- INKONSISTENZEN.md Übersicht um Status-Spalte erweitert; alle 14 Einträge ✓.

**MVP-Stand unverändert seit S009:** MVP-0 erreicht. MVP-1 blockiert durch fehlenden API-Key (ENT-038).

---

## Voraussetzung — Pflicht vor Start

**Anthropic API-Key liegt vor** (ENT-038). Falls noch nicht beschafft: Session 012 kann nicht starten.

Setup:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."  # oder in .env (gitignored)
```

Schnell-Test, dass der Key funktioniert:
```bash
python -c "import anthropic; print(anthropic.Anthropic().messages.create(model='claude-haiku-4-5-20251001', max_tokens=10, messages=[{'role':'user','content':'ping'}]).content[0].text)"
```

---

## Deine Rolle in dieser Session

Du bist wieder der **Senior Architect / Engineer**. Session 012 ist **Implementierung** mit klarem Zielbild: MVP-1 (echter Text-Ingest via Telegram) zum Laufen bringen. Architektur ist gesetzt — keine neuen Entscheidungen.

**Grundsatz:** Pipeline lebt. Erste echte PersonalFacts landen im Graph, nicht mehr nur Test-Fixtures.

---

## Zuerst lesen (Pflicht)

```
sessions/011_2026-04-20.md           ← Cleanup-Ergebnisse + Stand der Doku
doc/INKONSISTENZEN.md                ← Sollte vollständig ✓ sein (Verifikation: keine offenen Punkte)
doc/ENTSCHEIDUNGEN.md                ← 39 Entscheidungen — insbesondere ENT-025 (MVP-Stufen), ENT-038 (API-Key)
doc/ARCHITECTURE.md                  ← §3 Supervisor, §6 LangGraph (jetzt sauber nummeriert)
doc/COMP_DIARY.md                    ← §3 story_score, §9 Diary-Agent-Implementierung
hinweise/technischer_hinweis.md      ← §4 State-Merging-Schwäche (Annotated-Reducers)
sessions/009_2026-04-18.md           ← MVP-0 Status, Bug-Fixes P1–P4
```

---

## Session-Log

| # | Datum | Thema | Status |
|---|-------|-------|--------|
| 001–010 | siehe vorige Briefs | Stack, COMPs, Scaffold, MVP-0, PO-Review | ✓ |
| 011 | 2026-04-20 | Doku-Cleanup & Code-Alignment | ✓ |
| 012 | TBD | **MVP-1: Echter Text-Ingest via Telegram** | → |

---

## Fokus dieser Session

**Hauptziel:** Erster echter Telegram-Text wird vom System verarbeitet, ergibt PersonalFact mit gültigem `story_score`, landet im Graphen.

**Definition of Done für MVP-1:**
1. Telegram-Bot läuft, empfängt Nachrichten authentifizierter Nutzer.
2. Eingehender Text durchläuft den Ingestion-Flow: `classify → fetch_graph_context → diary_agent → supervisor_review → write_to_graph → update_index`.
3. Mindestens **3 unterschiedliche** Test-Texte erzeugen 3 valide PersonalFact-Markdown-Seiten in `wiki/personal/facts/`.
4. `index.md` und `log.md` werden korrekt aktualisiert.
5. Test-Lauf von `test_ingest.py` (aus S009) läuft mit echter Claude API (Haiku/Sonnet) statt Ollama-Fallback erfolgreich durch.
6. Kosten pro Ingest dokumentiert (in `hinweise/technischer_hinweis.md` ergänzen).

**Was NICHT in dieser Session:**
- Story-Lab / Voice-Coaching (V1 text-only, aber Story-Lab ist MVP-2).
- Anki-Export.
- Lint-Auto-Fixes über Symptom-Markierung hinaus.
- Services (Phase 3, QK-3).
- Chancen aus `doc/CHANCEN.md`.

---

## Deine Aufgaben

### A — Provider-Switch validieren
- `providers/`-Abstraktion (oder Äquivalent) prüfen: Claude-Pfad aktiv, Ollama-Fallback nur noch für `private`-Tier.
- Smoke-Test mit Haiku (Klassifikation) und Sonnet (story_score) — pro Modell ein Roundtrip.

### B — Telegram-Bot live
- `bot.py` (siehe S005) starten, Webhook oder Polling.
- Authentifizierungs-Filter: nur User-ID des PO antwortet (single-user-system).
- Eingehende Text-Nachrichten erzeugen `RawEvent` in `raw/events/`.

### C — Ingestion-Flow auf echte API
- `main_workflow.py` (siehe S005): Supervisor-Routing testen. State-Merging-Schwäche (`Annotated`-Reducer) wenn nötig fixen — siehe `hinweise/technischer_hinweis.md §4`.
- `extract_fact` (Haiku) + `score_main` (Sonnet) + `score_punchline` (Haiku) müssen mit echter API valide JSON-Outputs liefern.

### D — End-to-End-Test mit drei realen Eingaben
- Drei sehr unterschiedliche Eingaben durch den Bot schicken (z.B. Erlebnis-Anekdote, Vokabel-Frage, Mischtext).
- Ergebnis: `wiki/personal/facts/pf_*.md` (mindestens 1), `index.md` aktualisiert, `log.md` Append.
- Manuelle Spot-Prüfung: macht der story_score Sinn? Stimmt die Klassifikation?

### E — Kostenmessung
- Pro Ingest: Tokens In/Out und USD loggen (Anthropic-Response gibt das zurück).
- Mittelwert + Worst-Case in `hinweise/technischer_hinweis.md` ergänzen.

### F — `test_ingest.py` mit echter API
- Bisheriger Test (S009) lief mit Ollama-Fallback. Jetzt mit `ANTHROPIC_API_KEY` gegen echte API laufen lassen. Erwartete Output-Schema validieren.

---

## Risiken & Stolpersteine

1. **State-Merging:** `wiki_writes`-Liste kann beim parallelen `[language_agent, diary_agent]` (siehe ARCHITECTURE.md §6.1) überschrieben werden, falls keine `Annotated`-Reducer gesetzt sind. Diagnose, bevor das in Production weh tut.
2. **Sonnet-Kosten:** story_score-Prompts können bei langen Inputs teuer werden. Token-Limit pro Anfrage kappen.
3. **Telegram-Updates:** wenn Webhook nicht erreichbar (lokales Setup), polling nutzen (`Application.run_polling()`).
4. **`graph_context` leer:** Bei einem leeren Graphen liefert der `graph_reader` leere Listen — Supervisor-Logik muss damit umgehen können.

---

## Am Ende dieser Session

1. `wiki/personal/facts/` enthält ≥ 3 echte PersonalFact-Markdown-Dateien.
2. `index.md` + `log.md` aktualisiert.
3. `hinweise/technischer_hinweis.md` um Kosten-Sektion ergänzt.
4. `sessions/012_YYYY-MM-DD.md` (diese Datei, mit echtem Datum) — Ergebnis-Notizen ergänzt.
5. `sessions/013_YYYY-MM-DD.md` schreiben (Brief für nächste Session — vermutlich MVP-2-Auftakt: Voice + Anki + Lint-Auto-Fixes).
6. Git-Commit:
```bash
git add -- agents/ wiki/ index.md log.md hinweise/ sessions/
git commit -m "Session 012: MVP-1 erreicht — Telegram-Text-Ingest live mit Claude API"
```

---

## Kontext: Was dieses System ist

LLM-Personal-Knowledge-OS. Persistentes, kompiliertes Wissenssystem für eine Einzelperson. Karpathy-LLM-Wiki-Konzept: kein RAG, kein Vector-Store — kompiliertes Markdown, gepflegt von LLM-Agenten, navigierbar via Obsidian. Telegram als Input-Kanal.

**Tech Stack:**
- Python + Claude API (Haiku 4.5 Bulk, Sonnet 4.6 Synthesis, Ollama llama3.2 für `private`)
- LangGraph — explizite Zustandsmaschinen
- Markdown + Git — Wissensspeicher, Obsidian-kompatibel
- Telegram Bot — primärer Input-Kanal

**MVP-Plan (ENT-025, stabil):**
```
MVP-0 ✓  Pipeline-Mechanik (Ollama, Test-Script)     — erreicht S009
MVP-1 →  Echter Text-Ingest via Telegram              — Ziel S012
MVP-2    Voice + Anki + Lint-Auto-Fixes               — danach
```

**Relevante Kontext-Dokumente:**
- [doc/INKONSISTENZEN.md](../doc/INKONSISTENZEN.md) — sollte vollständig ✓ sein nach S011
- [doc/ENTSCHEIDUNGEN.md](../doc/ENTSCHEIDUNGEN.md) — 39 Entscheidungen indiziert
- [doc/SESSION_ZUSAMMENFASSUNG.md](../doc/SESSION_ZUSAMMENFASSUNG.md) — Projekt-Historie
- [doc/CHANCEN.md](../doc/CHANCEN.md) — Potential-Radar (nicht Scope)
- [hinweise/technischer_hinweis.md](../hinweise/technischer_hinweis.md) — technischer Zustand & Schulden
- [sessions/011_2026-04-20.md](011_2026-04-20.md) — Cleanup-Session inklusive Ergebnis-Notizen

**Letzter Engineering-Brief mit Code-Fokus:** [sessions/009_2026-04-18.md](009_2026-04-18.md)
