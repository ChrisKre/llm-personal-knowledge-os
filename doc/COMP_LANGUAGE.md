# COMP_LANGUAGE.md — Language Module
> Version: 0.1 | Datum: 2026-04-18 | Status: DRAFT

---

## 0. Modul-Überblick

Das Language Module ist das **Sprachlern-Gedächtnis** des Systems. Es verwaltet Vokabeln, Grammatik-Konzepte, kulturelle Ankerpunkte und die Brücken zwischen Sprachen — alles im Kontext der echten Erlebnisse des Nutzers.

### Zweck

```
Sprachkontakt → VocabEntry mit persönlichem Kontext → Anki-Karte → geübtes Wissen
             → LanguageBridge → Konzeptlücken sichtbar machen
             → CulturalEntry → Bedeutungsraum des Wortes verstehen
```

Das Modul arbeitet in vier Betriebsmodi:

| Modus          | Trigger                                   | Was passiert                                                 |
|----------------|-------------------------------------------|--------------------------------------------------------------|
| **Ingest**     | Neuer Telegram-Input mit Sprachbezug      | VocabEntry / CulturalEntry erstellen, Bridges erkennen       |
| **Enrichment** | Lint-Trigger oder Nutzer-Anfrage          | Bestehende Einträge mit Graph-Kontext anreichern             |
| **Anki-Sync**  | Nach Elaboration oder Lint-Anki-Lücke     | Karte in Anki erstellen/aktualisieren via AnkiConnect        |
| **Push**       | Täglich, zufällige Zeit                   | Vokabel-Challenge oder Empfehlung an Nutzer senden           |

### Abgrenzung

- **Language ↔ Diary Agent:** Wenn ein PersonalFact einen Sprachmoment enthält (z.B. Lehrer sagt *duende*), übergibt der Diary Agent einen VocabEntry-Task an den Language Agent. Die Grenze liegt auf dem Satz: PersonalFacts beschreiben *Erlebnisse*, VocabEntries beschreiben *Wörter*.
- **Language ↔ Lint Agent:** Der Lint-Agent erkennt VocabEntries ohne Anki-Karte und triggert den Anki-Sync. Der Language Agent führt den Export aus.
- **Language ↔ Diary Impuls:** Die Impuls-Typen `codemix` und `emotion_vocab` nutzen VocabEntries als Zutaten. Wenn der Nutzer antwortet, aktualisiert der Language Agent die Nutzungsstatistiken. (→ §7)

### Modell-Wahl

| Aufgabe                                  | Modell            | Begründung                                        |
|------------------------------------------|-------------------|---------------------------------------------------|
| Intent-Klassifikation: Vokabel?          | Haiku 4.5         | Günstig, reicht für Erkennung                     |
| VocabEntry erstellen (Übersetzungen, Beispiele, Eselsbrücke) | Sonnet 4.6 | Kreative Sprach-Synthese |
| LanguageBridge Erkennung + Insight       | Sonnet 4.6        | Nuanciertes Sprach-Reasoning                      |
| CulturalEntry erstellen                  | Sonnet 4.6        | Kultureller Kontext erfordert gutes Reasoning     |
| Vocab-Empfehlung (welches Wort passt?)   | Haiku 4.5         | Keyword-Matching gegen Graph, günstig             |
| Anki-Karten-Template befüllen            | Haiku 4.5         | Template-basiert, kein deep reasoning nötig       |
| user_language_profile.md aktualisieren  | Haiku 4.5         | Statistik-Update, kein LLM nötig                 |

**Privacy:** Sprachbezogene Inhalte sind in der Regel `public` oder `sensitive`, nie `private`. Das Sensitivity-Tier-Modell aus SCHEMA.md §6.3 gilt.

---

## 1. `user_language_profile.md`

### 1.1 Zweck

Die `user_language_profile.md` ist eine spezialisierte Ergänzung zu `user_profile.md`, die ausschließlich sprachliche Metriken enthält. Sie wird vom Language Agent gepflegt und vom Supervisor für Routing-Entscheidungen genutzt.

**Lebt in:** `wiki/language/user_language_profile.md`  
**Update-Frequenz:** Nach jedem Language-Agent-Ingest + wöchentlicher Neuberechnung durch Lint

### 1.2 Schema

```markdown
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Sprachprofil

## Aktive Sprachen
| Sprache | Code | Status    | Einträge | Letzte Aktivität |
|---------|------|-----------|----------|-----------------|
| Deutsch | de   | Muttersprache | —   | —               |
| Spanisch| es   | aktiv lernend | 48  | 2026-04-18      |
| Englisch| en   | aktiv lernend | 12  | 2026-04-15      |

## Input-Verteilung (letzte 30 Tage)
- de: 60% (primär)
- es: 30% (lernend — steigt)
- en: 10% (lernend — stabil)

## Input-Verteilung (letzte 90 Tage)
- de: 65%
- es: 25%
- en: 10%

## Ziel-Konfiguration
primary_learning_language: es
secondary_learning_language: en
anki_deck_es: "Spanisch :: Personal"
anki_deck_en: "Englisch :: Personal"
daily_push_language: es       # Sprache für tägliche Push-Challenges

## Schwellwerte
vocab_recommend_min_score: elaborated   # nur elaborierte Einträge empfehlen
bridge_auto_create: true                # automatisch LanguageBridges erstellen
cultural_entry_auto: true               # automatisch CulturalEntries bei neuen Orten/Personen

## Anki-Status
anki_last_sync: YYYY-MM-DD
anki_entries_es: 41
anki_entries_en: 10
anki_streak_current: 14       # Tage in Folge geübt
anki_streak_best: 21

## Statistik
total_vocab_entries: 60
bridges_created: 8
cultural_entries: 15
concept_entries: 5
```

### 1.3 Update-Logik

```python
def update_language_profile(
    wiki_root: Path,
    trigger: str,   # "ingest" | "weekly_lint" | "anki_sync"
) -> None:
    profile_path = wiki_root / "wiki/language/user_language_profile.md"
    
    if trigger == "ingest":
        # Nur Zähler inkrementieren: total_vocab_entries, bridges_created, etc.
        _increment_counters(profile_path)
        _update_last_activity(profile_path, language=current_language)
    
    elif trigger == "weekly_lint":
        # Vollständige Neuberechnung der Input-Verteilung aus raw/events/
        distribution = _calculate_language_distribution(wiki_root / "raw/events/", days=30)
        distribution_90 = _calculate_language_distribution(wiki_root / "raw/events/", days=90)
        _update_distribution(profile_path, distribution, distribution_90)
    
    elif trigger == "anki_sync":
        _update_anki_stats(profile_path)
```

---

## 2. VocabEntry-Ingest

### 2.1 Wann entsteht ein VocabEntry?

Ein VocabEntry entsteht wenn:

1. **Direkter Sprachkontakt:** Nutzer schickt ein Wort via Telegram, explizit als Vokabel markiert (`#vocab`, "was bedeutet X", "interessantes Wort: X")
2. **Impliziter Sprachkontakt im PersonalFact:** Diary Agent erkennt ein fremdsprachiges Wort das eine Rolle gespielt hat und übergibt einen VocabEntry-Task
3. **Impuls-Antwort mit Codemix:** Language Agent erkennt neue Wörter die der Nutzer in einer Impuls-Antwort verwendet hat
4. **Lint-Empfehlung:** Wort taucht mehrfach in raw/events/ auf ohne eigenen VocabEntry-Eintrag

### 2.2 Graph Context Match für Vokabeln

Bevor der VocabEntry erstellt wird, sucht der graph_reader nach:
- Bestehende VocabEntries mit ähnlichem Bedeutungsfeld (selbe Sprache + verwandte Tags)
- Bestehende LanguageBridges die das Wort betreffen könnten
- CulturalEntries aus dem kulturellen Umfeld des Wortes
- PersonalFacts die das Wort bereits enthalten (für Verbindung über `Erschienen in`)

Das Ergebnis (`graph_context`) gibt dem Language Agent den Kontext: *"Was weiß der Graph schon über diesen Bedeutungsraum?"*

### 2.3 VocabEntry-Erstellungs-Prompt

```
Du erstellst einen vollständigen VocabEntry für ein Lernwörterbuch.

Wort: {word}
Sprache: {language}
Nutzer-Kontext: {user_context}   # z.B. "Flamenco-Kurs, Lehrer hat es erwähnt"
Graph-Kontext: {graph_context}   # bestehende verwandte Seiten

Nutzer-Profil (Sprachen): {user_languages}   # z.B. ["de", "es", "en"]

Aufgabe:
1. Gib Übersetzungen in alle bekannten Sprachen des Nutzers.
2. Erstelle 3 Beispielsätze: A-Niveau, B-Niveau, C-Niveau oder idiomatisch.
3. Schreibe eine Eselsbrücke die an die Muttersprache (Deutsch) oder bekannte Konzepte
   des Nutzers anknüpft. Falls graph_context einen PersonalFact mit diesem Wort enthält:
   baue diesen Moment als Eselsbrücke ein.
4. Identifiziere Cross-Language-Bridges:
   - Kognat (ähnliches Wort, ähnliche Bedeutung in einer anderen Sprache)?
   - Faux-ami (ähnliches Wort, verschiedene Bedeutung)?
   - Concept-gap (Konzept existiert in der Zielsprache, nicht in DE/EN)?
   - Structural-parallel (ähnliche grammatische Struktur)?
5. Bestimme Schwierigkeitsgrad (CEFR A1–C2).

Antworte im Format:
translations:
  de: [Übersetzung]
  en: [Übersetzung]
  (weitere Sprachen des Nutzers)
grammar:
  type: [Nomen | Verb | Adjektiv | ...]
  gender: [el | la | — ]   # falls Nomen
  conjugation_note: [Kurzform, falls Verb]
example_sentences:
  - [A-Niveau]
  - [B-Niveau]
  - [C-Niveau]
mnemonic: [Eselsbrücke]
bridges:
  - lang: [de | en | ...]
    type: [cognate | faux-ami | concept-gap | structural-parallel]
    note: [1 Satz Erklärung]
difficulty: [A1 | A2 | B1 | B2 | C1 | C2]
tags: [kommagetrennte Tags]
```

### 2.4 Automatische LanguageBridge-Erstellung

Wenn der VocabEntry-Prompt eine Bridge identifiziert, erstellt der Language Agent sofort eine `LanguageBridge`-Seite — sofern noch keine existiert (graph_context-Prüfung).

---

## 3. Cross-Language-Bridges

### 3.1 Erkennungs-Logik

LanguageBridges werden an zwei Punkten erkannt:

**Punkt A — Bei VocabEntry-Erstellung:** Direkter Vergleich mit bekannten Sprachen des Nutzers via Prompt (§2.3).

**Punkt B — Wöchentlicher Bridge-Scan (Lint):**

```python
def weekly_bridge_scan(wiki_root: Path, user_languages: list[str]) -> list[WikiWrite]:
    """Findet Bridges zwischen bestehenden VocabEntries die noch nicht verlinkt sind."""
    vocab_pages = load_all_pages(wiki_root, type="VocabEntry")
    existing_bridges = load_all_pages(wiki_root, type="LanguageBridge")
    
    candidates = []
    for page_a in vocab_pages:
        for page_b in vocab_pages:
            if page_a == page_b or page_a.language == page_b.language:
                continue
            if _phonetic_similarity(page_a.word, page_b.word) > 0.7:   # Haiku
                if not _bridge_exists(page_a, page_b, existing_bridges):
                    candidates.append((page_a, page_b))
    
    # Sonnet prüft Kandidaten auf echte sprachliche Verbindung
    bridges = [_create_bridge(a, b) for a, b in candidates if _is_real_bridge(a, b)]
    return bridges
```

### 3.2 Bridge-Typen im Detail

| Typ                   | Beschreibung                                                         | Beispiel                           |
|-----------------------|----------------------------------------------------------------------|------------------------------------|
| `cognate`             | Ähnliches Wort, ähnliche Bedeutung in Schwestersprache               | ES *noche* ↔ FR *nuit* (Nacht)    |
| `faux-ami`            | Ähnliches Wort, verschiedene Bedeutung — Verwechslungsgefahr         | ES *embarazada* (schwanger) ≠ EN *embarrassed* |
| `concept-gap`         | Konzept existiert nur in einer Sprache, kein direktes Äquivalent     | ES *duende* → DE kein Äquivalent  |
| `structural-parallel` | Gleiche grammatische Struktur/Muster in zwei Sprachen                | ES Reflexivverben ↔ DE Reflexivverben |

### 3.3 Bridge-Erstellungs-Prompt

```
Du analysierst eine sprachliche Verbindung zwischen zwei Wörtern/Konzepten.

Wort A: {word_a} ({language_a}) — Bedeutung: {meaning_a}
Wort B: {word_b} ({language_b}) — Bedeutung: {meaning_b}
Verdacht: {bridge_type}

Aufgabe:
1. Bestätige oder korrigiere den Bridge-Typ.
2. Formuliere die lernrelevante Erkenntnis in 1-2 Sätzen:
   Was muss ein Deutschlernender/Spanischlernender hier wissen?
3. Gib ein konkretes Beispiel für den Unterschied oder die Gemeinsamkeit.

Antworte:
bridge_type: [cognate | faux-ami | concept-gap | structural-parallel]
confirmed: [true | false]
insight: [1-2 Sätze — die Kernaussage für den Lernenden]
example_contrast:
  {language_a}: [Satz]
  {language_b}: [Satz]
  comment: [Was macht den Unterschied/die Ähnlichkeit deutlich?]
```

---

## 4. CulturalEntry-Erstellung

### 4.1 Wann entsteht ein CulturalEntry?

1. **Orte:** Nutzer erwähnt einen Ort in einer Zielsprach-Region (Barcelona, México DF, Buenos Aires)
2. **Personen:** Bekannte Person aus einer Zielsprach-Kultur taucht auf (Künstler, Autor, Musiker)
3. **Events/Konzepte:** Kulturelles Ereignis oder Konzept mit starkem regionalem Bezug (Flamenco, Día de los Muertos)
4. **Sprachliche Brücke:** CulturalEntry als Kontext für ein Vokabular mit kulturellem Bedeutungsraum

Automatische Erstellung nur wenn `cultural_entry_auto: true` in `user_language_profile.md`.

### 4.2 CulturalEntry-Prompt

```
Du erstellst einen CulturalEntry für das persönliche Wissenssystem eines Nutzers.

Entität: {name}
Typ: {type}   # person | place | event | cultural-concept
Grund für Erstellung: {trigger_context}   # z.B. "Nutzer war beim Flamenco-Kurs in München"
Nutzer-Kontext aus Graph: {graph_context}
Nutzer-Interessen: {user_interests}

Aufgabe:
1. Schreibe eine prägnante Zusammenfassung (3-5 Sätze).
2. Erkläre warum diese Entität für *diesen* Nutzer relevant ist — basierend auf
   graph_context und user_interests. Keine generische Beschreibung.
3. Identifiziere 2-3 cross_cultural_links zu anderen Kulturen/Regionen wenn sinnvoll.
4. Schlage 3-5 sinnvolle Tags vor.

Antworte:
summary: [3-5 Sätze]
why_relevant: [1-2 Sätze, personalisiert]
cross_cultural_links:
  - entry: [[c_[cc]_[name]]]
    note: [1 Satz Verbindung]
tags: [kommagetrennte Tags]
```

---

## 5. Anki-Integration

### 5.1 AnkiConnect-Überblick

[AnkiConnect](https://ankiweb.net/shared/info/2055492159) ist ein Anki-Plugin das eine lokale REST-API auf Port 8765 bereitstellt. Keine Cloud, kein API-Key — läuft komplett lokal.

**Voraussetzung:** Anki muss auf dem Gerät laufen wenn der Language Agent Karten erstellt.

```python
ANKI_CONNECT_URL = "http://localhost:8765"

def anki_request(action: str, **params) -> dict:
    payload = {"action": action, "version": 6, "params": params}
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    result = response.json()
    if result.get("error"):
        raise RuntimeError(f"AnkiConnect error: {result['error']}")
    return result["result"]
```

### 5.2 Deck-Struktur

```
Anki-Deck-Hierarchie:
  Personal :: Spanisch :: Vokabeln     ← VocabEntries (ES)
  Personal :: Spanisch :: Phrasen      ← idiomatische Ausdrücke
  Personal :: Englisch :: Vokabeln     ← VocabEntries (EN)
  Personal :: Brücken                  ← LanguageBridges (Faux-amis, Concept-gaps)
```

Deck-Namen aus `user_language_profile.md` (`anki_deck_es`, `anki_deck_en`).

### 5.3 Karten-Template

Jede VocabEntry-Seite wird zu zwei Anki-Karten (Vorderseite ↔ Rückseite):

**Karte 1 (Zielsprache → Deutsch):**
```
Vorderseite:
  [Wort in Zielsprache]
  [1 Beispielsatz (B-Niveau)]

Rückseite:
  [Deutsche Übersetzung]
  [Grammatik-Note]
  [Eselsbrücke]
  [Quelle: Flamenco-Kurs, April 2026]   ← persönlicher Kontext aus PersonalFact
```

**Karte 2 (Deutsch → Zielsprache):**
```
Vorderseite:
  [Deutsche Übersetzung]
  [Kontext-Hinweis]

Rückseite:
  [Wort in Zielsprache]
  [Konjugation (falls Verb)]
  [Weitere Beispielsätze]
```

### 5.4 Anki-Export-Funktion

```python
def export_to_anki(vocab_page: WikiPage, deck_name: str) -> int:
    """Erstellt zwei Anki-Karten und gibt die Karten-ID zurück."""
    
    # Karte 1: Zielsprache → DE
    note_id_1 = anki_request("addNote", note={
        "deckName": deck_name,
        "modelName": "Einfach (Vorne-Rückseite)",
        "fields": {
            "Vorderseite": f"{vocab_page.word}\n\n<i>{vocab_page.example_sentences[1]}</i>",
            "Rückseite": (
                f"<b>{vocab_page.translations['de']}</b><br>"
                f"{vocab_page.grammar_note}<br>"
                f"<i>{vocab_page.mnemonic}</i><br>"
                f"<small>Kontext: {vocab_page.first_personal_context()}</small>"
            ),
        },
        "tags": [f"personal-os", vocab_page.language] + vocab_page.tags,
    })
    
    # Karte 2: DE → Zielsprache (vereinfacht)
    note_id_2 = anki_request("addNote", note={
        "deckName": deck_name,
        "modelName": "Einfach (Vorne-Rückseite)",
        "fields": {
            "Vorderseite": vocab_page.translations['de'],
            "Rückseite": f"<b>{vocab_page.word}</b>",
        },
        "tags": [f"personal-os", vocab_page.language, "de-to-target"],
    })
    
    return note_id_1   # Haupt-ID die in VocabEntry.anki_id gespeichert wird


def update_anki_card(anki_id: int, vocab_page: WikiPage) -> None:
    """Aktualisiert bestehende Karte wenn VocabEntry elaboriert wurde."""
    anki_request("updateNoteFields", note={
        "id": anki_id,
        "fields": {
            "Rückseite": (
                f"<b>{vocab_page.translations['de']}</b><br>"
                f"{vocab_page.grammar_note}<br>"
                f"<i>{vocab_page.mnemonic}</i>"
            ),
        }
    })
```

### 5.5 Export-Trigger

| Trigger | Wann | Aktion |
|---------|------|--------|
| Neuer VocabEntry mit `status: elaborated` | Nach Elaboration | Karte erstellen, `anki_id` in Frontmatter schreiben |
| VocabEntry aktualisiert (neue Beispielsätze) | Nach Update | Bestehende Karte aktualisieren |
| Lint-Anki-Lücke | Täglich | VocabEntries mit `anki_id: null` und `status: elaborated` exportieren |

**Anki muss laufen:** Der Language Agent prüft via `anki_request("version")` ob Anki erreichbar ist. Falls nicht: Task in eine Queue schreiben (`raw/events/` mit `source_type: "anki_pending"`), Lint-Agent verarbeitet die Queue sobald Anki wieder läuft.

### 5.6 Streak-Tracking

Das Streak-Tracking basiert ausschließlich auf AnkiConnect-Feedback — nicht auf Schätzungen:

```python
def update_anki_streak(profile_path: Path) -> None:
    """Liest Anki-Review-Statistik und aktualisiert Streak in user_language_profile.md."""
    stats = anki_request("getCollectionStatsHTML", wholeCollection=True)
    # Alternativ: heute gelernte Karten prüfen
    today_reviews = anki_request("getNumCardsReviewedToday")
    
    if today_reviews > 0:
        _increment_streak(profile_path)
    else:
        _reset_streak(profile_path)
```

---

## 6. Push-Nachrichten & Empfehlungs-System

### 6.1 Tägliche Vokabel-Challenge

```
Trigger: täglich, zufällige Zeit zwischen 10:00–19:00 Uhr
         (nicht vor 10h, nicht nach 19h — respektiert Tagesrhythmus)
Format:  Telegram-Poll (is_quiz=True) oder Freitext-Frage
Sprache: aus user_language_profile.md → daily_push_language
```

**Drei Challenge-Formate:**

**Format A — Multiple-Choice (Telegram Poll):**
```
🇪🇸 Was bedeutet "duende"?
○ Mittagsschlaf
○ Frühe Morgenstunden
● Magischer Moment / Seele  ✓
○ Sonnenuntergang
```
→ Telegram Poll mit `is_quiz=True`. Anki zeigt nach Lösung die Eselsbrücke.

**Format B — Lückentext:**
```
🇪🇸 Füll die Lücke:
"El cantaor tiene ___." (Der Sänger hat [magische Ausstrahlung].)
→ Antwort per Textnachricht
```
→ Bot prüft Antwort, sendet Feedback.

**Format C — Persönlicher Kontext:**
```
🇪🇸 Erinnerung: Wann hast du dieses Wort das erste Mal gehört?
    "duende" — Flamenco-Kurs, April 2026
→ Keine Antwort nötig — reine Aktivierung des Gedächtnisses.
```

**Auswahl-Logik:** Format wird basierend auf Tageszeit und letztem Format rotiert.

### 6.2 Vokabel-Empfehlungs-Algorithmus

Das System empfiehlt Vokabeln nicht zufällig — sondern basierend auf dem, was der Nutzer gerade erlebt:

```python
def recommend_vocab(
    user_event: str,           # aktueller Telegram-Input oder leerstring
    graph_context: list[WikiPage],
    user_language_profile: dict,
) -> list[WikiPage]:
    """Empfiehlt VocabEntries die zum aktuellen Kontext passen."""
    
    target_lang = user_language_profile["primary_learning_language"]
    
    # Priorität 1: Vokabeln die im graph_context verlinkt sind
    context_vocab = [
        p for p in graph_context
        if p.type == "VocabEntry" and p.language == target_lang
    ]
    
    # Priorität 2: Vokabeln mit thematischer Nähe zum aktuellen Event (Haiku)
    if user_event:
        keywords = _extract_keywords(user_event)
        thematic_vocab = search_wiki(
            query=" ".join(keywords), type="VocabEntry",
            language=target_lang, limit=5
        )
    else:
        thematic_vocab = []
    
    # Priorität 3: Vokabeln die lange nicht geübt wurden (Anki-Abstand)
    stale_vocab = _get_stale_vocab(
        user_language_profile["anki_deck_es"],
        min_days_since_review=14
    )
    
    # Kombinieren + Deduplizieren, Priorität einhalten
    return _merge_deduplicate([context_vocab, thematic_vocab, stale_vocab], limit=3)
```

### 6.3 CulturalEntry-basierte Empfehlungen

Wenn ein CulturalEntry im graph_context ist, empfiehlt der Agent thematisch passende Vokabeln:

```
Nutzer hat PersonalFact "Flamenco-Kurs" im graph_context
  → CulturalEntry [[c_es_flamenco]] geladen
  → Language Agent: "Flamenco hat 5 VocabEntries — welche kennt der Nutzer noch nicht?"
  → Empfehlt: compás, zapateado, tablao, cante jondo
  → Optional: Telegram-Nachricht: "Zum Flamenco-Thema: kennst du 'compás'?"
```

---

## 7. Schnittstelle zu COMP_DIARY.md

Die Verbindung zwischen Language- und Diary-Modul ist bidirektional und gut definiert.

### 7.1 Diary → Language: VocabEntry-Task

Wenn der Diary Agent beim PersonalFact-Ingest ein fremdsprachiges Wort erkennt:

```python
# diary_agent.py
def _check_foreign_words(fact: dict, graph_context: list[WikiPage]) -> list[str]:
    """Gibt Liste von Fremdwörtern zurück die keinen VocabEntry haben."""
    foreign_words = _extract_foreign_words(fact["core_fact"])   # Haiku
    existing_vocab = [p.word for p in graph_context if p.type == "VocabEntry"]
    return [w for w in foreign_words if w not in existing_vocab]

# → Für jedes neue Wort: WikiWrite mit source_type="vocab_from_fact"
#   Language Agent verarbeitet beim nächsten Supervisor-Routing-Zyklus
```

### 7.2 Language → Diary: Vocab-Kontext in PersonalFact

Wenn ein VocabEntry zu einem PersonalFact erstellt wird, schreibt der Language Agent einen Backlink in den PersonalFact (`wiki_refs` Update). Das Diary-Modul nutzt diesen Link für Impuls-Generierung:

```python
# Impuls-Typ "fact_retell" kann Vokabeln als Herausforderung einbinden:
"Erzähl die Geschichte vom Flamenco-Kurs — diesmal auf Spanisch.
 Benutze dabei: duende, compás."
```

### 7.3 Impuls-Typen: codemix und emotion_vocab

Diese Impuls-Typen aus COMP_DIARY.md nutzen VocabEntries direkt:

```python
# In diary_agent.py → _select_ingredients() für codemix:
def _get_codemix_vocab(graph_context: list[WikiPage], n: int = 3) -> list[WikiPage]:
    """Wählt n VocabEntries für codemix-Impuls."""
    eligible = [
        p for p in graph_context
        if p.type == "VocabEntry"
        and p.status == "elaborated"
        and p.language == user_profile["primary_learning_language"]
    ]
    # Bevorzuge Wörter die der Nutzer noch wenig genutzt hat
    return sorted(eligible, key=lambda p: p.usage_count)[:n]
```

Nach dem Impuls aktualisiert der Language Agent die `usage_count`-Statistik in jedem verwendeten VocabEntry:

```yaml
# Feld in VocabEntry-Frontmatter (wird durch Language Agent ergänzt):
usage_stats:
  impuls_count: 3        # wie oft in Impuls-Challenges aufgetaucht
  last_impuls: 2026-04-20
  codemix_used: 2        # wie oft in codemix-Impuls natürlich verwendet
```

### 7.4 Spanische Impuls-Antwort: StyleProfile-Frage

**Das Problem:** Wenn der Nutzer auf einen Impuls auf Spanisch antwortet — welches StyleProfile wird für das Feedback verwendet?

**Entscheidung:**

| Situation | StyleProfile |
|-----------|-------------|
| Impuls auf Deutsch | `active_style_profile` aus user_profile.md |
| Impuls auf Spanisch, kein ES-Profil gesetzt | `null` → Standard-Benchmark (2.2 WPS, 1.5s Pause) |
| Impuls auf Spanisch, ES-Profil gesetzt via `/stil [name] es` | ES-spezifisches StyleProfile |

Das Feedback für Spanisch-Antworten fokussiert daher primär auf Sprachkorrektheit und Natürlichkeit — nicht auf Storytelling-Timing. Der Feedback-Text wird durch den Language Agent generiert, nicht den Diary Agent.

```python
def analyze_spanish_impuls_response(
    voice_ogg: Path,
    impuls: Impuls,
    user_language_profile: dict,
) -> str:
    """Feedback für Spanisch-Antwort: Fokus auf Sprachqualität, nicht Storytelling."""
    transcript = whisper_model.transcribe(voice_ogg, language="es")
    
    # Sprachkorrektheit (Sonnet)
    language_feedback = _analyze_spanish_quality(transcript.text)
    
    # Timing (Whisper) — aber ohne StyleProfile-Vergleich
    timing = analyze_timing(transcript.segments)
    
    return _format_language_feedback(language_feedback, timing)
```

**Erweiterungspfad:** Wenn der Nutzer Spanisch-Stil-Referenzen anlegt (z.B. `/stilreferenz [spanischer-comedian] es`), können ES-StyleProfiles erstellt werden. Das System unterstützt das bereits — es fehlt nur die Nutzer-Aktion.

---

## 8. Language Agent LangGraph-Implementierung

### 8.1 State-Erweiterung

```python
class LanguageAgentState(TypedDict):
    # Vom Supervisor übernommen
    raw_event: RawEvent
    user_profile: dict
    user_language_profile: dict
    graph_context: list[WikiPage]
    
    # Language-spezifisch
    detected_words: list[str]            # fremdsprachige Wörter im Input
    vocab_results: list[dict]            # Ergebnis VocabEntry-Prompt pro Wort
    bridge_results: list[dict]           # erkannte LanguageBridges
    cultural_entry_result: dict | None   # falls CulturalEntry erstellt
    anki_tasks: list[str]                # Pfade zu VocabEntries für Anki-Export
    
    # Output
    wiki_writes: list[WikiWrite]
    telegram_messages: list[str]
```

### 8.2 LangGraph-Nodes

```python
language_workflow = StateGraph(LanguageAgentState)

language_workflow.add_node("detect_words",       detect_foreign_words)      # Haiku
language_workflow.add_node("create_vocab",        create_vocab_entries)      # Sonnet
language_workflow.add_node("find_bridges",        find_language_bridges)     # Sonnet
language_workflow.add_node("create_cultural",     create_cultural_entry)     # Sonnet, conditional
language_workflow.add_node("schedule_anki",       schedule_anki_export)      # kein LLM
language_workflow.add_node("update_profile",      update_language_profile)   # kein LLM
language_workflow.add_node("write_entries",       write_wiki_entries)

language_workflow.set_entry_point("detect_words")
language_workflow.add_edge("detect_words",   "create_vocab")
language_workflow.add_edge("create_vocab",   "find_bridges")

language_workflow.add_conditional_edges(
    "find_bridges",
    lambda s: "create_cultural" if s["raw_event"].get("cultural_trigger") else "schedule_anki",
    {"create_cultural": "create_cultural", "schedule_anki": "schedule_anki"}
)

language_workflow.add_edge("create_cultural",  "schedule_anki")
language_workflow.add_edge("schedule_anki",    "update_profile")
language_workflow.add_edge("update_profile",   "write_entries")
language_workflow.add_edge("write_entries",    END)
```

### 8.3 Node-Übersicht

| Node                 | Modell       | Input                              | Output                              |
|----------------------|--------------|------------------------------------|-------------------------------------|
| `detect_words`       | Haiku        | raw_event                          | detected_words                      |
| `create_vocab`       | Sonnet       | detected_words + graph_context     | vocab_results (alle Felder)         |
| `find_bridges`       | Sonnet       | vocab_results + graph_context      | bridge_results                      |
| `create_cultural`    | Sonnet       | raw_event + graph_context          | cultural_entry_result               |
| `schedule_anki`      | —            | vocab_results                      | anki_tasks (Pfade in Queue)         |
| `update_profile`     | —            | vocab_results                      | updated user_language_profile.md    |
| `write_entries`      | —            | alle results                       | WikiWrite-Objekte                   |

---

## 9. Spezialfall: Mehrsprachige Unterstützung

### 9.1 Weitere Zielsprachen

Das Modul ist nicht auf Spanisch + Englisch beschränkt. Weitere Sprachen werden automatisch unterstützt sobald:

1. Der Nutzer Inputs in einer neuen Sprache sendet (Häufigkeit ≥5 in 30 Tagen)
2. Der Language Agent erkennt: neue Sprache, kein Profil-Eintrag
3. Telegram-Nachricht an Nutzer: *"Ich erkenne häufige Französisch-Inputs. Soll ich Französisch als Lernsprache einrichten?"*

```python
LANGUAGE_DETECTION_THRESHOLD = 5   # Inputs in 30 Tagen
```

### 9.2 Muttersprachenbehandlung

Für `de` (Muttersprache) werden keine VocabEntries erstellt — es wird als Referenzsprache für Übersetzungen und Eselsbrücken verwendet. Die Muttersprache ist in `user_language_profile.md` als `Primärsprache` markiert und wird nie in die `active_learning_languages`-Liste aufgenommen.

---

## 10. Offene Fragen (Backlog)

- [ ] **Codemix-Natürlichkeits-Bewertung:** Wie genau prüfen ob Spanisch-Wörter *natürlich* eingebettet sind statt mechanisch eingefügt? (Sonnet-Analyse des Transkripts vs. einfache Wortextraktion)
- [ ] **Anki-Verfügbarkeit:** Was wenn Anki tagelang nicht läuft? Queue-Größe begrenzen? Nutzer-Reminder ab N offenen Anki-Tasks?
- [ ] **Mehrsprachiger Story-Lab:** Wenn Nutzer weitere Sprachen lernt — fact_retell auf Französisch etc. Language Agent muss VocabEntry-Auswahl sprachspezifisch machen. Generisch halten oder Sprache hardcoden?
- [ ] **Bootstrap-Vokabeln:** Empfohlene erste 20 Spanisch-Vokabeln als Seed — Liste anlegen oder aus ersten Bootstrap-PersonalFacts ableiten?
- [ ] **user_language_profile.md Update-Frequenz:** Wöchentlich für Sprachverteilung ausreichend oder bei jedem Ingest?
- [x] **Spanische Impuls-Antwort StyleProfile:** Entschieden — Standard-Benchmark für Spanisch, ES-StyleProfile als optionaler Erweiterungspfad (§7.4)
- [ ] **Anki-Deck-Struktur:** Unterdeck "Phrasen" sinnvoll? Oder alles in "Vokabeln"? (Separierung erleichtert gezielte Übung)
