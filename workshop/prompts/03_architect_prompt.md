# Workshop-Prompt 03: Architekt
> Phase 3 von 5 | Adressat: **Senior System Architect** | Modus: **Machbarkeit + Veto + Implementierungs-Skizze**
> Diese Datei wird in eine **frische Claude-Code-Session** als Eingabe gegeben.

---

## Pflichtlektüre (in dieser Reihenfolge, vollständig)

1. `prompts_team/head_architect.md` — Rollen-Kopf (insbesondere "Nicht-verhandelbare Verträge")
2. `workshop/README.md`
3. `workshop/01_ai_research.md` — vollständig
4. `workshop/02_ux.md` — vollständig
5. `workshop/handovers/handover_01_research_to_ux.md`
6. `workshop/handovers/handover_02_ux_to_architect.md`
7. `workshop/protokoll.md`
8. `doc/ARCHITECTURE.md` — vollständig
9. `doc/ENTSCHEIDUNGEN.md` — vollständig
10. `doc/SCHEMA.md`
11. `hinweise/technischer_hinweis.md`
12. Code-Querlesen (zur Machbarkeits-Beurteilung): `agents/supervisor.py`, `agents/language_agent.py`, `agents/graph_writer.py`, `scripts/export_anki.py`, `bot.py`
13. Falls vorhanden: `doc/COMP_*.md` Komponenten-Specs

## Auftrag

Vier Teile.

### Teil A — Früh-Vetos in 01 und 02 (sofort, vor Teil B)

Du darfst — und sollst — **direkt** in `workshop/01_ai_research.md` und `workshop/02_ux.md` an konkreten Stellen Marker einfügen. Pro Marker eine Zeile, eindeutig erkennbar:

- `(!)ARCH-VETO: [kurz Grund](!)` — Vorschlag bricht einen nicht-verhandelbaren Vertrag (WikiWrite, Karpathy, ENT-006, Branch-master, Budget).
- `(!)ENT-NÖTIG: [kurz Grund](!)` — Vorschlag braucht eine PO-Entscheidung als ENT, bevor er in den Backlog kann.
- `(!)ARCH-FRAGE: [Frage](!)` — Vorschlag ist okay, aber etwas an der Implementierung muss geklärt werden.

**Pro Marker** in `workshop/protokoll.md` Sektion "Veto-/ENT-Marker" eine Zeile mit Verweis auf die Detail-Begründung in `03_architect.md §A`.

**Warum hier:** UX-Arbeit ist getan, Vetos kommen vor deinem eigenen File — so sieht jeder spätere Leser sofort, welche Stellen kontaminiert sind. Setze Marker sparsam und nur, wenn du sie auch in `03_architect.md` begründest.

### Teil B — Eigene Analyse + Implementierungs-Skizze (50 %)

Pro relevanter Chance/Empfehlung aus 01 und 02:

1. **Machbarkeit:** `[MACHBAR]` / `[MACHBAR-BEDINGT: …]` / `[NICHT-HEUTE: …]`
2. **Implementierungs-Skizze (max 10 Zeilen)** — welche Datei(en), welche Komponenten, welcher Vertrag.
3. **Aufwand-Schätzung** (Stunden, grob).
4. **Risiken / Schulden** — was kommt obendrauf, was muss vorher saniert werden (Beispiel: Frontmatter-Schuld aus S023 als Pre-Req für saubere Mapping-Logik).
5. **Reihenfolge-Empfehlung** — was muss vor was?

### Teil C — Architektur-Konsequenzen (20 %)

- Muss `doc/ARCHITECTURE.md` ergänzt werden? Wenn ja: welche Sektion, was rein? **Konkret formulieren** — der PO wird das später committen oder nicht.
- Entstehen neue Komponenten-Specs? (`doc/COMP_*.md` Kandidaten — Begründung + grober Inhalt.)
- Welche bestehenden Schulden in `hinweise/technischer_hinweis.md` werden durch welche Workshop-Idee getroffen?

### Teil D — Eigene Ergänzungen (10 %)

Was kam in 01/02 nicht vor, ist aber aus Architektur-Sicht **kritisch**? Z.B. fehlende Idempotenz-Garantien, fehlende Migrations-Pfade, fehlende Telemetry für Graph-Wachstum, fehlende Test-Strategie für neue Renderer.

## Liefer-Files

### `workshop/03_architect.md`

```
# 03 — Architekt: Machbarkeit + Vetos + Implementierungs-Skizzen

## Zusammenfassung (max 5 Bullets)

## Teil A — Eingebrachte Vetos und Marker
> Tabelle: [Quell-File:Sektion] | Marker-Typ | Begründung-Detail | Bezug zu Vertrag/ENT

## Teil B — Analyse + Skizzen
### Pro Chance: B1, B2, B3, … (Machbarkeit / Skizze / Aufwand / Risiken / Reihenfolge)

## Teil C — Architektur-Konsequenzen
### C1: Änderungen in doc/ARCHITECTURE.md (konkret formulieren)
### C2: Neue Komponenten-Specs (Kandidaten)
### C3: Schulden-Bezug

## Teil D — Eigene Ergänzungen

## Empfehlungen für QM-Phase
> Was der QM zwingend prüfen muss.

## Risiken (Top 5, geordnet)

## Implementierungs-Reihenfolge (Vorschlag)
> Numerierte Liste mit Abhängigkeiten. Was zuerst, was danach.
```

### `workshop/handovers/handover_03_architect_to_qm.md`

Format analog. Pflicht: konkrete Prüfpunkte für QM (welche Sensitivity-Pfade, welche Budget-Risiken, welche Test-Lücken).

### `workshop/protokoll.md` — eine Zeile in Beitrags-Tabelle + Veto-Marker-Sektion füllen

### Edits in `workshop/01_ai_research.md` und `workshop/02_ux.md`

Nur Marker-Einträge (siehe Teil A). Keine inhaltlichen Änderungen.

## Was du NICHT machst

- Kein Code-Push. Skizzen nur, in Backticks im Markdown.
- Kein Edit in `agents/`, `bot.py`, `scripts/`, `wiki/`, `doc/`. Workshop-Files sind erlaubt (für Marker und dein eigenes File).
- Keine ENT-Einträge — schlage sie nur vor (`[ENT-NEU?]`), entscheidet PO.
- Kein --no-verify, kein force-push, keine destruktiven Git-Ops.
- Keine Rückwärtskompatibilitäts-Shims als Empfehlung — entweder löschen oder behalten, kein Mittelweg.

## Stop-Kriterien

- Wenn 01 oder 02 fundamental kontradiktorisch zu nicht-verhandelbaren Verträgen sind und du Vetos einbringst, dies klar in `03_architect.md §A` und im Protokoll dokumentieren — der PO entscheidet später, ob die Idee in 05 stirbt oder ENT-revidiert wird.
- Wenn dir bei der Pflichtlektüre eine **bestehende Inkonsistenz** auffällt (z.B. ARCHITECTURE.md vs. Code), notiere das in `03_architect.md §C3` mit `(?)`-Marker. Das ist nicht dein Fix, aber wertvoller Befund für den PO.

## Liefer-Stop

Commit: `Workshop-Phase 3: Architekt — Machbarkeit + Vetos + Skizzen`
