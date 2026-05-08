# Workshop-Prompt 05: PO-Synthese
> Phase 5 von 5 | Adressat: **Product Owner** | Modus: **Synthese + Backlog + ENT-Updates + S026-Brief**
> Diese Datei wird in eine **frische Claude-Code-Session** als Eingabe gegeben.

---

## Pflichtlektüre (in dieser Reihenfolge, vollständig)

1. `prompts_team/head_product_owner.md` — Rollen-Kopf (insbesondere Nicht-verhandelbare Prinzipien)
2. `workshop/README.md`
3. `workshop/01_ai_research.md`, `workshop/02_ux.md`, `workshop/03_architect.md`, `workshop/04_qm.md` — alle vollständig, inkl. aller eingefügten Marker
4. Alle vier Files in `workshop/handovers/`
5. `workshop/protokoll.md` — vollständige Übersicht
6. `doc/ENTSCHEIDUNGEN.md` (vollständig — keine Duplikate erzeugen)
7. `doc/CHANCEN.md` (falls existiert)
8. `doc/INKONSISTENZEN.md` (falls existiert)
9. `sessions/024_2026-05-07.md` und `sessions/025_2026-05-08.md` — aktueller Stand
10. `hinweise/technischer_hinweis.md`

## Auftrag

**Sechs Liefer-Punkte.**

### 1 — `workshop/05_po_synthesis.md`

Sektionen:

- **Synthese der 4 Rollen-Beiträge** — was ist das gemeinsame Bild? Wo widersprechen sich die Rollen? Wie löst du die Widersprüche?
- **Verdict pro Leitfrage** (Leitfragen 1–6 aus README) — pro Frage: Status (gut / okay / lückenhaft / kritisch), kurze Begründung, Bezug auf Backlog-Item.
- **Anti-Decisions-Sektion** — was wir bewusst NICHT ändern. **Mindestens 5 Punkte.** Schützt MVP-3-Plan + nicht-verhandelbare Verträge. Beispiele:
  - Karpathy-Prinzip bleibt (kein RAG, kein Vektor-Store)
  - WikiWrite-Vertrag bleibt
  - MVP-3-Stufung bleibt unangetastet
  - Bestehende ENTs bleiben gültig (Revisionen brauchen neue ENT-Nummer mit `revidiert`-Verweis)
  - Kein Refactoring der Supervisor-Architektur ohne separates ENT
- **Reaktion auf Vetos und Marker** — pro `(!)ARCH-VETO(!)` / `(!)ENT-NÖTIG(!)` / `(!)ARCH-FRAGE(!)` aus dem Protokoll: angenommen / abgelehnt / verschoben + Begründung.
- **Reaktion auf QK-Vorschläge** — pro QK aus 04_qm.md: angenommen / abgelehnt + Begründung. Angenommene QKs werden zu ENT oder bleiben workshop-intern dokumentiert (deine Wahl).
- **Top-3-Workshop-Insights** — was nimmt die Organisation aus diesem Workshop dauerhaft mit? (Auch wenn keine Implementierung folgt.)

### 2 — `workshop/backlog.md`

Format **pro Eintrag**:

```
## BL-NN: [Titel]
- **Priorität:** P1 / P2 / P3 / Radar
- **Aufwand:** [Stunden grob]
- **Quelle:** Workshop-File X.Y (z.B. 03_architect.md §B2)
- **Architekt-Status:** [MACHBAR] / [MACHBAR-BEDINGT: …] / [NICHT-HEUTE: …]
- **QM-Status:** [P-Klasse + Risiko-Note kurz]
- **Bezug ENT:** ENT-NN existiert / ENT-NEU als ENT-NN angelegt / kein ENT nötig
- **Definition of Done:** [konkret, prüfbar]
- **Vorgesehene Rolle für Implementierung:** Architekt / UX / AI-Research / PO
- **Vorgesehene MVP-Stufe:** MVP-2.5 (Cleanup) / MVP-3 / MVP-3+
```

**Mindestens 5 Einträge, maximal 15.** Mehr ist nicht hilfreich — wird Friedhof. Lieber harte Auswahl + Rest in `doc/CHANCEN.md`.

**Sortierung:** P1 zuerst, dann P2, dann P3, dann Radar. Innerhalb gleicher Klasse: nach Aufwand aufsteigend (kleinster Aufwand oben).

### 3 — `doc/ENTSCHEIDUNGEN.md` ergänzen

Nur ENTs für **wirklich entschiedene** Sachen. Format wie bestehende ENTs (Nummer, Titel, Status, Begründung, Datum). Falls keine neue ENT entsteht — auch okay, dann nicht ergänzen.

**Wichtig:** Eine ENT-Revision (Änderung einer bestehenden Entscheidung) braucht **neue ENT-Nummer** mit `revidiert: ENT-XXX`-Verweis. Nicht die alte ENT umschreiben.

### 4 — `doc/CHANCEN.md` ergänzen

Alle Workshop-Ideen die `[RADAR]` / "nicht jetzt" sind, hier als Eintrag. Format: bestehende CHANCEN-Konvention. Falls `doc/CHANCEN.md` nicht existiert — kurz prüfen ob Anlage gerechtfertigt ist (siehe `doc/ENTSCHEIDUNGEN.md ENT-036` für Doku-Regel) und im Synthese-File markieren.

### 5 — `sessions/025_2026-05-08.md` Ergebnis-Notizen füllen

Standard-Sektion `## Ergebnis-Notizen`:
- Workshop durchgeführt, alle 5 Phasen abgeschlossen
- Kern-Outputs: Verweis auf `workshop/05_po_synthesis.md`, `workshop/backlog.md`
- ENTs neu: Liste mit Nummern und Titeln
- CHANCEN neu: Liste mit Titeln
- `hinweise/technischer_hinweis.md` aktualisiert: ja/nein, was geändert
- Nächste Session: 026, Adressat: [Rolle]

### 6 — `sessions/026_DATUM.md` schreiben

Standard-Brief-Format (wie `sessions/024_2026-05-07.md`). Adressat ist die Rolle, die das **Top-1-Backlog-Item** bearbeitet:

- Wenn Top-1 ist Implementierung → Architekt
- Wenn Top-1 ist Design / Karten-HTML → UX
- Wenn Top-1 ist Forschung / GE → AI-Research
- Wenn Top-1 ist neue ENT-Diskussion → PO selbst (nächste Session)

Brief enthält:
- Was S025 (Workshop) lieferte (sehr knapp, 1 Absatz, mit Verweis auf `workshop/05_po_synthesis.md`)
- Was in S026 zu tun ist (das Top-1-Backlog-Item, Definition of Done)
- Pflichtlektüre für Adressat
- Was NICHT in S026 hineinziehen (Scope-Schutz)
- Erwartete Liefer-Artefakte am Sessionsende
- Session-Log-Eintrag für 026

### 7 — `hinweise/technischer_hinweis.md` aktualisieren (falls 04_qm.md das vorgeschlagen hat)

Übernimm den QM-Vorschlag aus `04_qm.md §Aktualisierungs-Vorschlag`. Sehr konservativ — nur wenn klar entschieden.

## Was du NICHT machst

- Kein Code, kein Detail-Review, keine Architektur-Diskussion innerhalb dieses Files. Nur Was und Warum.
- Keine ENT-Einträge die nicht klar entschieden sind. Lieber als CHANCEN parken oder im Backlog als P3 stehen lassen.
- Kein Über-Bord-Werfen des bestehenden Plans. **Anti-Decisions-Sektion ist Pflicht** — sie schützt das System.
- Keine eigenen Implementierungs-Wahlen ("mach es mit Klasse X") — nur Was und Warum.
- Keine retroaktive Modifikation der Phasen-Files (01–04) außer reinen Tippfehler-Fixes. Die Vetos und Befunde stehen wie sie stehen.
- Keine Bewertung von Code-Qualität — das war QM-Territorium.

## Stop-Kriterien

- Wenn QM ein "Blocker"-Meilenstein-Urteil gegeben hat → vor Synthese-Start klären, ob Workshop wiederholt wird (Phase 3 oder früher) oder eingeschränkte Synthese ohne den Blocker-Ast stattfindet. Beide Wege im 05-File begründen.

## Liefer-Stop

**Commit:** `Session 025: Workshop-Synthese + Backlog + S026-Brief`

Damit ist der Workshop offiziell geschlossen und das Projekt geht zurück in den normalen Session-Rhythmus mit Backlog-getriebener Priorisierung. Die nächste Session (026) startet mit dem Brief, den du in Liefer-Punkt 6 geschrieben hast.
