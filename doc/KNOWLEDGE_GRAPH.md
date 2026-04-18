# KNOWLEDGE_GRAPH.md — Ingest, Seitenstruktur & Lint
> Version: 0.2 | Datum: 2026-04-18 | Status: DRAFT

---

## 0. Raw Data Pipeline — Vom Input zur verarbeitbaren Quelle

Bevor die Ingestion-Pipeline (§3) anläuft, muss jeder Input in ein **einheitliches Textformat** gebracht werden. Das übernimmt der **Extractor** — eine neue Komponente zwischen Telegram-Receiver und Ingestion-Agent.

### 0.1 Zwei Quell-Wege

```
Weg A: Telegram-Input (Echtzeit)
─────────────────────────────────
Nutzer schickt [Text | URL | Bild | PDF | Voice | YouTube-Link]
    + optionaler Kontext-Hint ("interessant für Vokabel", "story-Idee", "#vocab")
    → Telegram-Bot empfängt
    → Extractor erkennt Typ, extrahiert Inhalt
    → raw/sources/ (permanente Kopie) + raw/events/ (Verarbeitungs-Queue)
    → normaler Ingest-Flow startet

Weg B: Direkter Datei-Drop (manuell)
─────────────────────────────────────
Nutzer legt Datei in raw/sources/ ab (z.B. via Obsidian oder Dateisystem)
    → File-Watcher (watchdog-Library) erkennt neue Datei
    → Extractor greift an
    → raw/events/ Eintrag wird erzeugt
    → normaler Ingest-Flow startet
```

**Kernregel:** `raw/sources/` ist die **permanente, unveränderliche Kopie** des Originals. `raw/events/` ist die **Verarbeitungs-Queue** — hier liegt der extrahierte Text, den die Pipeline tatsächlich liest.

### 0.2 Zwei Verarbeitungs-Modi

Der **Kontext-Hint** des Nutzers steuert ob sofort verarbeitet wird oder nur gespeichert:

| Input                        | Modus           | Was passiert                                         |
|------------------------------|-----------------|------------------------------------------------------|
| URL ohne Hinweis             | **Quick-Save**  | Gespeichert in raw/sources/, Extraktion später       |
| Bild ohne Hinweis            | **Quick-Save**  | Gespeichert in raw/assets/, Extraktion später        |
| URL + Hinweis-Text           | **Process-Now** | Sofort extrahieren + durch Ingest-Pipeline           |
| Bild + Hinweis-Text          | **Process-Now** | Claude Vision sofort, dann Ingest                    |
| Jeder Text                   | **Process-Now** | Immer sofort (kein Extractions-Overhead)             |

**Quick-Save-Queue:** Der Lint-Agent prüft täglich ob unverarbeitete Quellen in raw/sources/ liegen und fragt den Nutzer via Telegram: *"Du hast 4 gespeicherte Links — jetzt verarbeiten?"*

### 0.3 Extractor: Format → Text

Der Extractor ist eine Python-Klasse mit Format-spezifischen Handlern:

```python
# extractors/extractor.py

class Extractor:
    def extract(self, input: TelegramInput | FilePath) -> ExtractedContent:
        match self._detect_type(input):
            case "text":    return self._extract_text(input)
            case "url":     return self._extract_url(input)
            case "pdf":     return self._extract_pdf(input)
            case "image":   return self._extract_image(input)
            case "audio":   return self._extract_audio(input)
            case "youtube": return self._extract_youtube(input)
            case "video":   return self._extract_video_audio(input)

class ExtractedContent:
    text: str            # normalisierter Volltext
    title: str           # Titel/Beschreibung der Quelle
    source_type: str     # original Format
    source_path: str     # Pfad in raw/sources/ oder raw/assets/
    user_hint: str       # optionaler Nutzer-Kontext
    language_detected: str
```

### 0.4 Format-Handler im Detail

#### URLs & Webseiten
```python
# Tool: requests + BeautifulSoup (lokal, kostenlos)
# Fallback: playwright (für JS-heavy Seiten wie SPAs)

def _extract_url(self, url: str) -> ExtractedContent:
    response = requests.get(url, headers=BROWSER_HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Haupt-Content extrahieren (ignoriert Nav, Footer, Ads)
    article = soup.find("article") or soup.find("main") or soup.body
    text = article.get_text(separator="\n", strip=True)
    
    # Speichern: Markdown-Version in raw/sources/
    save_as_markdown(url, text, title=soup.title.string)
    
    return ExtractedContent(text=text, source_type="url", ...)
```

**Obsidian Web Clipper Alternative:** Der Nutzer kann den Obsidian Web Clipper Browser-Extension nutzen — dieser konvertiert Webseiten direkt in formatiertes Markdown und legt es in `raw/sources/`. File-Watcher triggert dann automatisch.

#### PDFs & Dokumente
```python
# Tool: pdfplumber (lokal, kostenlos, besser als pypdf für Layout)

def _extract_pdf(self, path: Path) -> ExtractedContent:
    with pdfplumber.open(path) as pdf:
        pages_text = [page.extract_text() for page in pdf.pages]
    text = "\n\n--- Seite {i} ---\n\n".join(pages_text)
    # Kopie liegt bereits in raw/sources/ (Nutzer hat sie hingelegt)
    return ExtractedContent(text=text, source_type="pdf", ...)
```

#### Bilder & Screenshots
```python
# Tool: Claude Vision (bereits im Stack — kein Extra-Tool)

VISION_PROMPT = """Analysiere dieses Bild.
- Falls es überwiegend Text enthält (Screenshot, Whiteboard, Dokument):
  extrahiere den vollständigen Text möglichst originalgetreu.
- Falls es überwiegend visuell ist (Foto, Szene, Kunstwerk):
  beschreibe den Inhalt detailliert.
- Falls beides zutrifft: Text zuerst, dann visuelle Beschreibung.
Nutzer-Hinweis: '{user_hint}'"""

def _extract_image(self, image_path: Path) -> ExtractedContent:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    response = claude_client.messages.create(
        model="claude-haiku-4-5",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "data": image_data}},
                {"type": "text", "text": VISION_PROMPT.format(user_hint=user_hint)}
            ]
        }]
    )
    # Kein separater Typ für Screenshots/Whiteboards — Claude entscheidet selbst
    # was dominiert. Die Pipeline sieht immer nur den extrahierten Text.
    return ExtractedContent(text=response.content[0].text, source_type="image", ...)
```

#### Sprach-Nachrichten (Voice)
```python
# Tool: faster-whisper (lokal, kostenlos, schneller als OpenAI Whisper)
# Vorteil: läuft komplett offline — gut für private Inhalte

from faster_whisper import WhisperModel

model = WhisperModel("small", device="cpu")   # "small" reicht für klare Sprache

def _extract_audio(self, audio_path: Path) -> ExtractedContent:
    segments, info = model.transcribe(str(audio_path), language="de")
    text = " ".join([s.text for s in segments])
    return ExtractedContent(text=text, source_type="voice", language_detected=info.language)
```

#### YouTube-Links
```python
# Tool: youtube-transcript-api (kostenlos, kein API-Key nötig)
# Nutzt offizielle YouTube-Untertitel (auto-generiert oder manuell)

from youtube_transcript_api import YouTubeTranscriptApi

def _extract_youtube(self, url: str) -> ExtractedContent:
    video_id = self._parse_video_id(url)
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["de", "es", "en"])
    text = " ".join([entry["text"] for entry in transcript])
    # Kein Download des Videos — nur Text-Transcript
    return ExtractedContent(text=text, source_type="youtube", ...)
```

#### Lokale Videos
```python
# Aufwand: hoch. Strategie: nur Audio extrahieren → dann Whisper
# Tool: ffmpeg (CLI) + faster-whisper

def _extract_video_audio(self, video_path: Path) -> ExtractedContent:
    audio_path = video_path.with_suffix(".mp3")
    subprocess.run(["ffmpeg", "-i", str(video_path), "-q:a", "0", "-map", "a", str(audio_path)])
    return self._extract_audio(audio_path)
    # Hinweis: Bild-Inhalt des Videos wird ignoriert — nur Sprache
```

### 0.5 Nutzer-Hinweis als Routing-Signal

Der optionale Hinweis-Text des Nutzers wird **direkt in den SupervisorState** übernommen und beeinflusst Klassifikation und Tier-Wahl:

| Hinweis-Beispiel                          | Effekt                                              |
|-------------------------------------------|-----------------------------------------------------|
| *(kein Hinweis)*                          | Quick-Save oder Auto-Klassifikation                 |
| `"interessantes Vokabel"` / `#vocab`      | Language Agent priorisiert                          |
| `"gute Geschichte"` / `#story`            | Diary Agent priorisiert, story_score direkt berechnen|
| `"für Anki"`                              | Language Agent + sofortiger Anki-Export             |
| `"privat"` / `#private`                   | sensitivity: private → Ollama, kein Cloud-LLM       |
| `"Hintergrund zu Flamenco"`               | Free-Text → Haiku klassifiziert Intent              |

```
Telegram: [YouTube-Link] + "gute Erklärung zu Flamenco, interessant für Geschichte"
    → Extractor: YouTube-Transcript extrahieren
    → Hinweis: "interessant für Geschichte" → Intent-Hint: CulturalEntry + PersonalFact-Korrelation
    → Supervisor: Language Agent (CulturalEntry c_es_flamenco updaten)
                + Diary Agent (Korrelation zu bestehenden Flamenco-Facts prüfen)
```

### 0.6 Speicher-Konventionen

```
raw/
├── sources/               # Textuell extrahierbare Quellen
│   ├── YYYY-MM-DD_kebab-titel.md      # Webseiten (Markdown-konvertiert)
│   ├── YYYY-MM-DD_kebab-titel.pdf     # PDFs (Original)
│   └── YYYY-MM-DD_youtube-[id].txt   # YouTube-Transkript
│
├── assets/                # Medien — LLM liest Beschreibung, nicht Original
│   ├── YYYY-MM-DD_beschreibung.jpg    # Original-Bild
│   └── YYYY-MM-DD_beschreibung.png
│
└── events/                # Verarbeitungs-Queue (normalisierter Text)
    ├── YYYY-MM-DDTHH-MM-SS_telegram.json   # Telegram-Text-Input
    ├── YYYY-MM-DDTHH-MM-SS_url.json        # Extrahierter Web-Content
    ├── YYYY-MM-DDTHH-MM-SS_pdf.json        # Extrahierter PDF-Content
    ├── YYYY-MM-DDTHH-MM-SS_image.json      # Claude-Vision-Beschreibung
    └── YYYY-MM-DDTHH-MM-SS_voice.json      # Whisper-Transkript
```

Jede `raw/events/`-JSON hat das gleiche Schema — egal welches Format der Input war:

```json
{
  "timestamp": "2026-04-18T09:32:11Z",
  "source": "telegram",
  "source_type": "youtube",
  "original_ref": "raw/sources/2026-04-18_flamenco-arte.txt",
  "language_detected": "es",
  "content": "[normalisierter Volltext, extrahiert]",
  "user_hint": "gute Erklärung zu Flamenco, interessant für Geschichte",
  "processed": false,
  "wiki_refs": []
}
```

---

## 1. Was eine gute Wiki-Seite ausmacht

Jede Seite im Knowledge Graph erfüllt drei Qualitätskriterien:

1. **Eigenständig lesbar.** Eine Seite muss ohne Kontext verständlich sein — der LLM kann sie isoliert laden und sofort nützlichen Inhalt extrahieren.
2. **Dicht verlinkt.** Mindestens 2 ausgehende Links (`related:`). Eine Seite ohne Links ist eine Insel — sie trägt nicht zum Graphen bei.
3. **Klar typisiert.** Das Frontmatter ist vollständig ausgefüllt. `status` ist aktuell. Der LLM weiß sofort was diese Seite ist und in welchem Zustand.

---

## 2. Seiten-Templates

### 2.1 Template: `PersonalFact`

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

## Korrelationen im Graph
[Links zu thematisch verwandten Facts, CulturalEntries oder Concepts die diesen Fakt bereichern]

## Ausarbeitung
[Leer bei status:raw — wird vom Diary-Agent bei Elaboration befüllt]

## Übungsnotizen
[Leer bis status:story-ready — Feedback aus Übungsrunden]
```

**Konkretes Beispiel:**

```markdown
---
type: PersonalFact
created: 2026-04-18
updated: 2026-04-18
status: elaborated
sensitivity: sensitive
story_score: 7
tags: [spanisch, tanz, kultur, lernen]
sources: [raw/events/2026-04-18T09-32-11_telegram.json]
related:
  - "[[pf_2026-02-01_erste-flamenco-show]]"
  - "[[c_es_flamenco]]"
  - "[[v_es_duende]]"
  - "[[con_spanische-kultur]]"
---

# Flamenco-Kurs: Der Lehrer und das Duende

## Kern-Fakt
Ich war beim ersten Flamenco-Kurs. Der Lehrer hörte mittendrin auf, schaute mich an
und sagte: "Du denkst noch. Hör auf zu denken."

## Kontext
- **Wann:** 18. April 2026, Abend
- **Wo:** Tanzschule, München
- **Mit wem:** Kursgruppe (~8 Personen), spanischer Lehrer
- **Stimmung/Atmosphäre:** Konzentriert, leicht einschüchternd, dann befreiend

## Narrative Hook
Der Moment wo ein Fremder einen zwingt, den eigenen Kopf loszulassen — und es
funktioniert. Universell: jeder kennt das "zu viel denken"-Problem.

## Score-Begründung
- Überraschungsmoment (0–3): 2 — unerwartete direkte Ansage des Lehrers
- Anschlussfähigkeit (0–3): 3 — "zu viel denken" kennt jeder
- Sensorische Details (0–2): 1 — Tanzschule, Gruppe vorhanden
- Pointe/Wendung (0–2): 1 — es hat funktioniert
- **Gesamt: 7**

## Korrelationen im Graph
- [[c_es_flamenco]] — Duende als Kernbegriff des Flamenco, direkte Verbindung
- [[v_es_duende]] — das Wort das der Lehrer meinte, ohne es zu sagen
- [[pf_2026-02-01_erste-flamenco-show]] — erstes Flamenco-Erlebnis, Muster entsteht
```

---

### 2.2 Template: `VocabEntry`

```markdown
---
type: VocabEntry
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: raw | elaborated
language: es | en | de | fr | ...
difficulty: A1 | A2 | B1 | B2 | C1 | C2
anki_id: null
tags: []
sources: []
related: []
---

# [Wort]

## Übersetzungen
| Sprache | Übersetzung | Nuance |
|---------|-------------|--------|
| de      |             |        |
| en      |             |        |

## Grammatik
- **Wortart:** 
- **Genus:** (falls Nomen)
- **Konjugation:** (falls Verb, Kurzform)

## Beispielsätze
1. [Einfacher Satz, A-Niveau]
2. [Mittlerer Satz, B-Niveau]
3. [Komplexer Satz, C-Niveau oder idiomatisch]

## Eselsbrücke
[LLM-generiert, nutzt Muttersprache und bekannte Konzepte des Nutzers]

## Cross-Language-Bridges
- **[Sprache]:** [[lb_..._...]] — [kurze Erklärung der Verbindung/des Unterschieds]

## Erschienen in
[Links zu PersonalFacts oder CulturalEntries wo dieses Wort eine Rolle gespielt hat]
```

**Konkretes Beispiel:**

```markdown
---
type: VocabEntry
created: 2026-04-18
updated: 2026-04-18
status: elaborated
language: es
difficulty: B2
anki_id: null
tags: [kultur, gefühl, flamenco, musik]
sources: [raw/events/2026-04-18T09-32-11_telegram.json]
related:
  - "[[c_es_flamenco]]"
  - "[[pf_2026-04-18_flamenco-kurs-lehrer]]"
  - "[[lb_es-de_duende-gefuehl]]"
---

# duende

## Übersetzungen
| Sprache | Übersetzung | Nuance |
|---------|-------------|--------|
| de      | Zauber, Magie, Seele | Kein direktes Äquivalent — konzeptuell näher an "Gänsehaut-Moment" |
| en      | (spirit, charm) | Auch im Englischen oft unübersetzt gelassen |

## Grammatik
- **Wortart:** Maskulines Nomen
- **Genus:** el duende

## Beispielsätze
1. *El cantaor tiene duende.* — Der Sänger hat Duende.
2. *Esa actuación me llegó al alma — había duende.* — Diese Darbietung hat mich tief berührt.
3. *El duende no se aprende, se siente.* — Duende lernt man nicht, man fühlt es.

## Eselsbrücke
"Duende" klingt wie "der Wunder" — und das ist es auch: der Moment wo Kunst
zu echtem Wunder wird. Erinnert an den Flamenco-Lehrer der sagte "hör auf zu denken."

## Cross-Language-Bridges
- **DE:** [[lb_es-de_duende-gefuehl]] — Konzeptlücke: DE hat kein Wort für diesen Moment
- **EN:** [[lb_es-en_duende-sublime]] — Nähe zu "sublime" aber emotionaler, körperlicher

## Erschienen in
- [[pf_2026-04-18_flamenco-kurs-lehrer]] — Lehrer verkörperte Duende ohne das Wort zu sagen
```

---

### 2.3 Template: `LanguageBridge`

```markdown
---
type: LanguageBridge
created: YYYY-MM-DD
languages: [es, de]
bridge_type: cognate | faux-ami | concept-gap | structural-parallel
related: []
---

# [Sprache A] ↔ [Sprache B]: [Thema]

## Die Verbindung
[1-2 Sätze: Was verbindet oder trennt diese sprachlichen Konzepte?]

## Beteiligte Einträge
- [[v_[lang]_wortA]] — [kurze Beschreibung]
- [[v_[lang]_wortB]] — [kurze Beschreibung]

## Lernrelevante Erkenntnis
[Warum ist diese Brücke/Lücke für den Nutzer wichtig zu kennen?]

## Beispiel-Kontrast
| ES | DE | Kommentar |
|----|----|----|
| duende | ??? | Konzeptlücke — kein DE-Äquivalent |
```

---

## 3. Ingest-Workflow im Detail

Ein vollständiges Beispiel von Telegram-Nachricht bis fertiger Wiki-Seite.

### Input

```
Telegram-Nachricht, 18. April 2026, 09:32:
"war heute beim Flamenco-Kurs, unser Lehrer hat über duende gesprochen —
hatte so ein Aha-Moment dabei"
```

### Schritt 1 — Normalisierung (Ingestion Agent, Haiku)

```json
// raw/events/2026-04-18T09-32-11_telegram.json
{
  "timestamp": "2026-04-18T09:32:11Z",
  "source": "telegram",
  "language_detected": "de",
  "content": "war heute beim Flamenco-Kurs, unser Lehrer hat über duende gesprochen — hatte so ein Aha-Moment dabei",
  "processed": false,
  "wiki_refs": []
}
```

### Schritt 2 — Klassifikation (Ingestion Agent, Haiku)

```
Intent-Analyse:
  - "Flamenco-Kurs" → persönliches Erlebnis → PersonalFact
  - "duende" → spanisches Wort → VocabEntry
  → classified_intent: "both"
  → assigned_agents: ["diary_agent", "language_agent"]
```

### Schritt 3 — Graph Context Match (graph_reader)

```
Schlüsselbegriffe extrahiert: [flamenco, duende, kurs, lehrer, aha-moment]

Index-Scan → Treffer:
  1. [[pf_2026-02-01_erste-flamenco-show]]  — story_score: 6, tag: flamenco
  2. [[c_es_flamenco]]                       — CulturalEntry: Flamenco
  3. [[con_spanische-kultur]]                — Concept: Spanische Kultur

graph_context = [diese 3 Seiten, vollständig geladen]
```

### Schritt 4 — Parallele Agent-Ausführung (Sonnet)

Beide Agenten erhalten: `raw_event` + `user_profile` + `graph_context`

**Diary Agent bemerkt:**
- `graph_context` enthält bereits `pf_erste-flamenco-show` (story_score 6)
- Das ist ein Muster: zweites Flamenco-Erlebnis, diesmal mit konkretem Aha-Moment
- Aha-Moment hat starke Anschlussfähigkeit → story_score erhöht
- Erzeugt: `pf_2026-04-18_flamenco-kurs-lehrer.md` mit story_score: 7

**Language Agent bemerkt:**
- "duende" kommt aus `graph_context` (c_es_flamenco erwähnt den Begriff)
- Kein bestehender VocabEntry für "duende" im Index
- Erstellt: `v_es_duende.md` mit vollständigem Kontext
- Erstellt: `lb_es-de_duende-gefuehl.md` (Konzeptlücke DE↔ES)

### Schritt 5 — Supervisor Review

```
Prüft WikiWrite-Objekte gegen graph_context:

✓ pf_flamenco-kurs: story_score 7 — konsistent mit graph_context-Muster
✓ v_es_duende: korrekt verlinkt zu c_es_flamenco und pf_flamenco-kurs
✓ lb_es-de: korrekt typisiert als concept-gap
✓ related:-Felder vollständig

→ supervisor_verdict: "accept"
→ sensitivity: "sensitive" (PersonalFact mit Ortsbezug)
→ Freigabe-Flag: Ja (story_score > 7, Nutzer-Benachrichtigung)
```

### Schritt 6 — Draft Write & Index Update

```
graph_writer schreibt 3 Dateien auf draft-Branch:
  wiki/personal/facts/pf_2026-04-18_flamenco-kurs-lehrer.md
  wiki/language/vocab/v_es_duende.md
  wiki/language/bridges/lb_es-de_duende-gefuehl.md

index_updater hängt an index.md an:
  ## PersonalFacts (13)   ← war 12
  - [[pf_2026-04-18_flamenco-kurs-lehrer]] — Aha-Moment im Kurs, story_score: 7 ⭐
  ...
  ## VocabEntries — ES (48)   ← war 47
  - [[v_es_duende]] — "Zauber/Seele", Konzeptlücke zu DE
  ...

log_writer hängt an log.md an:
  ## [2026-04-18T09:32] ingest | "Flamenco-Kurs + duende" → 3 Seiten, score:7 → Freigabe ausstehend
```

### Schritt 7 — Nutzer-Benachrichtigung

```
Telegram-Nachricht an Nutzer:
┌─────────────────────────────────────────────────┐
│  ✨ Neuer High-Score Personal Fact (7/10)        │
│                                                 │
│  "Flamenco-Kurs: Der Lehrer und das Duende"     │
│  + Vokabel: duende  + 1 Sprachbrücke            │
│                                                 │
│  [Freigeben ✓]  [Details anzeigen]              │
└─────────────────────────────────────────────────┘
```

---

## 4. Linking-Strategie

Links entstehen nicht zufällig — der Language/Diary-Agent folgt diesen Regeln:

### 4.1 Wann wird verlinkt?

| Von → Nach          | Regel                                                         |
|---------------------|---------------------------------------------------------------|
| PersonalFact → VocabEntry | Wenn ein Wort im Erlebnis eine Rolle gespielt hat      |
| PersonalFact → PersonalFact | Wenn Ort, Person, oder Thema übereinstimmt          |
| PersonalFact → CulturalEntry | Wenn kultureller Kontext das Erlebnis erklärt       |
| VocabEntry → CulturalEntry | Immer wenn Wort kulturell eingebettet ist            |
| VocabEntry → LanguageBridge | Wenn Brücke zu einer anderen Sprache existiert      |
| Concept → Alle       | Concept-Seiten verlinken auf alles was ihr Thema berührt     |

### 4.2 Maximale Verlinkungstiefe

Ein Agent verlinkt **maximal 5 bestehende Seiten** pro neuem Dokument. Mehr würde den Kontext unlesbar machen. Lint prüft ob offensichtliche Links fehlen.

### 4.3 Backlinks

Wenn `v_es_duende` auf `pf_flamenco-kurs` verlinkt, fügt der Language Agent **auch** in `pf_flamenco-kurs` einen Link zu `v_es_duende` ein — sofern die Seite bereits existiert. Bidirektionale Links entstehen nicht automatisch durch Obsidian, sondern müssen explizit gepflegt werden. Das ist eine der wichtigsten Lint-Aufgaben.

---

## 5. Lint-Prozess im Detail

### 5.1 Algorithmus

```python
# agents/lint_agent.py — vereinfachter Ablauf

def run_lint(wiki_root: Path) -> LintReport:
    all_pages = load_all_pages(wiki_root)          # alle MD-Dateien lesen
    link_graph = build_link_graph(all_pages)       # related:-Felder zu Adjazenzliste
    
    tasks: list[LintTask] = []
    
    for page in all_pages:
        tasks += check_orphan(page, link_graph)        # Priorität: MEDIUM
        tasks += check_stale_raw(page)                 # Priorität: HIGH
        tasks += check_missing_backlinks(page, link_graph)  # Priorität: LOW
        tasks += check_score_vs_status(page)           # Priorität: HIGH
        tasks += check_anki_gap(page)                  # Priorität: MEDIUM
    
    tasks += check_contradictions(all_pages)           # Priorität: HIGH, Sonnet nötig
    
    return LintReport(
        auto_fixable=[t for t in tasks if t.auto_fix],
        needs_user=[t for t in tasks if not t.auto_fix],
        summary=generate_summary(tasks),
    )
```

### 5.2 Symptome im Detail

#### Verwaiste Seite (MEDIUM, Auto-Fix möglich)
```
Erkennung: page nicht in link_graph.inbound_links
Fix: LLM sucht top-3 semantisch verwandte Seiten → fügt related:-Links ein
     UND fügt Backlink in den Zielseiten ein
Modell: Haiku (semantische Ähnlichkeit via Keyword-Matching reicht)
```

#### Stale Raw (HIGH, Auto-Fix teilweise)
```
Erkennung: status == "raw" AND (heute - created) > 7 Tage
Fix-Option A (Auto): Archivieren wenn story_score < 3
Fix-Option B (Nutzer): Telegram-Frage "Soll ich diesen Fakt ausarbeiten?" [Ja/Archivieren]
Modell: kein LLM nötig für Erkennung
```

#### Fehlender Backlink (LOW, Auto-Fix)
```
Erkennung: page_A.related enthält link zu page_B, aber page_B.related enthält page_A nicht
Fix: Fügt symmetrischen Link in page_B ein (append zu related:-Block)
Modell: kein LLM nötig
```

#### High-Score ungeübt (HIGH, kein Auto-Fix)
```
Erkennung: story_score >= 7 AND status != "story-ready" AND age > 14 Tage
Fix: Diary-Agent sendet Übungs-Prompt an Nutzer via Telegram
Modell: Sonnet (personalisierter Übungs-Prompt)
```

#### Anki-Lücke (MEDIUM, Auto-Fix)
```
Erkennung: type == VocabEntry AND anki_id == null AND status == "elaborated"
Fix: Language-Agent ruft AnkiConnect API auf, erstellt Karte, schreibt anki_id zurück
Modell: kein LLM nötig (template-basiert)
```

#### Widerspruch (HIGH, immer Nutzer)
```
Erkennung: Haiku scannt Paare von PersonalFacts mit Überschneidung in tags/related
           Sonnet prüft ob inhaltlicher Widerspruch besteht
Fix: Nutzer entscheidet via Telegram (InlineKeyboard: Alt / Neu / Beide)
Modell: Haiku (Kandidaten-Filterung) + Sonnet (Widerspruchs-Analyse)
```

### 5.3 Lint-Report Format

```markdown
## [2026-04-18] Lint-Report

### Zusammenfassung
- 47 Seiten geprüft
- 3 Auto-Fixes angewendet
- 2 Aufgaben warten auf Nutzer-Entscheidung

### Auto-Fixes (angewendet)
- ✅ [[v_es_madrugada]] ↔ [[c_es_nachtleben]] — Backlink ergänzt
- ✅ [[pf_2026-01-10_cafe-madrid]] — Link zu [[c_es_madrid]] ergänzt
- ✅ [[v_en_serendipity]] → Anki-Karte #4821 erstellt

### Nutzer-Entscheidungen ausstehend
- ⚠️ [[pf_2026-03-01_barcelona-trip]] — status:raw seit 48 Tagen
- ⚠️ [[pf_2026-04-18_flamenco-kurs-lehrer]] — story_score:7, noch nicht geübt
```

### 5.4 Monatlicher Graph-Health-Report

Einmal pro Monat generiert der Lint-Agent einen Überblick:

```markdown
# Graph-Health-Report — April 2026

## Wachstum
- Seiten gesamt: 61 (+14 gegenüber März)
- PersonalFacts: 13 | VocabEntries: 48 | Bridges: 8 | Concepts: 5

## Qualität
- Durchschnittlicher story_score: 6.2
- Facts mit score ≥ 7: 3 (davon 2 ungeübt)
- VocabEntries mit Anki-Karte: 41/48 (85%)
- Verwaiste Seiten: 0

## Sprachprofil
- Aktive Zielsprachen: ES (48 Einträge), EN (12 Einträge)
- Neue LanguageBridges: 3

## Empfehlungen
1. Vokabel "madrugada" — seit 6 Wochen nicht geübt, Anki-Streak unterbrochen
2. Personal Fact "Flamenco-Kurs" — bereit für Übung, story-ready?
3. Thema "Architektur Barcelona" — 3 Events erwähnt, kein Concept-Eintrag
```

---

## 6. Graph-Wachstumsphasen

Das System verhält sich in verschiedenen Phasen unterschiedlich:

| Phase        | Seitenanzahl | Index-Methode | graph_context Qualität | Schwerpunkt          |
|--------------|-------------|---------------|------------------------|----------------------|
| **Bootstrap** | 0–20         | index.md      | Gering (wenig Treffer) | Aufbau, Seeding      |
| **Wachstum**  | 20–80        | index.md      | Mittel, erste Muster   | Linking, Bridges     |
| **Reife**     | 80–150       | index.md      | Gut, Cluster erkennbar | Elaboration, Übung   |
| **Scale**     | 150+         | SQLite FTS5   | Hoch, präzise Treffer  | Synthesis, Verdichtung|

### Bootstrap-Strategie (0–20 Seiten)

Bevor der Graph genug Inhalt hat um sich selbst zu bereichern, braucht der Nutzer einen Seed. Empfohlene erste Inputs:

1. **Selbst-Interview** via Telegram: Bot stellt 10 Basis-Fragen ("Wo bist du aufgewachsen?", "Was war dein lustigstes Erlebnis letztes Jahr?") → erzeugt erste PersonalFacts
2. **Sprach-Grundstock**: 20 häufigste Spanisch-Vokabeln aus Nutzer-Kontext direkt anlegen
3. **Manuelle Seed-Seiten**: Nutzer gibt 3-5 wichtige Themen vor (z.B. "Barcelona", "Flamenco", "Argentinien") → CulturalEntries als Anker

---

## 7. Offene Fragen (Backlog)

- [ ] Bootstrap-Interview: welche 10 Fragen? Wie Antworten in PersonalFacts überführen?
- [ ] Widerspruchs-Erkennung: Haiku-Kandidatenfilter genauer definieren (Schwellwert für "Überschneidung")
- [ ] Concept-Seiten: wann erzeugt der LLM automatisch eine neue Concept-Seite? (Schwellwert: 3+ Seiten mit gleichem Tag?)
- [ ] Linking-Tiefe: maximal 5 Links pro Seite — reicht das, oder brauchen wir mehr bei Concept-Seiten?
