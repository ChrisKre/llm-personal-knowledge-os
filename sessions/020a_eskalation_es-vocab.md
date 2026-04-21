# Mid-Session-020 → Eskalation an Product Owner
> Erstellt: 2026-04-21 (während Session 020) | Architekt → PO | Typ: **Scope-Entscheidung blockiert Voice-Verifikation**

---
# Rolle: [Product Owner](../prompts_team/head_product_owner.md)
---

## Worum es geht (in einem Satz)

Der Trocken-Test des Voice-Ingest hat einen **vorbestehenden Bug im LanguageAgent** sichtbar gemacht, der Voice ohne PO-Entscheidung produktiv nicht freigegeben werden kann: rein-spanische Inputs erzeugen 15+ VocabEntries pro Nachricht — das fragmentiert das Wiki, sprengt das Budget und erzeugt Anki-Spam, sobald Anki-Export aktiv ist.

Ich brauche von dir eine **Policy-Entscheidung**: *Wann soll der Bot überhaupt VocabEntries automatisch erzeugen?* Sobald die getroffen ist, kann ich den Live-Bot-Test der Voice-Pipeline sauber abschließen.

---

## Was Session 020 bisher gemacht hat (Architekt-Bericht)

1. **Environment verifiziert:** `faster-whisper 1.2.1` ist in `.venv` (Python 3.14) bereits installiert — kein pip-Drama.
2. **Voice-Pipeline-Code gelesen:** [audio_extractor.py](../agents/extractors/audio_extractor.py), [bot.py:258-262](../bot.py#L258-L262), [extractor.py:193-195](../agents/extractors/extractor.py#L193-L195) — alles intakt.
3. **`language_detected` end-to-end nachgegangen:** Whisper setzt es korrekt im `ExtractedContent`, aber **Supervisor.classify und LanguageAgent.detect_words ignorieren das Feld**. Routing läuft rein über Text-Klassifikation durch Haiku. (→ Befund #1, separat unten)
4. **Trocken-Test geschrieben** ([scripts/test_voice.py](../scripts/test_voice.py)) — generiert 3 gTTS-Samples (DE / ES / DE-Mix) und schickt sie durch `extract_audio()` + `run_ingest()` (Dry-Run, keine Wiki-Writes).
5. **Test ausgeführt** — Resultate unten.

---

## Konkrete Daten

### Test-Ergebnisse (Dry-Run, alle 3 Samples)

| Sample | Whisper-Lang | Erkannt | Pipeline-Latenz | Intent | Wiki-Writes geplant |
|---|---|---|---|---|---|
| DE kurz (~10s Audio) | de OK | richtig | **15s** | personal_fact | **1** (PersonalFact) |
| **ES kurz (~9s Audio)** | es OK | richtig | **245s** ⚠️ | both | **22** ⚠️ |
| Mix lang (~25s Audio, DE mit ES-Wort "ensimismado") | de OK | richtig | **25s** | both | **2** (1 Fact + 1 Vocab) OK |

**Zoom auf den ES-Sample (1 Voice-Nachricht, "Hoy aprendí una palabra nueva en español, madrugada. Significa la hora antes del amanecer."):**

22 geplante Wiki-Writes:
- 1 PersonalFact
- **15 VocabEntries** — `hoy`, `aprend`, `una`, `palabra`, `nueva`, `en`, `español`, `madrugada`, `significa`, `la`, `hora`, `antes`, `del`, `amanecer`, plus eine Slug-Variante
- **6 LanguageBridges** — meist auf Funktionswörter (`la`, `en`, `del`, `una`, `hoy`)

Davon **lernens-würdig laut menschlicher Einschätzung:** vielleicht `madrugada`, `amanecer`. Eventuell `aprender`. Der Rest ist Schul-Wortschatz oder reine Funktionswörter.

### Erst-Call-Latenz (separater Befund, nicht der Hauptpunkt)

Der allererste Whisper-Call **lädt das `small`-Modell (~460 MB) synchron** im Telegram-Voice-Handler-Thread → **703 Sekunden** in meinem Test. Folgecalls sind 5–10s. Ein Warm-up beim Bot-Start oder eine Nutzer-Mitteilung ("⏳ Lade Transkriptionsmodell, einmalig...") wäre freundlich. Liegt in Architekt-Autorität, mache ich nach deiner Vocab-Entscheidung.

### Kosten-Hochrechnung der Vokabel-Explosion

Aus [hinweise/technischer_hinweis.md](../hinweise/technischer_hinweis.md) §6 (Session-017-Messung):
- 1 VocabEntry = 1 Sonnet-Call (`create_vocab`) ≈ **$0.0068**
- 1 LanguageBridge = 1 Sonnet-Call (`find_bridges`) ≈ ~$0.005
- ES-Sample: 15 × $0.0068 + 6 × $0.005 = **~$0.13** + Haiku-Overhead → ca. **$0.15 pro spanischer Voice-Nachricht**

Wenn der Nutzer 1 ES-Voice/Tag schickt → **$4.50/Monat** allein durch diesen Bug. Das ist **45–90% des kompletten LLM-Budgets** ($5–10/Monat laut PO-Profil).

Bei 3 ES-Voices/Tag (realistisch für aktiven Spanischlerner) → **$13.50/Monat** → **Budget gesprengt.**

### Wiki- und UX-Wirkung

Jede ES-Voice würde produzieren:
- **22 Markdown-Files** in `wiki/personal/facts/` + `wiki/language/vocab/` + `wiki/language/bridges/`
- **22 neue Einträge in `index.md`** (auch nach S018-Dedup-Fix, weil neue Slugs)
- I1-Bestätigung im Bot würde rendern: **"22 Wiki-Seiten erstellt — la, en, del, una, hoy…"** — Demoralisierend, weil 90% Müll ist.
- Sobald MVP-2-Anki-Export aktiv ist (ENT-044, geplant nach Voice): **22 Anki-Karten** pro Voice. Karteikartenflut killt das Lernen.

---

## Architektur-Hintergrund

### Wie das Routing heute funktioniert

```
raw_event[content="Hoy aprendí..."]
   ↓
Supervisor.classify (Haiku-Prompt: "personal_fact / vocab / both / query / lint")
   → bei vermischtem Inhalt → "both"
   ↓ (parallel)
DiaryAgent.process       LanguageAgent.process
   ↓                         ↓ detect_words (Haiku-Prompt: "List all non-German words")
1 PersonalFact            ↓ create_vocab × N (Sonnet pro Wort)
                          ↓ find_bridges × M (Sonnet pro Bridge)
                          → 15 VocabEntries + 6 Bridges
```

`language_detected` aus dem Whisper-Info-Object (`"es"`) wird im `raw_event` persistiert, **aber nirgends abgefragt**. Die Klassifikation und der Detect-Words-Prompt arbeiten nur auf `content` und `user_hint`.

Der Detect-Prompt ([language_agent.py:26-45](../agents/language_agent.py#L26-L45)) enthält keinerlei Filter für:
- Funktionswörter
- A1/Schul-Wortschatz
- Maximale Anzahl pro Input
- Wörter, die der Nutzer schon kennt (existieren als VocabEntry?)

### Warum das auch ohne Voice ein Problem ist

Der Bug ist **nicht voice-spezifisch.** Wenn der Nutzer einen rein-spanischen Text in den Bot tippt, passiert dasselbe. Voice macht ihn nur sichtbarer, weil sich Spanisch sprechen leichter anfühlt als Spanisch tippen. Das heißt: deine Entscheidung ist eine **grundsätzliche Policy zum LanguageAgent**, kein Voice-Pflaster.

### Was bereits ENT-* entschieden ist (nicht neu erfinden)

- [ENT-014](../doc/ENTSCHEIDUNGEN.md): LanguageAgent ist verantwortlich für VocabEntries — **dass** er existiert, steht nicht zur Debatte.
- [ENT-029](../doc/ENTSCHEIDUNGEN.md): "both"-Intent läuft parallel via Send() — bleibt.
- [ENT-044](../doc/ENTSCHEIDUNGEN.md): Voice-Ingest ist MVP-2-Erstwelle. Der hier diskutierte Bug bremst die Erfüllung.
- [ENT-024](../doc/ENTSCHEIDUNGEN.md): Story-Lab-Voice-Coaching ist tot — kein Bezug zu dieser Frage.

---

## Optionen — was du zwischen wählen kannst

Ich habe vier saubere Optionen vorbereitet. Bitte eine wählen (oder eine eigene formulieren, falls du einen Pfad siehst, den ich übersehen habe).

### Option 1 — Hint-Gate (Architekt-Empfehlung)

**Regel:** VocabEntries werden **nur** erzeugt, wenn entweder
- `user_hint` enthält ein Vokabel-Marker (`#vocab`, `vokabel`, `#vocab madrugada`), **oder**
- Der Input ist überwiegend deutsch (`language_detected == "de"`) — dann werden eingestreute Fremdwörter wie heute extrahiert.

**Konsequenz:**
- Du sprichst spontan ES → wird PersonalFact ("Heute habe ich Spanisch geübt"). Kein Vokabel-Lärm.
- Du willst aktiv Vokabeln aus einer ES-Voice → schickst zuerst eine Caption "#vocab" oder sagst am Anfang "Vokabeln:".
- DE-Story mit ES-Wort (wie der Mix-Test) → funktioniert weiterhin, "ensimismado" wird zur Vokabel.

**Code-Aufwand:** ~5–15 Zeilen. Gate kann sitzen in [supervisor.py:90](../agents/supervisor.py#L90) (Routing-Ebene) oder [language_agent.py:188](../agents/language_agent.py#L188) (Agent-Ebene). Ich empfehle Routing-Ebene, weil es "both" bei pure-ES auf "personal_fact" downgradet und damit auch die parallel-Send-Last spart.

**Kosten:** keine zusätzlichen LLM-Calls. Spart Geld.

**Verlust:** Wenn der Nutzer **spontan** ein neues ES-Wort beim Sprechen entdeckt, ohne Hint, ohne DE-Mix → keine automatische Vokabel. Workaround: nachschicken mit Hint, oder DE-Satz drumherum sprechen.

**Architektonischer Bonus:** Nutzt das `language_detected`-Feld, das aktuell tot rumliegt — räumt damit Befund #1 mit auf.

### Option 2 — Stopword-Filter + Hard-Cap

**Regel:** Stopword-Liste filtert Funktionswörter (`la, el, en, un, una, de, del, hoy, ...`). Zusätzlich Cap bei max. 3 VocabEntries pro Input. Sonnet entscheidet pro Wort "lernenswert oder Trivialwort?".

**Konsequenz:**
- Funktioniert ohne Hint.
- Stopword-Liste muss gepflegt werden (DE/EN/ES) → Wartungs-Aufwand.
- Cap=3 ist arbiträr → bei ES-Volltext mit 5 echten Vokabeln gehen 2 verloren.

**Code-Aufwand:** ~30–50 Zeilen, neue Stopword-Liste-Datei.

**Kosten:** Mehr Haiku-Calls (Filter-Entscheidung) + bestehende Sonnet-Calls. Eher teurer.

### Option 3 — Practice-Intent (neuer Routing-Pfad)

**Regel:** Klassifikation bekommt einen 6. Intent: `language_practice` ("der Nutzer übt aktiv Sprache, kein Lernmaterial extrahieren"). Wird gespeichert als PersonalFact mit Tag `practice`.

**Konsequenz:**
- Saubere semantische Trennung.
- Eröffnet später: praxis_log-Counter, "du hast diese Woche 12 Mal Spanisch geübt"-Stats.

**Code-Aufwand:** ~40–80 Zeilen, Klassifikations-Prompt erweitern, neuer Routing-Branch.

**Aufwand vs. Nutzen:** Bigger surgery. Kann später nachgeholt werden, wenn aus den ES-Voice-PersonalFacts (Option 1) ein Muster sichtbar wird.

**Verbindung zu MVP-2:** Wäre eine Scope-Erweiterung. Würde Voice-Verifikation um 1 Session verzögern.

### Option 4 — Bug akzeptieren, MVP-2-Voice ohne Vokabel-Filter freigeben

**Regel:** Voice-Pipeline so live nehmen, wie sie ist. Bug in `hinweise/technischer_hinweis.md` dokumentieren, Fix in spätere Session.

**Konsequenz:**
- Voice ist nominal-verifiziert, aber nicht produktionsreif für ES.
- Risiko: Nutzer schickt ES-Voice → Wiki + Anki vermüllen → Vertrauen verloren → MVP-2-Aufnahme zurückgedreht.
- Budget-Risiko real.

**Aufwand:** 0.

**Wann sinnvoll:** Wenn du bereit bist, Voice nur für DE-Inputs zu nutzen, bis ein nächster Sprint die Vocab-Policy klärt. Erfordert Selbstdisziplin: keine ES-Voice schicken.

---

## Was die ideale PO-Antwort enthält

Damit ich nach deiner Antwort sofort weiterarbeiten kann, brauche ich:

1. **Gewählte Option:** 1 / 2 / 3 / 4 (oder eigener Vorschlag)
2. **Bei Option 1:** Gate-Lokation — Routing-Ebene (`supervisor.py`) oder Agent-Ebene (`language_agent.py`)? Architekt-Empfehlung: Routing-Ebene.
3. **Bei Option 1:** Welche Hints triggern? Nur `#vocab`, oder auch `vokabel`, `vocab`, `#es`, ...? Architekt-Empfehlung: `#vocab` und `vokabel` als Substring (case-insensitive), nichts weiter — Erweiterungen nach erstem Live-Lauf.
4. **ENT-Eintrag:** Soll ich (Architekt) den Entwurf für die ENT-* Begründung im Anschluss liefern, oder schreibst du sie selbst nach Entscheidung? Konvention sagt: PO schreibt ENT-Einträge.
5. **Session-020-Fortsetzung:** Soll Session 020 nach deiner Entscheidung weiterlaufen (Architekt setzt Fix um, dann Live-Test mit echter Stimme)? Oder schließen wir 020 als "Voice mechanisch verifiziert, ES-Vocab-Bug eskaliert" und machen aus dem Fix eine eigene Session 021?

---

## Was du nicht entscheiden sollst (Scope-Schutz)

- **Keine Änderung am VocabEntry-Schema.** SCHEMA.md / [ENT-005](../doc/ENTSCHEIDUNGEN.md) bleibt.
- **Kein neuer Agent** — schon explizit im 020-Brief ausgeschlossen.
- **Kein Story-Lab-Voice-Coaching** — [ENT-024](../doc/ENTSCHEIDUNGEN.md) bleibt final.
- **Keine Diskussion über `master` vs. `main`** — [ENT-039](../doc/ENTSCHEIDUNGEN.md).

---

## Zwei separate Befunde, die unabhängig sind (nicht in dieser Eskalation entscheiden)

Diese beiden Punkte landen auch im finalen Brief 021, aber sie blockieren dich nicht jetzt:

### Befund #1: `language_detected` ist totes Feld
Whisper setzt es, aber Supervisor + LanguageAgent ignorieren es. Wenn du Option 1 wählst, wird das Feld erstmals genutzt → automatisch repariert. Bei Option 2/3/4 bleibt es ungenutzt → ich dokumentiere es als technische Schuld.

### Befund #2: Erst-Call-Latenz von 703s (Whisper-Modell-Download)
Liegt in Architekt-Autorität. Ich werde nach deiner Vocab-Entscheidung entscheiden, ob Warm-up beim Bot-Start (`_get_model()` in `bot.py.main()`) oder Nutzer-Hinweis-Text ("⏳ Lade Transkriptionsmodell..."). Tendenz: Warm-up. Kostet 0, vermeidet Wartebalken-Drama.

---

## Pflichtlektüre (in der Reihenfolge)

```
sessions/020_2026-04-20.md                       ← die laufende Session, in der wir stecken
doc/ENTSCHEIDUNGEN.md                            ← ENT-014 (Agent-Set), ENT-029 (both), ENT-044 (Voice-MVP-2)
agents/language_agent.py:26-45, 182-206          ← der Detect-Prompt + die Detect-Funktion
agents/supervisor.py:71-103                      ← Klassifikation + Routing
hinweise/technischer_hinweis.md §6               ← Kostenmessung-Baseline
scripts/test_voice.py                            ← Reproduktion (run: --generate --no-pipeline für Lang-Check, --generate für Pipeline)
```

---

## Meine Empfehlung in einem Satz

**Option 1, Gate in `supervisor.py`, nur `#vocab`/`vokabel` als Hint, ENT-047 anlegen, Session 020 nach Fix abschließen mit Live-Test.**

---

**(?) Welche Option, und mit welcher Verfeinerung? (?)**
