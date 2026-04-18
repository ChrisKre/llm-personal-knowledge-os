# QUALITY_CONTROL_008.md — Architektur-Review
> Session: 008 | Datum: 2026-04-18 | Reviewer-Persona: Externer Senior Architect
> Kein Code geschrieben. Entscheidungen zu allen 7 QK-Punkten. Neue Prioritätenliste.

---

## Vorbemerkung

Alle sechs Dokumentationsdateien wurden frisch gelesen ohne Vorkenntnisse aus vorherigen Sessions. Das Review kommt von außen — das ist der Auftrag. Dieser Text ist kein Lob, kein Tadel, sondern ein ehrliches Urteil mit klaren Entscheidungen.

---

## ⚠️ Kritischer Bug — vor allen anderen Entscheidungen

**Gefunden beim Lesen von COMP_DIARY.md §6.5.**

```python
# COMP_DIARY.md §6.5 — analyze_tonal()
response = claude_client.messages.create(
    model="claude-sonnet-4-6",
    messages=[{
        "role": "user",
        "content": [
            {"type": "document", "source": {"type": "base64",
             "media_type": "audio/ogg", "data": audio_data}},
            ...
        ]
    }]
)
```

**Das Claude API unterstützt keine Audio-Dateien.** Das `document`-Typ ist für PDFs. `audio/ogg`, `audio/mp3` usw. sind keine unterstützten Medientypen in der Anthropic Messages API. Dieser Code wird zur Laufzeit mit einem `BadRequestError` fehlschlagen.

**Betroffene Features:**
- Story-Lab Ton-Analyse (Enthusiasmus, Natürlichkeit, Überzeugung)
- Impuls-Antwort Ton-Analyse
- Service-Audio-Analyse

**Was tatsächlich funktioniert (via Whisper):**
- `avg_words_per_second` ✓
- `avg_pause_before_punchline` ✓
- `energy_curve` ✓
- `total_duration` ✓

Diese Entdeckung bestimmt direkt QK-2 und QK-5.

---

## QK-1: Ist der Gesamt-Ansatz richtig?

**Entscheidung: JA — Ansatz ist richtig. Aber er muss bewiesen werden, bevor er weitergebaut wird.**

Das Karpathy-Konzept (kompiliertes Wissen statt RAG) ist für diesen Anwendungsfall technisch überlegen, weil:
1. PersonalFacts mit `story_score`, `social_context`, `practice_log` sind nicht retrieval-bar — sie sind Struktur die ein LLM beim Ingest baut, nicht einfache Textstücke
2. Der positive Feedback-Loop (reicher Graph → besserer graph_context → bessere Scores) ist architektonisch sauber begründet
3. Die Obsidian-Kompatibilität gibt dem Nutzer direkte Kontrolle über seine Daten

**Aber: Die Einstiegshürde ist real und ungelöst.** API-Key fehlt. Kein Test. Das einzige was zählt ist der erste echte End-to-End-Ingest. Alles andere ist Spekulation, egal wie elegant die Architektur.

**Entscheidung für QK-1:**
- Kein weiterer Architektur-Ausbau bis der erste Ingest-Test läuft
- Die Frage "Break-Even Aufwand vs. Mehrwert" beantwortet sich nach 30 echten Eingaben — nicht vorher
- Einfachere Wege zum gleichen Ziel (Notion AI, Obsidian Copilot) fehlt das Kernmerkmal: personalisierter story_score, practice_log, graph_context. Das ist kein RAG-Feature.

---

## QK-2: StyleProfile — zu vage oder tragfähig?

**Entscheidung: StyleProfile reduzieren. Tonal-Analyse-Layer aus V1 streichen.**

### Was bleibt (real implementierbar)

| Feature | Basis | Status |
|---|---|---|
| `avg_words_per_second` | Whisper-Timestamps | ✓ implementierbar |
| `avg_pause_before_punchline` | Whisper-Timestamps | ✓ implementierbar |
| `setup_ratio` | Sonnet-Analyse des TRANSKRIPT-TEXTS | ✓ implementierbar |
| `avg_sentence_length` | Sonnet oder Python-Regex | ✓ implementierbar |
| `key_patterns` | Sonnet-Analyse des TRANSKRIPT-TEXTS | ✓ implementierbar |
| `style_tags` | Sonnet-Analyse des TRANSKRIPT-TEXTS | ✓ implementierbar |

### Was fliegt raus (Claude verarbeitet kein Audio)

| Feature | Problem | Ersatz |
|---|---|---|
| `enthusiasmus` (1-5) | Kein Audio-Input möglich | Aus Transkript-Text schätzen (schwächer) |
| `natuerlichkeit` (1-5) | Kein Audio-Input möglich | Aus Transkript-Text schätzen (schwächer) |
| `ueberzeugung` (1-5) | Kein Audio-Input möglich | Aus Transkript-Text schätzen (schwächer) |
| `pause_vor_pointe` qualitativ | Kein Audio-Input möglich | Durch Whisper-Timing ersetzt (quantitativ) |

### Konsequenz für Story-Lab-Feedback

Das Feedback wird messbar ärmer — aber nicht wertlos. Whisper liefert präzises Timing. Sonnet kann aus dem Transkript-Text Natürlichkeit und Strukturqualität einschätzen (schwächer als Audio, aber nutzbar). Die Feedback-Qualität sinkt von "Coach" zu "Statistiker mit Kontext" — akzeptabel für V1.

**StyleFingerprint-Überarbeitung nötig:** `COMP_DIARY.md §8.3` muss `analyze_tonal()` durch eine `analyze_transcript_quality()`-Funktion ersetzen die nur den Whisper-Text auswertet.

**StyleProfile V1 ist tragfähig** mit dieser Reduktion. Die Konfidenz-Schwellwerte (1/3/5/8 Samples) bleiben sinnvoll.

---

## QK-3: GE-001 Gedankenexperiment — Ergebnis

**Entscheidung: Branch mergen als Dokumentation. Implementation erst in Phase 3.**

### Begründung

Die Spec ist gut. Das Problem ist der Zeitpunkt. Services bauen auf:
1. Funktionierender Core-Pipeline (noch nicht getestet)
2. Bootstrap abgeschlossen (`bootstrap_complete: true`)
3. Mindestens 30-50 Seiten im Graph (für `graph_prerequisites`)
4. StyleProfile funktioniert (QK-2 erfordert Umbau)
5. `ServiceConversationHandler` in `bot.py` existiert

Keiner dieser fünf Punkte ist heute erfüllt.

### Frühestmöglicher sinnvoller Zeitpunkt für Services

**Phase 3 Trigger:** Core-Pipeline läuft stabil (≥30 Tage), Bootstrap abgeschlossen, LanguageAgent und DiaryAgent getestet, erster echter Anki-Export durchgelaufen.

**Konservative Schätzung:** Services frühestens nach Phase 2 (Core + Telegram + Anki).

### Branch-Entscheidung

**Mergen** — aus zwei Gründen:
1. COMP_SERVICES.md ist wertvolle Dokumentation die nicht im Experimentier-Branch begraben bleiben sollte
2. Der Branch enthält keine Implementierung — er kann nicht brechen

**Nach dem Merge:** Status von COMP_SERVICES.md zu `ENTWURF — PHASE 3` aktualisieren. GE-001 ist abgeschlossen als Konzept-Arbeit.

---

## QK-4: SQLite Phase 2 — Wann und wie?

**Entscheidung: Threshold von 150 auf 30 Seiten senken. Phase 1 durch Frontmatter-Matching verbessern.**

### Problem mit Phase 1 wie spec'd

`_search_index_md()` macht freies Keyword-Matching auf der gesamten index.md. Das ist schwach weil:
- Keyword-Match auf dem Eintragstitel liefert false positives ("Flamenco-Kurs" matcht jeden Entry mit "Kurs")
- Keine Gewichtung nach Relevanz
- Tags in index.md werden nicht genutzt

### Phase 1 Verbesserung (ohne SQLite)

Jeder index.md-Eintrag hat bereits: `[[slug]] — beschreibung, tags: [x,y,z]`. Statt reinem Keyword-Matching: **Tag-Overlap-Scoring**.

```python
def _search_index_md_v2(query: str, type: str | None, limit: int) -> list[WikiPage]:
    # 1. Keywords aus query extrahieren (Haiku)
    # 2. Für jede index.md-Zeile: Tag-Overlap-Score berechnen
    #    score = len(keywords ∩ entry_tags) / len(keywords)
    # 3. Top-N nach Score laden
```

Das nutzt die bereits vorhandenen Tags in index.md und ist signifikant besser als naive String-Suche. Kein Extra-Tool nötig.

**SQLite-Threshold:** 30 Seiten (nicht 150). Bei 30 Seiten sind Tag-Overlaps bereits dicht genug dass FTS5 messbaren Mehrwert bringt. Der automatische Switch bleibt — nur früher.

---

## QK-5: MVP — Was ist das Minimum?

**Entscheidung: Dreistufiger MVP-Plan.**

### MVP-0 (API-Key-Test, sofort nach Key-Erhalt)

Kein Telegram. Kein Bot. Nur:
```bash
python scripts/test_ingest.py "war heute beim Flamenco-Kurs, Lehrer sagte duende"
```

Prüft: Extrahiert der DiaryAgent einen korrekten PersonalFact? Berechnet er story_score? Schreibt graph_writer die Datei?

**Dauer bis MVP-0 fertig:** 1-2 Stunden nach API-Key-Erhalt (DiaryAgent-Stubs sind bereits implementiert).

### MVP-1 (Core-Proof, ~1 Woche nach MVP-0)

- DiaryAgent (vollständig, inklusive Verbesserter Phase-1-Suche)
- LanguageAgent (vollständig)
- `"both"` Intent-Bug behoben (LangGraph Send())
- Einfacher Telegram-Bot: nur Text-Input, kein ConversationHandler, kein Voice
- Draft→Main Workflow **NICHT** — direkt auf main schreiben
- LintAgent **NICHT**
- StyleProfile **NICHT**
- Anki **NICHT**

**Ziel MVP-1:** 10-15 echte Einträge, graph_context beginnt nützlich zu werden.

### MVP-2 (Produktion-Fähig, ~4 Wochen nach MVP-1)

- Voice-Input (Whisper)
- LintAgent (Scanner fertig, auto_fixes implementiert)
- AnkiConnect-Integration
- Draft→Main Workflow aktivieren
- Story-Lab ConversationHandler (ohne Ton-Analyse, nur Timing-Feedback)

**Was NIE in V1 kommt:**
- StyleProfile Tonal-Analyse (API-Problem, QK-2)
- Services (Phase 3, QK-3)
- Ollama (separate Abklärung, kein Blocker für MVP)

---

## QK-6: Technische Schulden — Prioritäten

**Entscheidung: Priorisierungsreihenfolge festgelegt.**

| # | Bug | Priorität | Wann | Begründung |
|---|---|---|---|---|
| 1 | `"both"` Intent → LangGraph Send() | **KRITISCH** | vor MVP-1 | ~30% der echten Inputs (persönliche Erlebnisse mit Vokabel-Moment). Duende geht verloren. |
| 2 | graph_reader Phase 1 → Tag-Overlap-Scoring | **HOCH** | vor MVP-1 | Jeder Ingest ist betroffen. Schwaches Matching = schlechter graph_context = schlechte story_scores |
| 3 | `CulturalEntry` country-Code hardcoded | **MITTEL** | MVP-1 | Einfach zu fixen. Alle CulturalEntries landen sonst in `c_es_*.md` egal was |
| 4 | `_apply_auto_fixes()` stubs | **MITTEL** | MVP-2 | LintAgent kann nix reparieren. Nicht nötig bevor Graph Seiten hat |
| 5 | `_update_index()` Race Condition | **NIEDRIG** | Phase 2 | Single-User-System, simultane Writes sind unwahrscheinlich |
| 6 | StyleProfile tonal → Transkript-Analyse | **HOCH** | MVP-2 | Muss vor Story-Lab fertig sein |

---

## QK-7: Cost & Sustainability

**Entscheidung: Kostenmodell ist nachhaltig. Haiku-only ist nicht ausreichend. Sonnet bleibt für Scoring.**

### Bewertung

| Szenario | Kosten/Monat | Verdict |
|---|---|---|
| 50 Ingests, nur Haiku | ~$0.10 | Zu billig um gut zu sein |
| 50 Ingests, Haiku+Sonnet wie geplant | ~$1.50 | ✓ Nachhaltig |
| + Story-Lab 10x/Monat (Whisper+Transkript, kein Audio) | ~$0.50 extra | ✓ Nachhaltig |
| + Ollama für private Tier | $0 extra | ✓ |
| **Gesamt realistisch** | **~$2–4/Monat** | ✓ |

### Haiku-only-Option

**Nein.** Haiku reicht für Klassifikation, Kandidaten-Filterung, Anki-Export. story_score-Qualität (die Kernmetrik) erfordert nuanciertes Reasoning das Haiku nicht liefert. Kalibrierungs-Tests werden zeigen wie groß der Delta ist — aber als Default bleibt Sonnet für Scoring.

**Größter Kostentreiber:** Sonnet-Calls für Elaboration + story_score. Bei 50 Ingests/Monat und ~40% die Elaboration triggern (~20 Sonnet-Calls à $0.03) = ~$0.60. Kontrollierbar durch `story_score_elaborate_threshold`.

### Ollama-Entscheidung

**llama3.2 für `sensitivity: private`.** Begründung: Mistral hat höhere Halluzinationsrate bei strukturiertem Output (YAML-Frontmatter). llama3.2 ist besser auf Instruction-Following optimiert — relevant für Agents die Templates befüllen. Qualitäts-Test bleibt offen, aber llama3.2 ist der Default-Kandidat.

---

## Neue Prioritätenliste (nach API-Key)

```
SOFORT (Tag 1 nach API-Key):
  1. MVP-0 Test-Script: test_ingest.py mit einem echten Text-Input
  2. Bug fix: "both" Intent → LangGraph Send() parallel routing
  3. graph_reader Phase 1 → Tag-Overlap-Scoring
  4. CulturalEntry country-Code: Sprach-Erkennung statt hardcoded "es"

WOCHE 1:
  5. MVP-1: Telegram Text-Input aktivieren
  6. 10-15 echte Bootstrap-Eingaben machen
  7. graph_context Qualität beobachten: werden relevante Seiten gefunden?

WOCHE 2-4:
  8. Voice-Input (Whisper) aktivieren
  9. LintAgent _apply_auto_fixes() implementieren
  10. AnkiConnect-Integration testen
  11. Story-Lab ConversationHandler (Whisper-Timing-Only, kein Ton)

PHASE 2 (nach 30 stabilen Tagen):
  12. StyleProfile: analyze_tonal() → analyze_transcript_quality() umschreiben
  13. Draft→Main Workflow aktivieren
  14. SQLite FTS5 sobald Graph ≥30 Seiten

PHASE 3 (nach bootstrap_complete):
  15. Services: COMP_SERVICES.md Branch mergen + implementieren
```

---

## Bereinigung der offenen Entscheidungen

### Entschieden (neu, Session 008)

- [x] **StyleProfile Tonal-Analyse** — GESTRICHEN für V1. Claude unterstützt kein Audio-Input. Ersatz: Transkript-Text-Analyse via Sonnet (timing bleibt via Whisper)
- [x] **`"both"` Routing** — LangGraph Send() muss vor MVP-1 implementiert sein. Blocker.
- [x] **GE-001 Branch** — MERGEN als Dokumentation. Services frühestens Phase 3.
- [x] **MVP-Scope** — Definiert: dreistufig (MVP-0 / MVP-1 / MVP-2), Details oben
- [x] **Phase-1 Graph-Context Verbesserung** — Tag-Overlap-Scoring, SQLite-Threshold auf 30 Seiten
- [x] **Ollama-Modell** — llama3.2 als Default für `sensitivity: private`
- [x] **Haiku-only Option** — NEIN für story_score. Haiku nur für Klassifikation/Bulk.

### Gestrichen (kein Wert für V1)

- [ ] ~~**Impuls-GIFs** — Telegram-GIF-API vs. kuratierte Liste~~ → Impuls erst in MVP-2. Nicht jetzt entscheiden.
- [ ] ~~**Story-Lab Gamification** — score-Entwicklung sichtbar machen~~ → Phase 2, nach echten Daten
- [ ] ~~**Mehrsprachiger Story-Lab**~~ → Phase 2. Erst wenn eine Sprache getestet ist.

### Weiterhin offen (aber nicht blockierend für MVP-0/1)

- [ ] **Bootstrap-Timeout** — Reset oder weiterführen bei längerer Pause
- [ ] **Codemix-Bewertung** — natürlich vs. mechanisch eingebettete Wörter
- [ ] **Bootstrap-Vokabeln** — erste 20 Spanisch-Vokabeln als Seed
- [ ] **Widerspruchs-Filter** — Haiku-Kandidaten-Schwellwert
- [ ] **Anki-Deck-Struktur** — Unterdeck "Phrasen" sinnvoll?
- [ ] **SCHEMA.md §3** — ServiceDefinition eintragen (nach Branch-Merge)

---

## Zusammenfassung

Drei Kernaussagen:

**1. Der Ansatz ist solide — aber er muss getestet werden, nicht weitergebaut.**
Nach sechs Design-Sessions ist das System gut durchdacht. Der nächste Schritt ist kein Design — es ist der erste echte Ingest-Test. API-Key beschaffen, MVP-0 laufen lassen, dann weitersehen.

**2. Ein kritischer Bug wurde gefunden: Claude verarbeitet kein Audio.**
Die gesamte Tonal-Analyse (Enthusiasmus, Natürlichkeit, Überzeugung via OGG-Datei) ist nicht implementierbar wie spec'd. StyleProfile bleibt wertvoll — aber auf Timing-Metriken + Transkript-Text-Analyse reduziert. Das muss vor Story-Lab-Implementation korrigiert werden.

**3. Der MVP ist viel kleiner als das aktuelle System.**
DiaryAgent + LanguageAgent + Text-Input über Telegram ist MVP-1. Alles andere (LintAgent, Story-Lab, Anki, Voice, Services) ist Phase 2 oder später. Der Wert des Systems entsteht durch echte Nutzung, nicht durch weitere Features.
