# Workshop-Prompt 02: UX
> Phase 2 von 5 | Adressat: **UI/UX Spezialist** | Modus: **Radar + konkretes Anki-HTML-Konzept + Frontend-Symbiose**
> Diese Datei wird in eine **frische Claude-Code-Session** als Eingabe gegeben.

---

## Pflichtlektüre (in dieser Reihenfolge, vollständig)

1. `prompts_team/head_ux.md` — Rollen-Kopf
2. `workshop/README.md` — Workshop-Charta
3. `workshop/01_ai_research.md` — vollständig (Phase 1 ist abgeschlossen, das ist dein Input)
4. `workshop/handovers/handover_01_research_to_ux.md` — was AI-Research dir aufträgt
5. `workshop/refs/anki_html_examples/` — alle HTML-Anker-Beispiele vom PO (Pflicht!)
6. `workshop/protokoll.md`
7. `doc/ARCHITECTURE.md §7` — Telegram-UI-Ebenen
8. `bot.py` — querlesen, aktueller Frontend-Stand
9. `scripts/export_anki.py` — wie heute gerendert wird (CSS, Tags, Backlink)
10. Eine Quell-Vocab-Datei vollständig: z.B. `wiki/language/vocab/v_es_madrugada.md` und `v_es_duende.md`
11. `doc/ENTSCHEIDUNGEN.md` — UX-relevante: ENT-018, ENT-019, ENT-040–043, ENT-050–052
12. `sessions_ux/ux_001_initial-radar.md` — Stil-Referenz für den Radar-Ton

## Auftrag

Drei Teile.

### Teil A — Reaktion auf AI-Research (20 %)

Was übernimmst du, was kritisierst du, was schlägst du anders vor? Sehr kurz halten — der eigentliche UX-Wert kommt in Teil B/C. Maximal 1 Seite.

### Teil B — Anki-HTML-Konzept + Render-Layer (50 %)

**Klarstellung vom PO:** Die Anki-**Sync-Schicht** (genanki, GUID-stabil) ist gelöst (S023). Du designst die **Render-Schicht** — wie wird ein Markdown-Knoten zu einer hübschen, lernbaren HTML-Karte?

Liefere:

1. **Template-System-Konzept**
   - Wie viele Templates? Wonach unterscheiden sie sich (CEFR-Level? Wort-Klasse? Mit/ohne Eselsbrücke?)?
   - Welche Variablen / Slots?
   - Fallback-Strategie für fehlende Felder ("Template-first, LLM-second")
2. **Konkreter HTML-Entwurf für mindestens 2 Karten-Varianten**
   - Z.B. A1-Verb (`escribir`) vs. C1-Substantiv-mit-Eselsbrücke (`duende`).
   - Hier liegt eine txt datei für anki import mit ein paar Beispielen. Könnte als inspiration dienen, muss aber nicht! `C:\Users\<user>\Documents\repos\raw\sources\espayol_verbos_irregulares.txt`.
   - Mindestens **eine Variante** muss zeigen wie eine Eselsbrücke elegant gerendert wird.
3. **Pflicht-Web-Recherche: 3 weitere SOTA-Anki-Card-Templates**
   - Mit URL, Datum, Kurzanalyse (was machen sie gut, was nicht).
   - Du darfst über Anki hinaus suchen (z.B. SuperMemo, RemNote, Mochi-Karten) — alles was Render-Inspiration liefert.
   - Quellen-Sektion am Ende des Files.
4. **Schnittstellen-Vorschlag Markdown → HTML**
   - Welche Frontmatter-Felder mappen auf welche Slots?
   - Welche Body-Sektionen mappen auf welche Slots? (Heute: `## Meaning`, `## Bridge`, `## Examples`.)
   - Wie gehen wir mit fehlenden Feldern um? (Fallback-Templates.)
   - Wo liegt der Template-Renderer (in `scripts/export_anki.py`? Eigenes Modul?)? — Du gibst eine **Empfehlung**, der Architekt entscheidet final.
   - **Bedenke:** Markdown-Knoten verändern sich (Story-Lab fügt Beispiele nach, User editiert), aber Sync ist gelöst. Du sorgst nur dafür, dass das **Mapping** robust gegen leere Felder und neue Felder ist.
5. **Mobile vs. Desktop**
   - Was bricht? Was bleibt?
   - Konkret: funktioniert Obsidian-Backlink in Anki Mobile (S024 hat das geprüft — nutze den Befund)?

### Teil C — Knowledge-Graph ↔ Frontend allgemein (30 %)

Über Anki hinaus: welche Frontend-Berührpunkte hat der Graph? Telegram-Inline-Antworten, Obsidian-Backlinks, künftige Web-Renderer? Welche Symbiose-Möglichkeiten siehst du? (Aufgreifen, was AI-Research in Teil C empfohlen hat — speziell Leitfrage 5 der Charta.)

Maximal 3 Mockups (ASCII-Skizzen oder beschriebenes Verhalten).

Pro Idee Aufwand markieren: `[LEICHTE-FRUCHT]` / `[MITTLERE-IDEE]` / `[GROSSE-IDEE]` und MVP-Stufe `[MVP-2]` / `[MVP-3]` / `[RADAR]`.

## Liefer-Files

### `workshop/02_ux.md`

```
# 02 — UX: Anki-HTML-Konzept + Frontend-Symbiose

## Zusammenfassung (max 5 Bullets)

## Teil A — Reaktion auf AI-Research

## Teil B — Anki-HTML-Konzept
### B1: Template-System-Konzept
### B2: HTML-Entwurf Karten-Variante 1 — [Name]
### B3: HTML-Entwurf Karten-Variante 2 — [Name]
### B4: Recherchierte SOTA-Beispiele (mind. 3)
### B5: Schnittstelle Markdown → HTML
### B6: Mobile vs. Desktop

## Teil C — Frontend-Symbiose (Graph ↔ UI)
### C1, C2, C3 (max 3)

## Empfehlungen für Architekt-Phase
> Was der Architekt mitnehmen MUSS. Konkret, mit Begründung.

## Antizipierte Skepsis (PO/Architekt/QM)

## Quellen
> SOTA-Anki-HTML-Recherche, mindestens 3 Quellen mit URL/Datum.
```

### `workshop/handovers/handover_02_ux_to_architect.md`

Format analog zu Handover 01. Adressat: Architekt. Pflicht-Inhalt: was er an Render-Architektur entscheiden muss, welche Felder-Maps er prüfen muss, wo Template-Renderer hingehört.

### `workshop/protokoll.md` — eine Zeile in der Beitrags-Tabelle ergänzen + ggf. Querverweise

## Was du NICHT machst

- Kein produktiver Code in `scripts/` oder `agents/`. HTML+CSS-Code im Workshop-File ist OK.
- Kein neuer ENT.
- Kein Sync-Schicht-Redesign — Render-Schicht only.
- Kein Telegram-Spezial-Speicher (Chat-IDs als primäre Referenz etc., siehe head_ux.md).
- Kein "wir brauchen eine eigene App" ohne Begründung dass Telegram die Anforderung nicht erfüllen kann.

## Stop-Kriterien

- Wenn `workshop/refs/anki_html_examples/` leer ist → BLOCKIERT, beim PO melden, **nicht** ohne weitermachen.
- Wenn AI-Research-Ergebnis fundamental kontradiktorisch zum aktuellen Code-Stand ist → markieren `(?)`, weitermachen, im Handover an Architekt eskalieren.

## Liefer-Stop

Commit: `Workshop-Phase 2: UX — Anki-HTML-Konzept + Frontend-Symbiose`
