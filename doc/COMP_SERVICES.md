# COMP_SERVICES.md — Services Meta-Routine
> Version: 0.1 | Datum: 2026-04-18 | Status: ENTWURF — MVP-2/Phase 3 (QK-3, Session 008)
> Branch: `experiment/ge-001-services-meta-routine`
> Keine Implementierung — Entscheidungsgrundlage für spätere Sessions

---

## 0. Überblick

Services sind **domänenspezifische Übungsroutinen** die aus dem Graph-Inhalt generiert werden und das StyleProfile in Dimensionen anreichern, die Diary und Language allein nicht abdecken. Ein Service kombiniert:

```
Graph-Kontext (Interests, Facts, Concepts)
    → strukturierter Konversations-Flow via Telegram
    → Voice-Analyse (Timing + Ton)
    → context-tagged practice_log-Eintrag
    → StyleProfile-Anreicherung in neuer Domänen-Dimension
```

Der Unterschied zu Diary/Language: Services sind **domänenspezifisch** — sie erzeugen Situationen (Krypto-Erklärung, Tech-Debatte, Musik-Beschreibung) die das System sonst nie sieht.

---

## 1. Machbarkeits-Einschätzung: Autonome Implementierung (F4)

### 1.1 Was kann ein Coding-Agent heute realistisch?

Ein Coding-Agent (Claude Code, Aider, Cursor) kann heute:

| Aufgabe | Machbarkeit | Begründung |
|---|---|---|
| `requirements.txt` schreiben | ✅ vollständig | deterministisch aus Code ableitbar |
| Implementierung bestehender Stubs (klare Specs) | ✅ vollständig | `COMP_DIARY.md`, `COMP_LANGUAGE.md` sind präzise genug |
| LangGraph-Nodes nach vorgegebener Struktur füllen | ✅ vollständig | TypedDicts + Node-Übersichten sind Spezifikation |
| Anki-Integration, REST-Calls | ✅ vollständig | reine API-Calls, keine Logik-Entscheidungen |
| `bot.py` Grundgerüst mit ConversationHandler | ✅ mit Review | Struktur klar, Telegram-API dokumentiert |
| Story-Lab-ConversationHandler | ⚠️ mit Review | Zustandsmaschine komplex, Feedback-Texte brauchen Tuning |
| StyleProfile-Aggregationslogik | ✅ vollständig | reines Python, Algorithmus in §8.4 COMP_DIARY spezifiziert |
| Meta-Agent der Services *erfindet* | ❌ nicht heute | emergentes Verhalten, keine Spec vorhanden |
| Code-schreibender Agent in Produktion | ❌ nicht empfohlen | Guardrails fehlen, Testinfrastruktur fehlt |

**Grenzen 2026:** Coding-Agenten scheitern an unklaren Spezifikationen, emergenter Systemlogik und Aufgaben wo "korrekt" nur durch echten Nutzungstest messbar ist (Feedback-Qualität, UX-Entscheidungen). Sie sind stark bei gut spezifizierten, isolierten Modulen.

### 1.2 Gut geeignete Teile dieses Repos

```
agents/extractors/        ← bereits fertig, gutes Modell für Agenten
agents/lint_agent.py      ← SCHEMA.md §8 ist vollständige Spezifikation
agents/language_agent.py  ← COMP_LANGUAGE.md Nodes vollständig beschrieben
agents/diary_agent.py     ← COMP_DIARY.md Nodes vollständig beschrieben (bis auf Story-Lab-Texte)
Anki-Integration          ← AnkiConnect REST, pure functions
requirements.txt          ← deterministisch
```

### 1.3 Schlecht geeignete Teile

```
bot.py ConversationHandler  ← UX-Entscheidungen, viele Sonderfälle
Story-Lab-Feedback-Texte    ← Coaching-Qualität nicht spec-bar
graph_context Match          ← Keyword-Gewichtung, emergentes Tuning nötig
Meta-Routine (Service-Erfindung) ← keine Spezifikation für das Ergebnis
Scoring-Kalibrierung        ← "story_score: 7" korrekt? Nur durch echten Test
```

### 1.4 Empfohlenes Workflow-Modell

```
Spezifikation (Mensch) → Stub-Generierung (Agent) → Node-Implementierung (Agent)
    → Review + Tests (Mensch) → Integration (Agent mit Supervision)
```

**Nicht:** Vollautonomer Agent der das gesamte System baut.  
**Ja:** Agent implementiert ein Modul auf Basis einer klaren COMP_*.md-Spezifikation, Mensch reviewt.

**Konkreter Einsatz für Services:** Agent kann `ServiceConversationHandler` und alle Service-Nodes implementieren, sobald dieses COMP_SERVICES.md ausreichend spezifiziert ist. Das Meta-Routing (Service-Erfindung) bleibt beim Menschen bis die Infrastruktur steht.

---

## 2. Neue Entitäten (F1)

### 2.1 `ServiceDefinition`

> Beschreibt einen Service-Typ formal — was er braucht, was er tut, wie er gemessen wird. Lebt in `wiki/personal/services/sd_[slug].md`.

**Dateiname:** `sd_[slug].md` (z.B. `sd_crypto-erklaerung.md`)

```yaml
---
type: ServiceDefinition
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: proposed | active | paused | archived
tags: []
sources: []
related: []

# Service-Identität
name: "Krypto-Erklärung"
slug: crypto-erklaerung
description: "Nutzer erklärt ein Candlestick-Muster per Sprachnachricht — StyleProfile-Eintrag für Erklär-Stil unter Fachkontext."

# Graph-Voraussetzungen (Meta-Agent prüft diese)
graph_prerequisites:
  - type: PersonalFact
    min_count: 3
    required_tags: [krypto, trading]
  - type: Concept
    min_count: 1
    required_tags: [krypto]

# Trigger-Konfiguration
trigger: scheduled          # scheduled | user-request | graph-threshold
schedule: "weekly_random"   # täglich | weekly_random | on-demand
schedule_days: [Mo, Do]

# Input/Output
input_type: voice           # voice | text | image+voice | none
output_type: style_enrichment  # style_enrichment | personal_fact | vocab_entry | none
style_context_key: "krypto_erklaerung"   # Schlüssel im StyleProfile.context_profiles

# Kosten-Schätzung
llm_calls_per_execution:
  whisper: 1        # lokal, kostenlos
  haiku: 0
  sonnet: 1         # Transkript-Qualitätsanalyse (V1: text-only — ENT-024)
  estimated_cost_usd: 0.01

# Konversations-Flow
conversation_config:
  states: [INTRO, STIMULUS_PRESENT, AWAIT_VOICE, ANALYSIS, FEEDBACK]
  intro_message: "Service: Krypto-Erklärung. Du siehst gleich ein Chart-Muster — erkläre es laut."
  stimulus_type: image        # image | text | fact | none
  stimulus_source: "raw/assets/crypto_charts/"
  await_prompt: "Erkläre das Muster — 30–60 Sekunden."
  analysis_type: style_fingerprint   # style_fingerprint | story_lab | vocab | language_quality
  feedback_type: timing_transcript_quality
---

# Service: Krypto-Erklärung

## Zweck
[Beschreibung]

## Graph-Zutaten
[Welche Pages werden als Kontext geladen]

## StyleProfile-Dimension
[Was wird gemessen, das Diary/Language nicht sieht]

## Offene Fragen
[Noch nicht entschieden]
```

### 2.2 `ServiceInstance`

> Eine konkrete Ausführung eines Services. Lebt in `raw/events/` als JSON — ähnlich RawEvent, aber service-spezifisch. Wird nach der Verarbeitung in `practice_log` des aktiven StyleProfile-Kontexts referenziert.

```json
{
  "type": "ServiceInstance",
  "timestamp": "2026-04-18T14:32:00",
  "source": "telegram",
  "service_slug": "crypto-erklaerung",
  "triggered_by": "scheduled",
  "graph_context_refs": [
    "wiki/concepts/con_trading-muster.md",
    "wiki/personal/facts/pf_2026-03-10_erste-chart-analyse.md"
  ],
  "stimulus_path": "raw/assets/crypto_charts/double_top.png",
  "audio_path": "raw/assets/2026-04-18T14-32-00_voice.ogg",
  "transcript": "[Whisper-Transkript]",
  "timing": {},
  "transcript_quality": {},
  "style_context_key": "krypto_erklaerung",
  "feedback_sent": true,
  "processed": true
}
```

### 2.3 Erweiterung: `StyleProfile.context_profiles`

Das bestehende StyleProfile-Schema (SCHEMA.md §3.6 + COMP_DIARY §8.4) erhält ein optionales Feld:

```yaml
# Ergänzung in sp_[name].md Frontmatter (additive — bestehende Felder bleiben unverändert)
context_profiles:
  krypto_erklaerung:
    avg_words_per_second: 2.8
    avg_pause_before_punchline: 0.9
    sample_count: 4
    confidence: 0.60
    style_tags: [fachsprache, direkt, schnell]
  smalltalk:
    avg_words_per_second: 2.1
    avg_pause_before_punchline: 1.8
    sample_count: 7
    confidence: 0.85
    style_tags: [locker, selbstironie]
```

**Warum dieses Schema statt neuer StyleFingerprint-Dimensionen:**
- Additive zur bestehenden Struktur — keine Migration nötig
- Bestehende StyleProfiles bleiben valide
- Context-Profile entstehen inkrementell aus practice_log-Einträgen
- Ermöglicht direkte Vergleiche: *"Beim Krypto-Erklären bist du 33% schneller als beim Smalltalk"*

---

## 3. Meta-Routine Architektur (F2)

### 3.1 Optionen-Analyse

| Option | Beschreibung | Machbarkeit heute | Risiken | Wartbarkeit |
|---|---|---|---|---|
| **A — Agent schreibt Code** | Meta-Agent generiert Python-Code für neue Services | ❌ nicht empfohlen | Code in Produktion ohne Tests, Sicherheitsrisiken, keine Guardrails vorhanden | niedrig |
| **B — Template-Instanziierung** | Meta-Agent füllt ServiceDefinition-Template mit Graph-abgeleiteten Parametern | ✅ empfohlen | Begrenzt auf vordefinierte Konversations-Flows | hoch |
| **C — Nur ServiceDefinition** | Meta-Agent erstellt nur Dokumentation, Mensch implementiert | ✅ als Fallback | Kein autonomes Wachstum, aber kein Risiko | sehr hoch |

**Entscheidung: Option B als Primärstrategie, Option C als Fallback für ungewöhnliche Services.**

### 3.2 Meta-Routine Flow (Option B)

```
[Wöchentlich, systemgetriggert]
    │
    ▼
Meta-Agent liest user_profile.md Interessen-Cluster
    │
    ├─ Cluster-Scan: Gibt es ein Interesse mit ≥5 Facts/Concepts UND kein aktiver Service?
    │
    │  Nein → Ende
    │  Ja ↓
    │
    ▼
Graph-Context-Match: Lade relevante Seiten für diesen Cluster
    │
    ▼
Service-Generator: Fülle ServiceDefinition-Template
    │
    ├─ Wähle conversation_config aus Bibliothek passender Vorlagen
    │   (aktuell: style_fingerprint, story_lab, vocab, language_quality)
    ├─ Befülle graph_prerequisites aus Cluster-Daten
    ├─ Wähle style_context_key: "[cluster_name]_[service_type]"
    ├─ Schätze llm_calls_per_execution
    │
    ▼
ServiceDefinition-Wiki-Seite schreiben (status: proposed)
    │
    ▼
Supervisor → Telegram-Nachricht an Nutzer:
    ┌──────────────────────────────────────────────────────┐
    │  🧩 Neuer Service-Vorschlag                          │
    │                                                      │
    │  Dein Graph enthält 6 Krypto-Facts + 2 Concepts.    │
    │  Idee: "Krypto-Erklärung" — erkläre Chart-Muster    │
    │  per Sprachnachricht, 1x/Woche.                      │
    │                                                      │
    │  StyleProfile-Dimension: Erklär-Stil unter           │
    │  Fachkontext (bisher nicht messbar)                  │
    │  Kosten: ~$0.01 pro Ausführung                       │
    │                                                      │
    │  [Aktivieren]  [Ablehnen]  [Details]                 │
    └──────────────────────────────────────────────────────┘
    │
    ├─ [Ablehnen] → ServiceDefinition: status: archived
    │
    └─ [Aktivieren] → ServiceDefinition: status: active
                   → Scheduler registriert neuen Trigger
```

### 3.3 Service-Generator-Prompt (Meta-Agent)

```
Du schlägst einen neuen Service für ein Personal-Knowledge-OS vor.

Nutzer-Profil:
{user_profile}

Graph-Cluster:
{cluster_data}   # Top-Facts und Concepts für dieses Thema

Bestehende aktive Services:
{active_services}   # Vermeide Duplikate

Verfügbare conversation_config Templates:
- style_fingerprint: Nutzer spricht, wird auf Timing + Ton analysiert → context_profile
- story_lab:         Nutzer übt eine Geschichte aus dem Graph
- vocab:             Nutzer beantwortet Vokabel-Challenge aus Graph-Kontext
- language_quality:  Nutzer spricht auf Zielsprache, Fokus auf Korrektheit

Regeln:
- Kosten: max 1 Sonnet-Call pro Ausführung
- Friction: max 2 Minuten Setup für Nutzer
- Wert: muss StyleProfile in Dimension bereichern, die Diary/Language nicht abdeckt
- Nur Stimulus-Quellen aus raw/ oder kuratierter Liste — keine externen APIs

Antworte im ServiceDefinition-YAML-Format.
```

### 3.4 Service-Lifecycle

```
proposed → [Nutzer bestätigt] → active → [Nutzer pausiert] → paused → [reaktiviert] → active
                                                                      [archiviert]  → archived
```

**Automatische Archivierung:** Wenn der Graph-Cluster unter den `graph_prerequisites` Min-Threshold fällt und 30 Tage kein Service ausgeführt wurde.

**Max. aktive Services: 5.** Lint-Agent warnt bei Überschreitung und schlägt Priorisierung vor.

---

## 4. StyleProfile-Verbindung (F3)

### 4.1 Mechanismus: Kontextueller Benchmark (empfohlen)

Services schreiben keinen neuen StyleFingerprint im alten Sinn — sie erzeugen **context-tagged Aggregationen** im StyleProfile.

**Schritt 1 — Service-Antwort analysieren:**
Identisch zur Story-Lab Voice-Analyse (COMP_DIARY §6.5): Whisper-Transkript + Claude Sonnet Text-Analyse (V1: kein Audio-Input — ENT-024).

**Schritt 2 — In practice_log schreiben:**
```yaml
# Ergänzung practice_log in aktivem PersonalFact oder als standalone ServiceInstance
- date: 2026-04-18
  type: service_execution
  service_slug: crypto-erklaerung
  style_context_key: krypto_erklaerung
  timing_wps: 2.8
  pause_before_punchline: 0.9
  transcript_quality: {struktur: 4, klarheit: 3, ueberzeugung: 4}   # V1: text-only (ENT-024)
  style_profile_ref: "[[sp_chappelle]]"
```

**Schritt 3 — StyleProfile.context_profiles aggregieren:**
```python
def update_context_profile(
    style_profile: StyleProfile,
    context_key: str,
    new_instance: ServiceInstance,
) -> StyleProfile:
    """Fügt neuen Service-Datenpunkt zum context_profile hinzu."""
    existing = style_profile.context_profiles.get(context_key, {
        "sample_count": 0, "avg_words_per_second": None, ...
    })
    # Inkrementelles Mittel-Update
    n = existing["sample_count"] + 1
    new_avg_wps = _incremental_mean(
        existing["avg_words_per_second"], new_instance.timing["wps"], n
    )
    confidence = CONFIDENCE_THRESHOLDS.get(min(n, 8), 1.0)
    
    return {**style_profile, "context_profiles": {
        **style_profile.context_profiles,
        context_key: {
            "avg_words_per_second": new_avg_wps,
            "sample_count": n,
            "confidence": confidence,
            "style_tags": _majority_tags_from_instances(context_key),
        }
    }}
```

### 4.2 Feedback-Nutzung der context_profiles

```
Vergleich:
  Dein Storytelling-Stil: 2.1 WPS, 1.8s Pause → confident, locker
  Dein Krypto-Erklär-Stil: 2.8 WPS, 0.9s Pause → schneller, weniger Pausen

  → Du erklärst Fachthemen anders als du Geschichten erzählst.
    Tipp: Bau Pausen ein — auch im Fachkontext zieht das mehr.
```

### 4.3 Warum nicht die anderen Mechanismen

**Neuer style_tag:** Zu grob. "krypto-erklaerung" als Tag sagt nichts über Timing-Delta.

**Neue StyleFingerprint-Dimension:** Bricht das Schema. Alle bestehenden StyleProfiles müssen migriert werden. Wartungsaufwand > Nutzen für diesen Einsatz.

---

## 5. Session-Management (F5)

### 5.1 Entscheidung: Option B — Generischer ServiceConversationHandler

```python
class ServiceConversationHandler:
    """
    Universeller ConversationHandler der eine ServiceDefinition als Config erhält.
    Ersetzt individuelle Handler pro Service.
    """
    
    def __init__(self, service_def: ServiceDefinition):
        self.service_def = service_def
        self.config = service_def.conversation_config
    
    async def handle_intro(self, update, context) -> int:
        """INTRO → STIMULUS_PRESENT oder AWAIT_VOICE."""
        await update.message.reply_text(self.config["intro_message"])
        if self.config.get("stimulus_type"):
            await self._send_stimulus(update, context)
            return AWAIT_VOICE
        return AWAIT_VOICE
    
    async def handle_voice(self, update, context) -> int:
        """AWAIT_VOICE → ANALYSIS."""
        # speichert Voice in raw/assets/, sendet "⏳ Analysiere..."
        voice_path = await _save_voice(update)
        context.user_data["voice_path"] = voice_path
        await update.message.reply_text("⏳ Analysiere...")
        return ANALYSIS
    
    async def handle_analysis(self, update, context) -> int:
        """ANALYSIS → FEEDBACK."""
        analysis_type = self.config["analysis_type"]
        feedback = await _run_analysis(
            analysis_type,
            context.user_data["voice_path"],
            self.service_def,
        )
        await update.message.reply_text(feedback)
        return ConversationHandler.END
    
    def build_handler(self) -> ConversationHandler:
        """Erstellt den python-telegram-bot ConversationHandler."""
        states = {
            INTRO:    [MessageHandler(filters.TEXT, self.handle_intro)],
            AWAIT_VOICE: [MessageHandler(filters.VOICE, self.handle_voice)],
            ANALYSIS: [CallbackQueryHandler(self.handle_analysis)],
        }
        return ConversationHandler(
            entry_points=[CommandHandler(self.service_def.slug, self.handle_intro)],
            states=states,
            fallbacks=[CommandHandler("cancel", cancel)],
        )
```

**Registrierung bei Service-Aktivierung:**
```python
# bot.py
def register_service(app: Application, service_def: ServiceDefinition) -> None:
    handler = ServiceConversationHandler(service_def)
    app.add_handler(handler.build_handler())
    app.add_handler(CommandHandler(service_def.slug, handler.handle_intro))
```

### 5.2 Warum nicht Option A/C

**Option A** (eigener Handler): 10 Services = 10 fast-identische Handler. Bugfixes müssen 10× gepflegt werden. Nicht skalierbar.

**Option C** (Telegram Mini App): Upgrade-Pfad wenn Ebene-2-UI nicht reicht. Heute nicht nötig.

---

## 6. Service-Lifecycle-Logik (F6)

### 6.1 Schwellwert für Service-Vorschlag

```python
SERVICE_PROPOSAL_THRESHOLD = {
    "min_facts_with_tag": 5,       # mindestens 5 PersonalFacts mit dem Cluster-Tag
    "min_cluster_confidence": 0.6, # Cluster-Konfidenz in user_profile.md Interessen
    "no_existing_service": True,   # kein aktiver Service für diesen Cluster
    "max_active_services": 5,      # keine neuen Vorschläge wenn Limit erreicht
}
```

### 6.2 Anti-Explosion-Mechanismen

1. **Max 5 aktive Services** — Lint-Agent warnt bei Versuch #6
2. **Nutzer-Bestätigung immer erforderlich** — Meta-Agent kann nie auto-aktivieren
3. **Cooling-Off:** Ein abgelehnter Service-Vorschlag für denselben Cluster frühestens nach 90 Tagen erneut vorschlagen
4. **Qualitäts-Gate im Meta-Agent-Prompt:** Service muss explizit eine Dimension abdecken die weder Diary noch Language abdeckt

### 6.3 Automatische Inaktivierung

```python
def check_service_health(service_def: ServiceDefinition, graph: Graph) -> str:
    """Gibt empfohlenen neuen Status zurück."""
    # Prüft ob graph_prerequisites noch erfüllt
    for prereq in service_def.graph_prerequisites:
        pages = graph.search(type=prereq["type"], tags=prereq["required_tags"])
        if len(pages) < prereq["min_count"]:
            return "archived"   # Graph-Basis weggefallen
    
    # Prüft Nutzungsfrequenz
    instances = _get_recent_instances(service_def.slug, days=30)
    if len(instances) == 0 and service_def.status == "active":
        return "paused"   # Inaktivitäts-Signal, aber kein Auto-Archiv
    
    return service_def.status
```

---

## 7. Service-Katalog (Version 1)

### 7.1 Bestehende Beispiele — Bewertung

#### Crypto-Service ✅ architektur-tauglich mit Anpassungen

| Frage | Entscheidung |
|---|---|
| Chart-Bilder: woher? | 20–30 kuratierte Pattern-PNGs in `raw/assets/crypto_charts/` — keine externe API nötig, manuell befüllt |
| "Krypto-Sprache" als Dimension? | → `context_profiles["krypto_erklaerung"]` — nicht neue Felder, sondern context-key |
| Erklärqualität: Timing oder Inhalt? | Nur Timing + Ton — inhaltliche Korrektheit erfordert Domänen-Wissen-Validierung die das System nicht hat |

**Angepasster ServiceDefinition-Kern:**
- `conversation_config.stimulus_type: image` (Candlestick-Chart aus `raw/assets/`)
- `analysis_type: style_fingerprint` (Timing + Ton, kein Story-Lab)
- `style_context_key: "krypto_erklaerung"`

#### Movie-Service ⚠️ bedingt tauglich

**Problem 1:** Setzt voraus dass der Graph bereits 5+ CulturalEntries zu Filmen hat. Vor dem Bootstrap wenig relevant.

**Problem 2:** "Zitat-Erkennung" als Spiel ist gut — aber woher kommen kuratierte Zitate? Manuelle Liste nötig (20-30 Zitate aus Filmen die im Graph sind). Keine externen APIs.

**Anpassung:** Service erst aktivierbar wenn Graph-Threshold (5 Film-CulturalEntries) erfüllt. Zitat-Liste manuell in `raw/assets/movie_quotes.json` kurieren.

**Entscheidung:** Zweiter Service nach Crypto, wenn Film-Interesse im Graph messbar ist.

#### Sprach-Service (Konversations-Simulation) ✅ eigenständiger Service

**Ist es eine Language-Agent-Extension oder eigenständiger Service?**

Eigenständiger Service. Begründung:
- Language-Agent verarbeitet Inputs (ingest) — er analysiert was der Nutzer gesendet hat
- Der Sprach-Service **generiert Situationen** die der Nutzer dann beantwortet
- Der Konversations-Flow (mehrere Turns, Szenario-Aufbau) passt in ServiceConversationHandler
- Die Analyse-Pipeline (Whisper + Sonnet Audio) kann aus Diary/Language wiederverwendet werden

**conversation_config-Besonderheit:** `analysis_type: language_quality` (Fokus auf Sprachkorrektheit, nicht Storytelling-Timing — analog COMP_LANGUAGE §7.4).

### 7.2 Neue Service-Vorschläge

#### Service 4: Tech-Opinion-Service ✅

**Graph-Basis:** Concepts zu KI/Tech (z.B. `con_llm-development.md`, `con_coding-tools.md`)

**Was es tut:** Bot präsentiert eine Debatte-These aus dem Graph ("LLMs werden Programmierer ersetzen") → Nutzer gibt 45-Sek-Meinung auf Deutsch → Voice-Analyse.

**Neue StyleProfile-Dimension:** `"tech_debate"` — Argumentations-Stil bei Fachthemen. Diary sieht nie strukturierte Tech-Debatte-Situationen.

**graph_prerequisites:**
```yaml
- type: Concept
  min_count: 3
  required_tags: [KI, tech, software]
```

**stimulus_source:** Die These kommt aus den Concepts selbst (open_questions-Feld). Kein externes Material nötig.

**Kosten:** 1 Sonnet/Ausführung. Sehr effizient.

---

#### Service 5: Musik-Kontext-Service ✅

**Graph-Basis:** CulturalEntries zu Musikern/Genres oder PersonalFacts mit Musik-Tag.

**Was es tut:** Bot wählt Künstler/Genre aus Graph → fragt Nutzer nach emotionaler Reaktion auf Spanisch (30 Sek) → Language-Quality-Analyse.

**Neue Dimensionen:**
- `style_context_key: "musik_emotion_es"` — emotionale Sprach-Reaktion auf Spanisch, spontan
- Verknüpft Musik-Interesse mit Spanisch-Lernen auf natürliche Weise

**graph_prerequisites:**
```yaml
- type: CulturalEntry
  min_count: 3
  required_tags: [musik, artist]
```

**Besonderheit:** `analysis_type: language_quality` (Spanisch-Fokus). Feedback via Language Agent (analog COMP_LANGUAGE §7.4).

---

#### Service 6: CS2-Debrief-Service ✅

**Graph-Basis:** PersonalFacts über Gaming-Sessions oder Esport-Concepts.

**Was es tut:** Bot fragt nach einer konkreten Entscheidung aus einer Gaming-Session ("Erkläre die wichtigste taktische Entscheidung in unter 1 Minute") → Timing-Analyse.

**Neue StyleProfile-Dimension:** `"tactical_narration"` — Narrations-Präzision unter kognitivem Druck. Einzig dieser Service erzeugt Daten für "schnelle, präzise Erklärung unter Zeitdruck".

**graph_prerequisites:**
```yaml
- type: PersonalFact
  min_count: 3
  required_tags: [gaming, CS2, esport]
```

**Stimulus:** Kein externes Material — die PersonalFacts aus dem Graph sind der Kontext. Bot fragt: "Letzte Session: [Fact-Titel]. Erkläre die wichtigste Entscheidung."

---

#### Service 7: Foto-Caption-Service ✅

**Graph-Basis:** Eigene Fotos in `raw/assets/` (Nutzer-Fotos via Telegram gesendet).

**Was es tut:** Bot wählt ein eigenes Foto aus dem Graph → Nutzer beschreibt es spontan auf Spanisch (20 Sek).

**Neue Dimension:** `"visual_description_es"` — Spontane Beschreibungssprache auf Spanisch. Impuls `image_react` ist ähnlich, aber mit fremdem GIF. Eigene Fotos aktivieren persönlicheren, reicheren Sprach-Kontext.

**graph_prerequisites:**
```yaml
- type: RawEvent
  min_count: 5
  source_type: telegram_image
```

**Achtung:** Nur wenn Nutzer tatsächlich Fotos via Telegram schickt. Low-priority bis Foto-Ingest-Muster erkennbar ist.

---

#### Service 8: Gesundheits-Reflexions-Service ✅

**Graph-Basis:** PersonalFacts mit Gesundheits-Tags (Sport, Schlaf, Ernährung, mentale Gesundheit).

**Was es tut:** Bot greift einen Gesundheits-Moment aus dem Graph → fragt nach Reflexion: "Was würdest du heute anders machen?" (45 Sek, Deutsch).

**Neue Dimension:** `"personal_reflection"` — Selbstreflexions-Stil bei persönlichem/emotionalem Kontext. Andere Sprach-Muster als Tech oder Krypto. Führt zu `context_profiles`-Vergleich der aufzeigt ob persönliche Themen den Stil fundamentally ändern.

**Sensitivitäts-Hinweis:** Gesundheits-Facts können `sensitivity: private` haben. Service-Config muss prüfen:
```yaml
sensitivity_filter: "public_only"   # oder "public_and_sensitive"
```

---

### 7.3 Service-Prioritäts-Reihenfolge (Empfehlung)

| Prio | Service | Begründung |
|---|---|---|
| 1 | Crypto-Service | Nutzer-Interesse stark, Chart-Stimuli einfach kurierbar, klarer StyleProfile-Mehrwert |
| 2 | Tech-Opinion-Service | Graph-Basis sofort vorhanden (Concepts), kein externes Material |
| 3 | Sprach-Service | Erweitert Language-Modul, Spanisch-Lern-Synergy |
| 4 | CS2-Debrief | Einzigartiger Stil-Kontext, aber setzt Gaming-Facts im Graph voraus |
| 5 | Musik-Service | Gut, aber wartet auf Musik-CulturalEntries |
| 6 | Foto-Service | Wartet auf Foto-Ingest-Verhalten |
| 7 | Gesundheits-Service | Wertvoll aber Sensitivitäts-Handling komplex |
| 8 | Movie-Service | Wartet auf Film-CulturalEntries + manuelle Zitat-Liste |

---

## 8. Offene Technische Fragen

### 8.1 Wer deployt neue Services?

Bei Option B (Template-Instanziierung): Der Meta-Agent schreibt nur die ServiceDefinition-Datei. Der `ServiceConversationHandler` wird von `bot.py` beim Start geladen — alle ServiceDefinitions mit `status: active` werden automatisch registriert:

```python
# bot.py startup
for service_def in load_all_services(status="active"):
    register_service(app, service_def)
```

Kein Code-Deployment nötig. Neue Services aktivieren sich beim nächsten Bot-Neustart.

### 8.2 Dokumentation der Services

`COMP_SERVICES.md` ist ein statisches Dokument für die Architektur. Die tatsächlich aktiven Services leben als `ServiceDefinition`-Seiten im Graph (`wiki/personal/services/`). Der Lint-Agent pflegt `index.md` automatisch.

`COMP_SERVICES.md` wird **nicht** dynamisch erweitert — es beschreibt das System, nicht den Inhalt.

### 8.3 Service-Logs

**Entscheidung:** ServiceInstances leben in `raw/events/` (wie RawEvents). Kein separates Service-Log.

Das bestehende `log.md` erhält einen neuen Eintrag-Typ:
```
## [2026-04-18T14:32] service | crypto-erklaerung | timing: 2.8 WPS | style_context: krypto_erklaerung
```

### 8.4 Rückwärtskompatibilität bei Schema-Erweiterungen

`context_profiles` ist ein optionales Feld. Bestehende StyleProfiles ohne dieses Feld sind vollständig valide. Der Aggregations-Code prüft immer:
```python
context_profiles = style_profile.get("context_profiles", {})
```

Migration für bestehende StyleProfiles: keine nötig. Das Feld entsteht erst beim ersten Service-Datenpunkt.

### 8.5 Kosten-Kontrolle

| Szenario | Kosten/Monat |
|---|---|
| 1 aktiver Service, 2x/Woche | ~$0.08 |
| 3 aktive Services, 2x/Woche je | ~$0.24 |
| 5 aktive Services, täglich je | ~$1.50 |
| 5 aktive Services + normale Pipeline | ~$4–6 gesamt |

Budget $5–10/Monat: 5 aktive Services täglich ist das Maximum. In der Praxis (2x/Woche je Service) bleibt der Service-Overhead unter $0.50/Monat.

**Mechanismus:** `llm_calls_per_execution` in ServiceDefinition ist Pflichtfeld. Lint-Agent summiert monatliche Service-Kosten und warnt bei >$2/Monat aus Services allein.

---

## 9. Kritische Risiken

### Risiko 1: Komplexitäts-Explosion ohne generischen Handler

**Was kann schiefgehen:** Ohne `ServiceConversationHandler` (Option B für F5) entsteht für jeden Service ein eigener ~150-Zeilen-Handler in `bot.py`. Bei 5 Services = 750 Zeilen fast-identischer Code. Bugfixes müssen 5× gepflegt werden.

**Konsequenz:** Unbeherrschbarer Bot-Code, jeder neue Service kostet überproportional viel Entwicklungszeit.

**Mitigation:** Generischer Handler **muss vor dem ersten Service** implementiert sein. Kein Service ohne ihn.

---

### Risiko 2: Graph-Content-Dependency-Loop

**Was kann schiefgehen:** Die Meta-Routine setzt voraus dass der Graph reich genug ist um Services zu generieren. Wenn der Nutzer den Graphen nicht regelmäßig befüllt (Bootstrap nicht abgeschlossen, keine täglichen Inputs), bleibt die Meta-Routine dauerhaft leer.

**Konsequenz:** Das "selbsterweiternde System" erweitert sich nie. Services könnten als erste manuell angelegt werden bevor die Meta-Routine existiert — aber dann ist der Mehrwert des Meta-Routings weg.

**Mitigation:** Bootstrap **muss abgeschlossen** sein bevor Meta-Routine aktiviert wird (`bootstrap_complete: true`). Erste 2-3 Services manuell anlegen um den Wert zu beweisen, bevor Meta-Routing implementiert wird.

---

### Risiko 3: Audio-Analyse-Kosten skalieren mit Services

**Was kann schiefgehen:** Jede Service-Antwort = 1 Sonnet-Call. Bei 3 Services × täglich = 90 Sonnet-Calls/Monat ≈ $0.90 nur für Service-Audio. Kombiniert mit normalem Pipeline-Betrieb kann das $8-10 Budget überschreiten wenn der Nutzer viele Voice-Inputs sendet.

**Konsequenz:** Budgetüberschreitung, System wird eingeschränkt.

**Mitigation:**
1. Lint-Agent überwacht monatliche Kosten-Schätzung
2. Service-Frequenz (schedule) als erster Hebel: 2x/Woche statt täglich halbiert Kosten
3. Optional: Haiku statt Sonnet für Ton-Analyse bei niedriger-Prio-Services (Qualitätsverlust akzeptierbar?)

---

## 10. Empfehlung: Nächste konkrete Schritte

### Der kleinste sinnvolle erste Schritt (Pareto: 20% Aufwand, 80% Nutzen)

**Schritt 1 — ServiceDefinition-Entität in SCHEMA.md einführen (2h)**
Ergänze SCHEMA.md §3 um ServiceDefinition und §6 um `context_profiles` in StyleProfile. Erstelle `templates/sd_template.md`. Dieser Schritt kostet minimal und etabliert den Schema-Vertrag für alles Folgende.

**Schritt 2 — Crypto-Service manuell implementieren, ohne Meta-Routing (1–2 Tage)**

```
agents/services/
    base_service.py          ← ServiceConversationHandler (generisch)
    crypto_service.py        ← ServiceDefinition-Instanz (hardkodiert für Test)

wiki/personal/services/
    sd_crypto-erklaerung.md  ← erste ServiceDefinition-Seite

raw/assets/crypto_charts/
    *.png                    ← 15–20 kuratierte Candlestick-Patterns
```

Der `ServiceConversationHandler` wird nicht für den Crypto-Service gebaut — er wird für **alle zukünftigen Services** gebaut. Der Crypto-Service ist nur der erste Testfall.

**Was dieser Schritt liefert:**
- Einen nützlichen Service der das StyleProfile in einer neuen Dimension anreichert
- Den generischen `ServiceConversationHandler` als Infrastruktur (alle weiteren Services kosten ~1h Konfiguration)
- Die erste `ServiceDefinition`-Seite als Schema-Beispiel für den Meta-Agenten
- Reales Feedback ob der generische Handler-Ansatz tragfähig ist

**Was dieser Schritt NICHT braucht:**
- Meta-Routine (Service-Generierung)
- Komplexe Graph-Threshold-Logik
- Neue LangGraph-Nodes im Haupt-Workflow

**Schritt 3 — Tech-Opinion-Service hinzufügen (2–3h nach Schritt 2)**
Zweiter Service der beweist: generischer Handler funktioniert, neue ServiceDefinition = minimaler Aufwand. Kein neues Material nötig — Concepts aus dem Graph sind der Stimulus.

Nach Schritt 3 ist die Services-Infrastruktur bewiesen. Erst dann lohnt sich die Meta-Routine.

---

## 11. Offene Fragen (Backlog)

- [ ] **Stimulus-Bibliothek:** Kuratierte Candlestick-Charts (Crypto-Service) — wie viele? Statisch oder rotierend?
- [ ] **Service-Index in index.md:** Eigene Sektion `## ServiceDefinitions (N)` oder in Concepts-Sektion?
- [ ] **`sensitivity_filter` in ServiceDefinition:** Wenn Service Gesundheits-Facts lädt — Haiku-Analyse ok oder Ollama-Pflicht?
- [ ] **Mehrsprachige Services:** Spanisch-Impuls-Analyse via Language Agent (§7.4 COMP_LANGUAGE) wiederverwendbar oder neuer Analyse-Pfad?
- [ ] **Service-Pause via Telegram:** `/service pause [slug]` oder globales `/services` Dashboard?
- [ ] **context_profiles Lint:** Wann ist ein context_profile "gut genug" für aussagekräftige Vergleiche? (Min. 5 Samples → confidence: 0.85 analog StyleProfile-Logik?)
