# UX-Radar 001 — Erst-Einarbeitung & UX-Empfehlungen
> Erstellt: 2026-04-19 | Autor: UI/UX (Telegram-Spezialisierung), Erstbegegnung mit dem Projekt
> Typ: **EMPFEHLUNG / VORSCHLAG — keine Anweisung, keine Roadmap**
> Adressaten: Product Owner, Quality-Manager, Senior System Architect
> Abgrenzung: Dieser Strang (`sessions_ux/`) läuft **neben** der regulären Session-Nummerierung (`sessions/NNN_*.md`). Nichts hier blockiert, nichts hier verpflichtet — es ist ein Radar, kein Beschluss.

---

## Warum dieser Eintrag existiert

Ich bin neu im Team. Der Bot läuft seit [sessions/013_2026-04-19.md](../sessions/013_2026-04-19.md) stabil im Ollama-Modus, MVP-1 wartet auf den Anthropic-Key ([ENT-038](../doc/ENTSCHEIDUNGEN.md)). Das ist eine ungewöhnlich gute Gelegenheit: Ich kann mich mit der UX-Oberfläche befassen, **ohne** laufende Implementierungsphasen zu stören. Alles was ich hier notiere, sind Beobachtungen und Ideen-Samen — gewichtet nach dem, was die Kollegen vermutlich an ihnen skeptisch machen würde.

Gelesene Unterlagen (Kern): [doc/ARCHITECTURE.md](../doc/ARCHITECTURE.md) §7, [doc/COMP_SERVICES.md](../doc/COMP_SERVICES.md), [doc/CHANCEN.md](../doc/CHANCEN.md), [doc/ENTSCHEIDUNGEN.md](../doc/ENTSCHEIDUNGEN.md), [bot.py](../bot.py), [sessions/014_2026-04-19.md](../sessions/014_2026-04-19.md), [sessions/013_2026-04-19.md](../sessions/013_2026-04-19.md).

---

## 1. Stärken der aktuellen UX (wert zu erhalten)

| # | Stärke | Warum sie wirkt |
|---|---|---|
| S1 | **Zero-Friction-Eingabe.** Jede Nachricht ist potentiell ein Fact — kein Modus, kein Kommando nötig. | Bricht die Einstiegshürde fast vollständig. Der Nutzer muss nicht wissen, ob er "was Sprachliches" oder "was Persönliches" schickt. |
| S2 | **Multi-Modal von Anfang an.** Text / Voice / Foto / Video / Dokument laufen alle denselben Pfad. | Die handler-Symmetrie in [bot.py:147-191](../bot.py#L147-L191) ist UX-Kapital — Nutzer lernen *ein* Muster. |
| S3 | **Obsidian als Read-Only-Fenster.** Der Nutzer kann jederzeit "in den Graph schauen" ohne den Bot zu fragen. | Baut Vertrauen auf — die Black-Box ist keine Black-Box. |
| S4 | **Emoji-Statusmicro.** `⏳ → ✓ / ❌ / ⚠️` ist sparsam, aber ausreichend informativ. | Minimalistische Rückmeldung respektiert den Chat-Rhythmus. |
| S5 | **`#tag`-Prefix als User-Hint.** [bot.py:152-155](../bot.py#L152-L155) — stiller, optionaler Power-User-Kanal. | Gut designte Progressive-Disclosure: unsichtbar für Anfänger, mächtig für Fortgeschrittene. |
| S6 | **Bootstrap-Interview als strukturierter Einstieg.** [bot.py:86-98](../bot.py#L86-L98). | Gibt dem Kaltstart-Problem ([ENT-011](../doc/ENTSCHEIDUNGEN.md)) ein Gesicht, ohne zu überfordern. |
| S7 | **Sessions-als-Gedächtnis-Pattern**, intern angewandt auf Engineering. | Das System lebt, was es vom Nutzer will. Das ist konsistent und erzeugt Vertrauen in die Philosophie. |

---

## 2. Schwachstellen (aus UX-Sicht — nicht alle sind Bugs)

Alle in Vorschlags-Ton. Keine Feature-Anordnung.

### 2.1 Die Bestätigung nach Ingest ist technisch, nicht menschlich

Aktuell: `✓ Gespeichert: pf_2026-04-19_flamenco-kurs.md` ([bot.py:124](../bot.py#L124)).

Der Dateiname ist ein Artefakt — für einen Nutzer bedeutet er *"irgendetwas Korrektes ist passiert"*, aber nicht *"ich wurde verstanden"*. Vorschlag weiter unten (Idee I1).

### 2.2 Keine sichtbare Rückkopplung der Graph-Intelligenz

Der Supervisor berechnet `story_score`, der graph_context findet verwandte Seiten, der Lint-Agent entdeckt Korrelationen — **der Nutzer sieht davon nichts im Chat**. Der wertvollste Teil des Systems ist unsichtbar.

Das ist ein Widerspruch zur Selbstverstärkungs-These aus [CHANCEN.md §1.2](../doc/CHANCEN.md): wenn der Mehrwert mit jedem neuen Fact wächst, sollte dieses Wachstum **spürbar** werden.

### 2.3 Fire-and-Forget-Charakter

Heute: Nutzer schickt, Bot quittiert, Ende. Kein Thread, kein Dialog. Das ist einfach — aber verschenkt die Kernstärke von Telegram (Reply-Threads, Reactions, InlineKeyboards).

### 2.4 Kein proaktiver Kanal

Die [ENT-019](../doc/ENTSCHEIDUNGEN.md)-Impulse sind spezifiziert, aber nicht live. Das ist korrekt (MVP-Schnitt), macht aber den Bot zum reinen Postkasten. Für die "Gewohnheit stapeln"-These aus [CHANCEN.md §2.4](../doc/CHANCEN.md) fehlt damit die tägliche Anfass-Möglichkeit.

### 2.5 Fehler-Tonfall ist distanziert

Heute: `⚠️ Fehler: [exception-Text]` und `⚠️ Systemfehler. Log geprüft.` ([bot.py:133](../bot.py#L133), [bot.py:263](../bot.py#L263)).

Das ist technisch sauber, aber der Nutzer bleibt mit der Exception allein. Vorschlag siehe I6.

### 2.6 Ambiguität wird stumm aufgelöst

Wenn der Supervisor nicht sicher ist (vocab vs. personal_fact vs. beides), entscheidet er eigenständig. Der Nutzer merkt es erst, wenn er in Obsidian die "falsche" Einordnung sieht. [ARCHITECTURE.md §3.3](../doc/ARCHITECTURE.md) erwähnt bereits die Rückfrage-Option — wert, konkret auszuformulieren (I4).

### 2.7 Keine leichte Korrektur

"Ach Mist, das war April nicht März" — heute keine vorgesehene Geste dafür. Der Nutzer müsste in Obsidian editieren oder über den Bot neu schreiben (Duplikat).

---

## 3. Ideen-Radar

Drei Kategorien nach Aufwand. Reihenfolge innerhalb jeder Kategorie ist **Wirkungs-Rang aus UX-Sicht**, nicht Priorität.

### 3.1 Leichte Früchte (≤ 1 Tag pro Stück, kein Schema-Impact)

#### I1 — Inhaltliche statt dateiartige Bestätigung

**Aktuell:** `✓ Gespeichert: pf_2026-04-19_flamenco-kurs.md`

**Vorschlag:**
```
✓ Flamenco-Kurs gespeichert
  story_score 8 · verknüpft mit 3 ähnlichen Facts
  "Spanische Kultur" wächst.
```

Konkret: statt `w["path"].split("/")[-1]` in [bot.py:123-124](../bot.py#L123-L124) ein kurzer "Title + score + 1-Zeile-Graph-Kontext"-Render. Der Supervisor hat die Info ohnehin im State (`graph_context`, `wiki_writes`). Kein neuer Call, nur Formatierung.

**Vermutliche QM-Bedenken:** Wortwahl könnte LLM-generiert sein → Kosten? — Nein, reine Python-Formatierung auf existierenden State-Feldern. Keine zusätzlichen Tokens.

**Vermutliche Architekt-Bedenken:** WikiWrite-Vertrag. — Hier nicht berührt, nur gelesen.

#### I2 — Ambiguität als InlineKeyboard-Frage

Wenn `Supervisor.classify()` unsicher ist (z.B. confidence < 0.7 oder explizit `ambiguous`):

```
┌────────────────────────────────────────────┐
│  "Me encanta el duende del flamenco"        │
│                                            │
│  Wie soll ich das verstehen?               │
│                                            │
│  [📘 Vokabel: "duende"]                     │
│  [📝 Erlebnis-Notiz]                        │
│  [🔀 Beides]                                │
│  [💾 Nur roh speichern]                     │
└────────────────────────────────────────────┘
```

Nutzt Telegram `InlineKeyboardMarkup`, bereits in [ARCHITECTURE.md §7 Ebene 1](../doc/ARCHITECTURE.md) vorgesehen. Klick → Callback schreibt `user_hint` und ruft die Pipeline neu auf.

**PO-Bedenken:** Klingt nach Feature-Creep. — Eher nicht, weil der ambiguous-Fallback **heute stillschweigend irgendwas rät**. Ein Button-Fragezeichen ist fachlich ehrlicher und kostet keine zusätzlichen LLM-Calls.

#### I3 — Emoji-Reactions als Quick-Tagging

Telegram unterstützt Reactions auf Nachrichten. Der Bot könnte die Eingangs-Nachricht des Nutzers mit kontext-sensitiven Reactions anbieten:

- 👍 = alles korrekt erfasst
- 💬 = erzähl-wert, bitte später mehr fragen
- 🔖 = wichtig (story_score manuell anheben)
- 🌙 = privat (sensitivity=private erzwingen — Ollama-only)

Die Reaction wird vom Bot als Post-Hoc-Hint übernommen und in den Fact zurückgeschrieben. **Null Schreib-Friction.**

**QM-Bedenken:** Mehr API-Aufrufe für Reaction-Updates? — Nur ein `edit_message_reactions`-Call, kein LLM-Aufruf. Vernachlässigbar.

#### I4 — Pinned-Message als lebendes Dashboard

Eine einzige gepinnte Bot-Nachricht, die der Bot bei jedem Ingest live aktualisiert (`edit_message_text`):

```
📊 Graph-Puls
• 47 Facts · 23 Vokabeln · 4 Concepts
• Letzter Fact: Flamenco-Kurs (vor 2 Min, story_score 8)
• Wochen-Top-Cluster: Spanische Kultur
• Offen: 3 Facts mit score>7 für Story-Lab
```

Immer sichtbar oben im Chat, ohne jeden neuen Ping. Sehr hohe UX-Wirkung / sehr niedrige Friction.

**Architekt-Bedenken:** Was wenn der Edit fehlschlägt? — `try/except` um den einen Call, state weiter verwenden. Defensiv zu halten.

### 3.2 Mittlere Ideen (2–5 Tage, schemafreundlich)

#### I5 — "Morgen-Kaffee" als täglicher Gewohnheits-Anker

Einmal pro Tag, zufällige Zeit innerhalb eines 2h-Fensters (Nutzer stellt Präferenz ein):

```
☕ Guten Morgen.
• Heute vor einem Jahr: "Erste Flamenco-Show" (story_score 6)
• Noch ungeübt mit Score 8: "Fahrradunfall in München"
• Vokabel des Tages: duende — "der künstlerische Moment des Entflammens"
  → schon verlinkt mit [[pf_flamenco-kurs]]

Was davon willst du anfassen?
[🎭 Story üben]  [🇪🇸 Vokabel-Quiz]  [📖 Fact-Karte]  [💤 Morgen wieder]
```

Baut die [ENT-019](../doc/ENTSCHEIDUNGEN.md)-Impulse auf ein Ritual auf. Auswahl `💤` darf eine Weile nichts triggern — Ritual muss Nein können, sonst wird es zur Last.

**PO-Bedenken:** Scope! Das ist MVP-2-Territorium. — Richtig. **Erst nach MVP-1.** Aufnehmen ins Radar, nicht ziehen.

**QM-Bedenken:** Wenn der Nutzer Freitag bis Sonntag im Urlaub ist, fährt er mit 3 unbeantworteten Impulsen zurück. — Regel: Impuls mit 24h-TTL, danach verwerfen. `🔇 Diese Woche pausieren`-Kommando einbauen.

#### I6 — Menschlichere Fehler

Statt `⚠️ Fehler: [exception]`:

```
🤔 Hm — da ist was schiefgelaufen.
Dein Input ist nicht verloren (steht in raw/events/).

[🔁 Nochmal versuchen]  [📋 Details]  [🙈 Egal, weiter]
```

Die Exception wandert weiterhin ins Log; der Nutzer bekommt eine Handlung statt einer Panne. Rein Formatierungs-Änderung in [bot.py:131-133](../bot.py#L131-L133) und [bot.py:261-265](../bot.py#L261-L265).

#### I7 — Reply-Threads als Update-Kanal

Python-Telegram-Bot kennt `update.message.reply_to_message`. Wenn der Nutzer auf eine alte Bot-Bestätigung antwortet, interpretiert der Bot das als **Update desselben Facts** statt als neuen Fact:

```
Nutzer (vor 2 Tagen): "war beim Flamenco-Kurs"
Bot: "✓ Flamenco-Kurs gespeichert ..."
Nutzer (jetzt, antwortet auf Bot-Nachricht):
       "Kleine Korrektur: der Kurs war in Malaga nicht Madrid"
Bot: ✏️ Aktualisiert: Flamenco-Kurs → Malaga
```

Extrem natürliche Korrektur-Geste, ohne eigenes Kommando. Benötigt: `raw_event`-Referenz im State-Dict, `update`-Modus im LangGraph-Flow (analog `append` in [WikiWrite](../doc/ARCHITECTURE.md)).

**Architekt-Bedenken:** LangGraph hat heute keinen Update-Pfad. — Ja, und genau deshalb ist das eine Architektur-Frage, nicht nur UX. Wenn für MVP-2 eh ein Update-Mechanismus kommt, lässt sich dieses UI-Muster nachträglich überstülpen.

#### I8 — Stil-Karten-Vergleich als nativer Poll

Die 4 Stil-Karten aus [ENT-022](../doc/ENTSCHEIDUNGEN.md) sind Telegram-Poll-Material erster Güte:

```
Welcher Ton passt zu dir bei dieser Geschichte?

○ Lakonisch: "Ich lag im Kies. Nobody clapped."
○ Beobachtend: "Die Sekunde davor war still."
○ Selbstironisch: "Elegant wie ein Pokal-Wrapper."
○ Warm: "Meine Mutter hätte gelacht — zu Recht."
```

`is_anonymous=False`, Auswahl landet im `practice_log`. Null Custom-UI-Code — nativer Telegram-Poll.

### 3.3 Größere Ideen (Woche+, Architektur-Impact)

#### I9 — Mini App als Graph-Spiegel (Ebene 3, aber wann?)

Heute: Obsidian ist der Viewer. Problem: mobile Obsidian-Nutzung ist für viele Nutzer zu schwer. Eine **Mini App** mit:
- Suche über `index.md`
- Cluster-Visualisierung der Top-Concepts
- Tap-to-edit für bestehende Facts

Aufwand ~1 Woche ([ARCHITECTURE.md §7 Ebene 3](../doc/ARCHITECTURE.md)). **Nur wenn** messbar Mobile-Nutzer ein Editier-Problem haben. Heute nicht anfangen.

#### I10 — "Konversationaler Bootstrap" statt 10-Fragen-Fragebogen

Der aktuelle Bootstrap ([bot.py:86-98](../bot.py#L86-L98)) ist ein Fragebogen — 10 starre Fragen, keine Reaktion auf Antworten. Alternative:

```
Bot: "Erzähl mir von deinem peinlichsten Moment."
Nutzer: "Mit 16 auf einer Party ..."
Bot: "Bam. Wer war dabei — Freunde oder Fremde?"
Nutzer: "Halb-Fremde, von einer anderen Schule."
Bot: "Alles klar, hab ich. Letzte Runde-Frage dazu: wie hast du dich danach gefühlt? (oder sag 'weiter' wenn du genug hast)"
```

Führt zu reicheren PersonalFacts *vom ersten Moment an*. Kostet ~3-5 Haiku-Calls pro Frage statt 1 — bei 10 Fragen also ~40 Haiku-Calls = unter $0.01.

**QM-Bedenken:** Kosten-Variance. — Gering bei Haiku. Messen, Cap setzen (max 3 Follow-Ups pro Frage).

**PO-Bedenken:** Bootstrap ist final ([ENT-011](../doc/ENTSCHEIDUNGEN.md)). — Nicht revidieren — als Erweiterungs-Modus (`/bootstrap --conversational`) einführen, wenn überhaupt.

---

## 4. Drei Mini-Mockups (die ich am stärksten finde)

### Mockup A — Der neue Ingest-Flow

```
Nutzer → "War heute beim Flamenco-Kurs in Málaga. Fand heraus, dass 'duende' 
          nicht übersetzbar ist."

Bot   → ⏳ Verarbeite...
        [2s später] 
        ✓ Flamenco-Kurs in Málaga gespeichert
          story_score 7 · 4. Fact im Cluster "Spanische Kultur"
          💡 Erster Hit auf Vokabel "duende" — hab's als Bridge 
             DE↔ES notiert.
          
          [📖 Details] [✏️ Korrigieren] [🎭 Später üben]

Nutzer → [tippt ✏️ Korrigieren]

Bot   → Was war falsch?
        ○ Ort
        ○ Datum
        ○ Sprache/Vokabel-Klassifikation
        ○ Was anderes (schreib's mir)
```

Prinzip: die **drei wichtigsten User-Intentions nach Ingest** (ansehen / korrigieren / üben) werden zur Selbstverständlichkeit.

### Mockup B — Graph-Puls als Pinned Message

```
─────────────── oben im Chat, gepinnt ───────────────
📍 Dein Graph heute

47 Facts · 23 Vokabeln · 4 Themen-Cluster

Letzter Eintrag: vor 12 Min — "Flamenco-Kurs in Málaga"
Stärkster Cluster: Spanische Kultur (12 Facts)
Offen: 3 Geschichten mit Score ≥ 7 wollen geübt werden

Getippt seit Montag: 14 Facts · +4.2% Graph-Wachstum

[📊 Mehr] [🎭 Eine Story wählen] [🇪🇸 Vokabel-Quiz]
─────────────────────────────────────────────────────
```

Rein Telegram-`edit_message_text`, kein neuer Ping. Null Störung, maximale Sichtbarkeit der Graph-Intelligenz.

### Mockup C — Wochenend-Replay (proaktiv, Sonntag 20:00)

```
🌙 Deine Woche

Du hast diese Woche 14 Mal geschrieben — Tops:

🥇 "Fahrradunfall in München" — score 9
   Ungeübt. Willst du sie erzählen?
   
🥈 "Erster richtiger Flamenco-Moment" — score 8
   Verknüpft mit: 'duende', 'compás', 'cante jondo'

📈 Themen die wachsen: Spanische Kultur (+3), Gesundheit (+2)
📉 Stumm: Tech-Opinions (0 — sonst 2/Woche)

[🎭 Fahrrad-Story üben]  [📖 Vollständige Statistik]  
[💤 Nächste Woche wieder]
```

Zeigt **Wachstum** und **Stille** — beides aussagekräftig. Das "Stumm"-Feld ist besonders wertvoll: erinnert den Nutzer an Interessensfelder, die aus dem Blick geraten.

---

## 5. Was die Kollegen wahrscheinlich skeptisch macht — antizipiert

### Product Owner (Scope-Schutz)
- **Befürchtung:** "Das klingt nach Feature-Creep vor MVP-1." — Berechtigt. **Nichts von I4–I10 vor MVP-1 ziehen.** I1–I3 sind reine Formatierungs-/Dialogtweaks auf bestehendem State und vertretbar als MVP-1-Politur.
- **Befürchtung:** "Wir haben die UI-Ebenen bei [ENT-018](../doc/ENTSCHEIDUNGEN.md) schon gestaffelt." — Alle Ideen hier bleiben in Ebene 1–2; I9 markiert explizit Ebene 3 als *Upgrade-Pfad, nicht heute*.

### Quality-Manager (Kosten & Testbarkeit)
- **Befürchtung:** "Jede proaktive Nachricht ist ein Haiku/Sonnet-Aufruf — das summiert sich." — Stimmt für I5/I10. Deshalb Vorschlag: **Opt-In + Frequenz-Cap + TTL für Impulse.** Monatsbudget-Alarm wie in [COMP_SERVICES.md §9.3](../doc/COMP_SERVICES.md) bereits vorgesehen.
- **Befürchtung:** "Ollama-Fallback-Texte werden unsauber." — Ja (siehe [hinweise/technischer_hinweis.md §2](../hinweise/technischer_hinweis.md)). Alle UX-Strings, die LLM-generiert sind, sollten **Template-first, LLM-second** gebaut werden — Fallback-Text hardcoded, LLM liefert nur Nuance.
- **Befürchtung:** "Wie testet man UX?" — Für I1/I3/I4 reichen Screenshot-Vergleiche im Tester-Chat. Für I5/I10 braucht es das was wir ohnehin nicht haben (Nutzer-Sessions). Ehrlich benennen.

### Senior System Architect (Schema & Verträge)
- **Befürchtung:** "I7 (Reply-Threads als Update) bricht den Append-Only-Charakter von `raw/events/`." — Nein, solange Updates eigene `raw/events/`-Datei mit `operation: "update"` und `ref_event: <old_path>` schreiben. Append-Only bleibt.
- **Befürchtung:** "Pinned Message (I4) setzt persistenten Zustand pro Chat voraus." — Ein einziger Integer (Message-ID) in `user_profile.md` oder `.env`. Vernachlässigbar.
- **Befürchtung:** "Der `WikiWrite`-Vertrag." — Keine der Ideen berührt ihn. Bot bleibt Input/Output-Adapter; Schreib-Freigabe weiter Supervisor-gesteuert ([main_workflow.py:207-213](../main_workflow.py#L207-L213)).

---

## 6. Empfehlung — der einzige konkrete Vorschlag

**Wenn überhaupt etwas aus diesem Radar gezogen wird, dann I1 + I6 als MVP-1-Politur**, sobald der API-Key da ist und Phase 6 ([sessions/014_2026-04-19.md §Modus B](../sessions/014_2026-04-19.md)) gelaufen ist:

- **I1 — inhaltliche Bestätigung** — macht die Claude-Qualität unmittelbar sichtbar (sobald sie da ist). Ohne I1 merkt der Nutzer den Unterschied zwischen Ollama- und Claude-Lauf kaum.
- **I6 — menschlichere Fehler** — `⚠️ Systemfehler. Log geprüft.` wurde [in Session 013](../sessions/013_2026-04-19.md) eingeführt und ist funktional korrekt, aber uneinladend.

Beides zusammen: ~1 Tag Arbeit, kein Architektur-Impact, kein Schema-Impact, keine neuen LLM-Calls. Das wäre mein Vorschlag für den ersten UX-Beitrag nach MVP-1.

Alles andere bleibt Radar — warten auf einen Auslöser:
- **I2 (Ambiguität-Button)** sobald reproduzierbar `intent=ambiguous` auftritt.
- **I3 (Reactions), I4 (Pinned), I5 (Morgen-Kaffee)** frühestens MVP-2.
- **I7 (Reply-Threads)** braucht erst einen Update-Pfad im LangGraph-Flow.
- **I9 (Mini App)** nur bei belegtem Mobile-Schmerz.
- **I10 (Konversationaler Bootstrap)** frühestens nach 5+ realen Bootstraps, wenn klar ist, wo Nutzer aussteigen.

---

## 7. Offene Fragen an die Kollegen

- **PO:** Welche der kleinen Ideen (I1, I6) sollen bei MVP-1-Abschluss mitlaufen — oder ist das bereits zu viel Scope-Kreuzfeuer?
- **QM:** Gibt es Telemetrie-Pläne, um "hat Nutzer auf Bot-Bestätigung reagiert?" überhaupt zu messen? Ohne das bleibt UX-Bewertung subjektiv.
- **Architekt:** Gäbe es prinzipielle Einwände, einer der Wiki-Seiten (z.B. `user_profile.md`) ein `telegram_state`-Feld beizumischen (Pinned-Message-ID, Impuls-Präferenzen)? Oder lieber eigene `.state/` außerhalb des Graphen?

---

## 8. Eigenreflexion zum Schluss

Ich erkenne an, dass dieses Projekt seine UX-Philosophie sehr bewusst konservativ aufgebaut hat: Text-First, Obsidian-Native, Markdown-Portabel, Karpathy-Wiki-Prinzip. Jede UI-Geste, die ich vorschlage, steht potentiell im Konflikt zu diesem Ethos ("mehr Geste = mehr Lock-in in Telegram"). Das ist ein legitimer Konflikt, den ich nicht überstimmen möchte. Die Leitlinie, die ich aus [CHANCEN.md §1.5](../doc/CHANCEN.md) ziehe: **alles Sichtbare im Chat ist ephemer — der Knowledge Graph bleibt Markdown.** Solange das UI-Feedback den Graphen nicht ersetzt, sondern ihn spürbar macht, passt es zum Projekt.

Gerne Gegenrede.
