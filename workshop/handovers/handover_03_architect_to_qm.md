# Handover: Architekt → QM
> Erstellt: 2026-05-08 | von: Architekt | an: Quality-Manager | Workshop: [README](../README.md)

---

## Was du aus 03_architect.md zwingend lesen musst

- **[03_architect.md §A — Eingebrachte Vetos und Marker](../03_architect.md)** — sechs Marker (3× ENT-NÖTIG, 3× ARCH-FRAGE), Detail-Begründung pro Marker. Keine harten ARCH-VETOs. Lies §A1 vollständig — die ENT-NÖTIG-Begründungen sind die Schnittstelle zu deiner Risikobewertung.
- **[03_architect.md §B — Analyse + Skizzen (B1–B12)](../03_architect.md)** — pro Chance/Empfehlung: Machbarkeit, Skizze (≤10 Zeilen Code), Aufwand, Risiken, Reihenfolge. Du musst dort Test-Lücken, Idempotenz-Schwächen, Budget-Anomalien finden.
- **[03_architect.md §C3 — Schulden-Bezug + Inkonsistenz-Befunde](../03_architect.md)** — vier `(?)…(?)`-Inkonsistenz-Befunde, die nicht Workshop-Output sind, sondern bestehende Schulden. **Bitte als P1 in deinen QM-Risiko-Snapshot ziehen** — keiner ist reines Workshop-Veto-Material, aber jeder kann einen MVP-2-Zweitwellen-Schritt entgleisen lassen.
- **[03_architect.md §D — Eigene Ergänzungen](../03_architect.md)** — sechs Punkte (D1–D6) zu Idempotenz, Migrations, Telemetry, Tests, Draft-Branch-Reaktivierung, `_split_frontmatter`-Konsolidierung. **D2 und D6 sind versteckt-architektur-relevant**: ohne sie multipliziert sich der Aufwand jeder weiteren Migration.
- **[03_architect.md §Risiken (Top 5)](../03_architect.md)** — geordnet, mit Wahrscheinlichkeit/Schaden/Mitigation. Deine QM-Risikomatrix sollte sich daran orientieren.
- **[03_architect.md §Implementierungs-Reihenfolge](../03_architect.md)** — neun Schritte (1–8 MVP-2-Zweitwelle, 9 MVP-3-Backlog). Deine P1/P2/P3-Bewertung darf die Reihenfolge nicht zerreißen, ohne die Abhängigkeiten zu adressieren.

---

## Konkrete Prüfpunkte für QM

### Prüfpunkt 1 — Sensitivity-Pfade (P1)

**Was:** [03 §A1 (01 §C6)](../03_architect.md) und [03 §B6](../03_architect.md). Multi-Modal-Backfill schickt Bilder per Default an Vision-API (Cloud).

**Konkret prüfen:**
1. Ist die Default-Tier-Annahme `sensitive` ausreichend, oder muss `private` Default sein (mit explizitem Opt-In für Cloud-Vision via Hint `#vision`)?
2. Wenn ein Bild ohne Caption kommt: was passiert? Quick-Save in `raw/assets/` oder Auto-Ingest mit Default-Tier?
3. Welche Mitigation greift, **bevor** Vision-API gerufen wird (PII-Detection lokal? Hash-basierter Block-List?)?
4. Ist [ENT-006](../../doc/ENTSCHEIDUNGEN.md#ent-006-sensitivity-tier-modell-provider-routing) klar genug formuliert für Bilder, oder braucht es eine [ENT-NEU?]?

### Prüfpunkt 2 — Budget-Risiken (P2)

**Was:** [03 §B + §QM-Empfehlungen](../03_architect.md). Architekt-Schätzung: Workshop-Schritte 1–8 bleiben deutlich unter $5–10/Monat.

**Konkret prüfen:**
1. Validiere die Annahmen in B1, B5, B6, B8 (Sonnet/Haiku-Calls + Vision-Calls).
2. Was ist das Worst-Case-Szenario (z.B. 50 Bilder/Tag, wöchentliches Refresh + tägliches Lint)?
3. Greift [ENT-045](../../doc/ENTSCHEIDUNGEN.md#ent-045-proaktiver-kanal-grundsätzlich-freigegeben-opt-in) `Haiku-only`-Constraint für Workshop-Outputs (C8 nutzt Sonnet)?

### Prüfpunkt 3 — Test-Lücken (P1 für Migrations, P2 für Renderer)

**Was:** [03 §D4](../03_architect.md). Heute keine `tests/`-Struktur dokumentiert.

**Konkret prüfen:**
1. **B4 (C4 Frontmatter-Migration):** ohne Idempotenz-Test ist Migration unsicher. Pflicht-Fixture? Pflicht-Snapshot des `anki_id`-Feldes vor/nach? **P1, weil destruktiv.**
2. **B9 (Render-Modul):** Snapshot-Tests gegen Erwartungs-HTML — UX hat das vorgesehen, aber `pytest-snapshot` ist nicht in `requirements.txt`. P2.
3. **B3 (Lint-Detektoren):** `before/`-`after/`-Wiki-Mock-Trees fehlen. P1, weil Lint-Auto-Fixes destruktiv auf Wiki schreiben.
4. **B6 (Multi-Modal):** End-to-End-Test fehlt. P1.

### Prüfpunkt 4 — Idempotenz (P1 für Schritt 1+5+7)

**Was:** [03 §QM-Empfehlungen Punkt 4](../03_architect.md).

**Konkret prüfen:**
1. **C4 (Frontmatter-Migration):** zweiter Lauf = 0 Diffs?
2. **C5a (Health-Tag):** Re-Export setzt Tag deterministisch (gleicher Input → gleicher Output)?
3. **C6 (Multi-Modal):** Doppel-Bild-Drop erzeugt nur ein Event ([D1](../03_architect.md))?
4. **B2 (FTS5-Build):** Re-Build überschreibt vollständig oder nur Delta? Konsistenz-Garantie?

### Prüfpunkt 5 — Inkonsistenz-Befunde aus §C3 (P1)

**Was:** vier `(?)…(?)`-Befunde, die der Architekt während Pflichtlektüre fand.

**Konkret prüfen:**
1. **`graph_writer.py:55-65` `git checkout main` Bug:** würde der Workshop-Schritt 5 (Lint-Live, abhängig von Draft-Branch-Reaktivierung in §D5) damit brechen? Trivialer Fix oder versteckter Mehraufwand?
2. **`WIKI_PAGE_THRESHOLD` 30 vs. 150:** welcher Wert gilt für QM-Test-Szenarien? Hat Code-Verhalten Vorrang vor Doku?
3. **`index_updater` als Phantom-Modul:** ist die Architektur-Doku jetzt-noch-zukunftssicher, wenn `scripts/rebuild_index.py` der reale Pfad wird?
4. **Draft-Branch dormant:** muss QM die formale Pause oder die Re-Aktivierung empfehlen? Welche Test-Strategie kippt bei welcher Wahl?

### Prüfpunkt 6 — Reihenfolge-Treue (P2)

**Was:** [03 §Implementierungs-Reihenfolge](../03_architect.md).

**Konkret prüfen:**
1. Stören PO-Prioritäten (z.B. C5a als P1 für UX) die technische Reihenfolge?
2. Welche Schritte sind **parallelisierbar** (1+2 nein, 3+4 ja, 5+6 mit Pre-Req)?
3. Aufwand-Realismus: 39h Architekt-Aufwand für Schritte 1–8 — plausibel? Test-Aufwand-Aufschlag (~30%) reicht?

---

## Was QM *nicht* prüft (Scope-Schutz)

- **Inhaltliche UX-Empfehlungen** (Slot-Profile A/B/C/D, CSS-Block, Mockups). UX-Mandat, Architekt hat sie validiert. QM darf höchstens Test-Strategie für Render-Output prüfen.
- **State-of-Art-Recherche-Qualität** (01 §B Quellen). AI-Research-Mandat.
- **Karpathy-Prinzip-Diskussion.** Bleibt nicht-verhandelbar.
- **`05_po_synthesis.md`-Inhalt.** Das ist PO-Mandat. QM liefert Risiken+P1/P2/P3, nicht Backlog-Entscheidung.
- **Anti-Decisions formulieren.** PO-Mandat.

---

## Architekt-Empfehlungen, zu denen QM-Verdict erbeten ist

| Architekt-Empfehlung | QM-Aktion gewünscht |
|---|---|
| `out/anki_export_log.json` für Health-Tag-Zeitstempel (§A1) | Backup-/Restore-Strategie? Was passiert bei `out/`-Löschung? |
| `agents/render/` als Modul-Standort statt `scripts/` (§A1) | Test-Aufbau-Konsequenzen? Bestehende Imports? |
| Default-Tier `sensitive` für Bilder (§A1, §B6) | Risikoreich genug für ENT-Eskalation oder reicht Architekt-Default? |
| Direct-Master-Write für Migration (§A1, [01 §C4-Marker]) | Test-Aufbau analog `anki_id`-Patch? |
| Snapshot-Tests vs. End-to-End-Tests | Welche Pflicht-Tests pro Workshop-Schritt? |
| Backup-Branch-Strategie für C4 | Restore-Test? Branch-Lebenszyklus? |
| Draft-Branch formale Pause vs. Re-Aktivierung (§D5) | Test-Auswirkungen pro Pfad? |

---

## Schnittstelle Architektur↔QM — was ich für die Risikobewertung beitrage

**Beobachtung 1:** Die Workshop-Vorschläge sind **architektonisch sauber** — keine harten Vetos, alle Karpathy-konform. Aber sie **schichten sich**: jeder Schritt ist Pre-Req für den nächsten. Wenn QM einen mittleren Schritt aus Risiko-Gründen verwirft, **fällt die Reihenfolge zusammen**.

**Beobachtung 2:** Der größte versteckte Risikofaktor ist **nicht** der Workshop-Vorschlag, sondern die **bestehende Schuld**, die die Workshop-Schritte aufdecken. Frontmatter-Schuld, Draft-Branch-Dormanz, `index_updater`-Phantom, `WIKI_PAGE_THRESHOLD`-Inkonsistenz — alle sind Pre-Workshop, aber jede einzelne kann einen Workshop-Schritt entgleisen lassen.

**Beobachtung 3:** Test-Strategie ist heute uneinheitlich. Renderer hat Snapshot-Vorschlag (UX), aber Lint, Migration, Multi-Modal haben **gar keine Test-Pattern**. QM sollte das als zentralen P1-Befund nehmen.

**Beobachtung 4:** Sensitivity-Tier-Bruch durch C6 ist **das einzige echte Privacy-Risiko** im Workshop. Alle anderen Risiken sind technisch (Schulden, Drift, Idempotenz). C6 ist das einzige Vertrags-Bruch-Risiko gegenüber [ENT-006](../../doc/ENTSCHEIDUNGEN.md#ent-006-sensitivity-tier-modell-provider-routing).

**Mein Bias:** Ich bin Architekt, kein QM — wenn meine Risiko-Gewichtung gegen ein Test- oder Compliance-Prinzip verstößt, das ich nicht sehe, **bitte ohne Zögern höher gewichten**. Insbesondere bei §A1-ENT-NÖTIG-Markern: ich habe sie als ENT-Bedarf eingeordnet, aber QM darf sie als P1-Risiko aufstufen, wenn der ENT-Pfad zu lange dauert.

---

## Übergabe-Status

- [x] [03_architect.md](../03_architect.md) geschrieben (Teil A + B + C + D + Empfehlungen + Risiken + Reihenfolge).
- [x] Sechs Marker in [01_ai_research.md](../01_ai_research.md) und [02_ux.md](../02_ux.md) gesetzt (3× ENT-NÖTIG, 3× ARCH-FRAGE), keine ARCH-VETOs.
- [x] Implementierungs-Skizzen für 12 Chancen/Empfehlungen (B1–B12).
- [x] Vier Inkonsistenz-Befunde (`(?)…(?)`) aus Pflichtlektüre als Architekt-Befund dokumentiert in §C3.
- [x] Sechs eigene Ergänzungen (D1–D6) — Idempotenz, Migrations, Telemetry, Tests, Draft-Re-Aktivierung, Frontmatter-Konsolidierung.
- [x] Top-5-Risiken geordnet mit Wahrscheinlichkeit/Schaden/Mitigation.
- [x] Implementierungs-Reihenfolge mit Abhängigkeiten (8 MVP-2-Schritte + 1 MVP-3-Backlog).
- [x] Querverweise an QM in [protokoll.md](../protokoll.md) eingetragen.
- [x] Diese Handover-Datei bereit.
- [ ] Git-Commit (passiert nach Schreibe-Schluss von protokoll.md).

**Bereit für Phase 4.** QM-Session kann mit frischer Claude-Code-Session und [prompts/04_qm_prompt.md](../prompts/04_qm_prompt.md) starten.

---

## Anti-Erwartungen

- QM darf alle Architekt-Empfehlungen aufstufen oder abstufen — Begründung in `04_qm.md` reicht.
- QM darf neue Inkonsistenzen aus Code-Querlesen melden, die der Architekt übersehen hat — als zusätzliche `(?)…(?)`-Befunde im QM-File.
- QM darf P0/P1/P2/P3-Klassifikation pro Vorschlag liefern (Architekt hat nur Reihenfolge); PO synthetisiert in 05.
- QM darf einzelne Workshop-Schritte als `[NICHT-MVP-2]` markieren, wenn Risiken es verlangen — Architekt hat alle als MVP-2-fähig markiert.
