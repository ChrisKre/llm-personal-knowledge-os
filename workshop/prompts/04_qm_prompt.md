# Workshop-Prompt 04: Quality Manager
> Phase 4 von 5 | Adressat: **Quality Manager** | Modus: **Risiko-Audit + P1/P2/P3 + QK-Vorschläge**
> Diese Datei wird in eine **frische Claude-Code-Session** als Eingabe gegeben.

---

## Pflichtlektüre (in dieser Reihenfolge, vollständig)

1. `prompts_team/head_quality_manager.md` — Rollen-Kopf
2. `workshop/README.md`
3. `workshop/01_ai_research.md` (inkl. Architekt-Marker)
4. `workshop/02_ux.md` (inkl. Architekt-Marker)
5. `workshop/03_architect.md`
6. `workshop/handovers/handover_03_architect_to_qm.md`
7. `workshop/handovers/handover_01_research_to_ux.md`, `handover_02_ux_to_architect.md` (zur Kontext-Vollständigkeit)
8. `workshop/protokoll.md`
9. `hinweise/technischer_hinweis.md`
10. `doc/ENTSCHEIDUNGEN.md`
11. `doc/QUALITY_CONTROL_008.md` — Stil-Referenz für Review-Format
12. `doc/ARCHITECTURE.md` (querlesen, als Vergleichs-Soll)

## Auftrag

Drei Teile.

### Teil A — Konsistenz-Check (30 %)

- Stimmen die Vorschläge aus 01–03 untereinander überein? (Wo widersprechen sie sich? Konkrete Stellen.)
- Stimmen sie mit dem aktuellen Stand von `doc/ARCHITECTURE.md` und `doc/ENTSCHEIDUNGEN.md` überein? (Inkonsistenz-Liste, falls nein.)
- Werden nicht-verhandelbare Prüfpunkte verletzt?
  - **Sensitivity-Routing** (`sensitivity: private` → Ollama, nie Claude — ENT-006, ENT-028)
  - **WikiWrite-Vertrag** (kein direktes Schreiben in `wiki/` außer über Draft→Master-Flow)
  - **Karpathy-Prinzip** (kein RAG, kein Vektor-Store)
  - **Branch master**, kein --no-verify
  - **Budget** (~$5–10/Monat, keine täglichen Sonnet-Loops ohne Kosten-Nachweis)

### Teil B — Risiko-Bewertung pro Vorschlag (50 %)

Für jede Chance/Empfehlung aus 01–03 (verlinkt mit Quell-Sektion):

- **Klasse:** `P1` (Blocker für MVP-3) / `P2` (mitziehen in nächste Session) / `P3` (technische Schuld, dokumentieren) / `OK`
- **Testbarkeit:** wie würde man verifizieren, dass das funktioniert? (Konkret: Test-Idee, kein Fertig-Test, kein Code.)
- **Kosten-Risiko:** zusätzliche LLM-Calls? Tägliche Loops? Sonnet vs. Haiku? **$/Monat-Schätzung wenn möglich.**
- **Schulden-Bezug:** wird eine bestehende Schuld aus `hinweise/technischer_hinweis.md` getroffen — beseitigt oder verschärft? Konkret namentlich nennen.

Format als Tabelle, plus Detail-Block pro Eintrag mit > 1 Zeile Kommentar.

### Teil C — QK-Entscheidungs-Kandidaten + Meilenstein-Urteil (20 %)

- Welche QK-* Entscheidungen würdest du **vorschlagen**? (PO entscheidet final in 05.)
  - Format wie `doc/QUALITY_CONTROL_008.md` — `### QK-N: [Titel]`, **Befund / Entscheidung / Auswirkung / Status**.
- **Meilenstein-Urteil zum Workshop-Output bisher:**
  - "Synthese kann starten" — Standard-Pfad
  - "Synthese mit Auflagen" — was ist die Auflage?
  - "Blocker: [X]" — was muss vor Synthese geklärt werden?
  - Begründung in 2–3 Sätzen.

## Liefer-Files

### `workshop/04_qm.md`

```
# 04 — QM: Risiko-Audit + Meilenstein-Urteil

## Zusammenfassung (max 5 Bullets)

## Teil A — Konsistenz-Check
### A1: Workshop-interne Konsistenz
### A2: Konsistenz mit doc/ARCHITECTURE.md und doc/ENTSCHEIDUNGEN.md
### A3: Verletzungen nicht-verhandelbarer Prüfpunkte

## Teil B — Risiko-Bewertung
### B1: P1-Befunde
### B2: P2-Befunde
### B3: P3-Befunde
### B4: OK-Befunde (kurz)

## Teil C — QK-Vorschläge + Meilenstein-Urteil
### C1: QK-N (mehrere Einträge möglich)
### C2: Meilenstein-Urteil

## Empfehlungen für PO-Synthese-Phase
> Was der PO zwingend in der Synthese behandeln muss (z.B. ENT-Bedarf, Anti-Decisions).

## Aktualisierungs-Vorschlag für hinweise/technischer_hinweis.md
> Welche Schulden neu, welche behoben durch Workshop-Vorschläge. Format: Bullet-Liste, wird vom PO am Ende übernommen.
```

### `workshop/handovers/handover_04_qm_to_po.md`

Format analog. Pflicht: P1-Liste oben, klare ENT-Bedarfs-Liste, Meilenstein-Urteil als Header.

### `workshop/protokoll.md` — eine Zeile in Beitrags-Tabelle + QM-Risiko-Snapshot füllen

## Was du NICHT machst

- Keine Fixes — du findest Probleme, du löst sie nicht.
- Keine Architektur-Wahl — du nennst Alternativen, der PO entscheidet.
- Keine ENT-Einträge im `doc/`-Tree.
- Keine stilistischen Code-Kommentare ohne sachliche Begründung.
- Kein "alles nochmal von vorne" — Quality-Reviews schließen Arbeit ab, sie ersetzen sie nicht.

## Stop-Kriterien

- Wenn ein **P1-Blocker** existiert, der die PO-Synthese sinnlos machen würde (z.B. fundamentaler Vertragsbruch, der nicht heilbar ist) → Meilenstein-Urteil "Blocker: [X]" und beim PO eskalieren. PO entscheidet, ob Phase 5 trotzdem läuft (dann eingeschränkt) oder Phase 3 nochmal.

## Liefer-Stop

Commit: `Workshop-Phase 4: QM — Risiko-Audit + Meilenstein-Urteil`
