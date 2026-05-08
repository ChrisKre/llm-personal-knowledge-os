# Workshop-Protokoll (Spine)
> Index aller Workshop-Beiträge. Jede Rolle ergänzt **eine Zeile** in der Beitrags-Tabelle und Querverweise/Marker in den darunter stehenden Sektionen.
> Die Detail-Inhalte stehen in den jeweiligen Rollen-Files (01–05). Hier nur Index + Verweise.

---

## Beitrags-Index

| # | Rolle | Datum | Kern-Befunde (max 3, sehr kurz) | Detail-File | Handover an |
|---|---|---|---|---|---|
| 1 | AI-Research | 2026-05-08 | (1) Index-Drift + Slug-Summaries blocken Retrieval; (2) Frontmatter-Schuld blockt alle künftigen Konsumenten; (3) Lint-Stub heißt: keine Konsolidierung. | [01_ai_research.md](01_ai_research.md) | UX |
| 2 | UX | 2026-05-08 | (1) Ein Notetype, vier Slot-Profile (A/B/C/D); Template-first, LLM-second; (2) Render-Layer als eigenes Modul `scripts/render_card.py` empfohlen + `RenderDict`-Adapter-Vertrag für künftige Discord/E-Mail-Konsumenten; (3) Mobile-Backlink-Bruch bestätigt — Klartext-Pfad als zweite Zeile Pflicht; C5a (Health-Tag) angenommen, C5b (zweiter Backlink) abgelehnt. | [02_ux.md](02_ux.md) | Architekt |
| 3 | Architekt | 2026-05-08 | (1) Keine harten ARCH-VETOs — alle Workshop-Vorschläge Karpathy-konform; 6 Marker (3× ENT-NÖTIG, 3× ARCH-FRAGE). (2) Reihenfolge ist scharf: C4 (Frontmatter) → C1 (Index) → Render-Modul → C5a (Health-Tag) → C3 (Lint). (3) Vier Pre-Workshop-Inkonsistenzen aufgedeckt: `graph_writer.py`-Branch-Bug (`main` vs. `master`), `WIKI_PAGE_THRESHOLD` 30-vs-150, `index_updater`-Phantom-Modul, Draft-Branch dormant. | [03_architect.md](03_architect.md) | QM |
| 4 | QM | 2026-05-08 | (1) Meilenstein-Urteil: **"Synthese mit Auflagen"** — Workshop-Output sachlich konsistent mit Karpathy/WikiWrite/Branch-master/Budget; vier P1-Befunde alle heilbar in 05. (2) Vier P1-Auflagen für PO: `graph_writer.py:55-65` Branch-Bug-Fix als Schritt 0 (R1), Frontmatter-Migration mit drei Auflagen (Backup-Branch + Idempotenz-Test + `anki_id`-Hash-Snapshot, R2/QK-8), Sensitivity-ENT für Bilder vor C6 (R3/QK-9), Test-Skelett als Pre-Implementierungs-Pflicht (R4/QK-14). (3) Sieben QK-Vorschläge (QK-8 bis QK-14) + drei ENT-NEU-Vorschläge + zwei ENT-Updates (ENT-007 Status, ENT-027 Doku-Korrektur); plus Bonus-Befund: [graph_reader.py:3-4](../agents/graph_reader.py#L3-L4) Header-Kommentar widerspricht Z.20 derselben Datei (R16). | [04_qm.md](04_qm.md) | PO |
| 5 | PO-Synthese | _TBD_ | _TBD_ | [05_po_synthesis.md](05_po_synthesis.md) | (Ende) |

---

## Querverweise

> Format: `[Rolle-Quelle → Rolle-Ziel] [Thema] — [Quell-File:Sektion] — [Bemerkung kurz]`
> Beispiel: `[AI-Research → UX] Knowledge-Graph-Visualisierung — 01_ai_research.md §C2 — UX bitte in 02_ux.md prüfen`

- `[AI-Research → UX]` Symbiose Graph↔Frontend (Charta-Leitfrage 5) — `01_ai_research.md §C5` — UX-Hauptanker für Phase 2: Verdict zu C5a (Health-Tag) + C5b (zweiter Backlink) erwartet.
- `[AI-Research → UX]` Multi-Modal-Karten-Format — `01_ai_research.md §A4 Punkt 5` + `§Empfehlungen für UX-Phase Punkt 3` — UX bitte Format-Empfehlung pro VocabEntry-Typ liefern (Bild/Audio auf Karte ja/nein).
- `[AI-Research → UX]` Render-Layer-Strategie für künftige Konsumenten — `handovers/handover_01_research_to_ux.md §Schnittstelle Graph↔Frontend` — Empfehlung zu Mindest-Frontmatter-Feldern für generischen Renderer.
- `[AI-Research → Architekt]` (via UX-Handover-Reihenfolge) Frontmatter-Schuld-Migration vor Lint-Live + vor Index-Renderer — `01_ai_research.md §C4` + Risiko 1.
- `[AI-Research → Architekt]` Index-Updater-Code-Pfad fehlt; Drift Index↔FS sichtbar — `01_ai_research.md §A1` + Lücke L2.
- `[AI-Research → PO-Synthese]` Backlog-Vorschlag nach Schmerz: P1=C1 (Index reparieren) + C4 (Frontmatter); P2=C3 (Lint live) + C5 (Symbiose); P3=C2/C6/C8; Off-Radar=C7 — `01_ai_research.md §Teil C`.
- `[UX → Architekt]` Render-Layer-Modul-Trennung — `02_ux.md §B5` + `handover_02_ux_to_architect.md §Auftrag 1` — Empfehlung: neues `scripts/render_card.py` mit `render_front`/`render_back`/`pick_profile`/`CSS_BLOCK`. Architekt entscheidet final.
- `[UX → Architekt]` `RenderDict`-Adapter-Vertrag für künftige Render-Konsumenten — `02_ux.md §C3` + `handover_02_ux_to_architect.md §Auftrag 3` — Mindest-Schnittstelle (`identity`/`content`/`display`/`links`) für Anki + künftige Discord/E-Mail (ENT-049).
- `[UX → Architekt]` Mobile-Backlink-Befund — `02_ux.md §B6` — `obsidian://`-URI bricht auf Anki Mobile (S024-Live-Test); `backlink-path` als Klartext-zweite-Zeile ist nicht-verhandelbar.
- `[UX → Architekt]` Health-Tag `health::stale-mnemonic` (C5a annehmen, C5b ablehnen) — `02_ux.md §Empfehlungen Punkt 4` + `handover §Auftrag 4` — Tag-Schema, Persistenz-Ort `out/anki_export_log.json` vs. `usage_stats:` zu klären.
- `[UX → Architekt]` IPA-Schema-Frage `[ENT-NEU?]`-Kandidat — `02_ux.md §B5` + `handover §Auftrag 6` — UX-Empfehlung: Frontmatter-Feld `ipa:`. Architekt-Verdict: Schwenk wert oder zu früh?
- `[UX → Architekt]` Reihenfolge-Hinweis (von AI-Research übernommen + verstärkt) — `handover §Auftrag 5` — Frontmatter-Schuld-Migration vor Render-Layer-Refactor; sonst erbt jeder neue Render-Konsument den Regex-Workaround.
- `[UX → PO-Synthese]` Symbiose-Vorschläge nach Aufwand: C1 Telegram-Echo `[LEICHTE-FRUCHT][MVP-2]`; C2 Discord-Wochen-Replay `[GROSSE-IDEE][MVP-3]` (gekoppelt an ENT-045/049); C3 RenderDict-Vertrag `[MITTLERE-IDEE][MVP-3]` als Vorbereitung für künftige Renderer — `02_ux.md §Teil C`.
- `[Architekt → QM]` Sensitivity-Pfade für C6 (Multi-Modal) — `03_architect.md §A1 (01 §C6)` + `§B6` + `handover_03_architect_to_qm.md §Prüfpunkt 1` — Default-Tier `sensitive` für Bilder; ohne ENT bricht ENT-006 sobald C6 live geht.
- `[Architekt → QM]` Test-Lücken für B3/B4/B6/B9 — `03_architect.md §D4` + `handover §Prüfpunkt 3` — heute keine `tests/`-Struktur; Migrations-Idempotenz-Test ist P1.
- `[Architekt → QM]` Inkonsistenz-Befunde aus Pflichtlektüre — `03_architect.md §C3` (vier `(?)…(?)`-Befunde) + `handover §Prüfpunkt 5` — `graph_writer.py:55-65` Branch-Bug, `WIKI_PAGE_THRESHOLD` 30-vs-150, `index_updater`-Phantom, Draft-Branch dormant.
- `[Architekt → PO-Synthese]` ENT-Bedarf in 6 Punkten: IPA-Schema (§A1 [02 §B5]), Sensitivity für Bilder (§A1 [01 §C6]), `out/anki_export_log.json` als Persistenz-Pfad (§A1 [01 §C5]), `WIKI_PAGE_THRESHOLD`-Korrektur in ARCHITECTURE.md (§C1), `graph_writer.py`-Branch-Fix als Schuld in `hinweise/technischer_hinweis.md` (§C3), Draft-Branch-Status-Beschluss (§D5).
- `[Architekt → PO-Synthese]` Implementierungs-Reihenfolge — `03_architect.md §Implementierungs-Reihenfolge` — 8 MVP-2-Zweitwellen-Schritte (~39h Architekt-Aufwand) + 1 MVP-3-Backlog. PO darf priorisieren, aber nicht ohne Abhängigkeiten zu adressieren.
- `[Architekt → Architekt-Folge]` neue COMP-Spec-Kandidaten — `03_architect.md §C2` — `doc/COMP_RENDER.md` (empfohlen), `doc/COMP_LINT.md` (empfohlen), `doc/COMP_INDEX.md` (optional).
- `[QM → PO-Synthese]` Meilenstein-Urteil "Synthese mit Auflagen" — `04_qm.md §C2` + `handover_04_qm_to_po.md §Meilenstein-Urteil` — fünf Auflagen: QK-8 (Frontmatter-Migration mit drei Pflicht-Auflagen), QK-9 (Sensitivity-ENT vor C6), R1 (graph_writer-Fix als Schritt 0), QK-14 (Test-Strategie als Pre-Req), Reihenfolge-Treue der acht Workshop-Schritte.
- `[QM → PO-Synthese]` Vier P1-Befunde — `04_qm.md §B1` — R1 (`graph_writer.py:55-65` Branch-Bug, QM-im-Code-verifiziert), R2 (C4 destruktive Migration mit `anki_id`-Erhaltungspflicht), R3 (Sensitivity-ENT für Bilder vor C6), R4 (Test-Strategie etablieren).
- `[QM → PO-Synthese]` Sieben QK-Vorschläge (QK-8 bis QK-14) — `04_qm.md §C1` — Frontmatter-Migration-Auflagen, Sensitivity-Tier für Bilder, Health-Tag-Persistenz, Render-Modul-Standort `agents/render/`, ARCHITECTURE.md-Threshold-Korrektur, Draft-Branch formale Pause, Test-Strategie etablieren.
- `[QM → PO-Synthese]` ENT-Bedarfs-Liste — `handover_04_qm_to_po.md §ENT-Bedarfs-Liste` — drei ENT-NEU-Vorschläge (Sensitivity Bilder, `out/anki_export_log.json`, IPA-Schema) + zwei ENT-Updates (ENT-007 Pause, ENT-027 Doku-Konsistenz-Bestätigung).
- `[QM → PO-Synthese]` Anti-Decisions-Empfehlungen — `handover_04_qm_to_po.md §Anti-Decisions-Empfehlungen` — Karpathy bleibt, Discord+C7 bleiben MVP-3-Backlog, C5b bleibt abgelehnt, AnkiConnect-Eintrag in `hinweise/technischer_hinweis.md` streichen (obsolet seit ENT-050).
- `[QM → PO-Synthese]` Aktualisierungs-Vorschlag für `hinweise/technischer_hinweis.md` — `04_qm.md §Aktualisierungs-Vorschlag` — acht neue Schulden (vom Workshop aufgedeckt) + sechs behobene + ein zu streichender (AnkiConnect).
- `[QM → QM-Folge]` Bonus-Inkonsistenz aus QM-Pflichtlektüre — `04_qm.md §A2 K5` + `§B3 R16` — `agents/graph_reader.py` Header-Kommentar Z.3-4 sagt "150", Konstante Z.20 sagt "30" (interne Datei-Inkonsistenz, vom Architekten nicht gemeldet, vom QM gefunden).

---

## Veto-/ENT-Marker (vom Architekt während Phase 3)

> Format: `[Quell-File:Sektion] (!)ARCH-VETO/ENT-NÖTIG/ARCH-FRAGE(!) — [Begründung kurz, Detail in 03_architect.md §X]`

- `[01_ai_research.md §C4]` (!)ARCH-FRAGE(!) — Migration schreibt direkt auf `wiki/`; Verhältnis zu Draft→Master-Workflow (ENT-007). Detail in `03_architect.md §A1 [01 §C4]`.
- `[01_ai_research.md §C5]` (!)ENT-NÖTIG(!) — Persistenz-Ort des `last_export`-Zeitstempels: `out/anki_export_log.json` vs. `usage_stats:` im Wiki-Frontmatter. Architekt-Empfehlung: `out/`. Detail in `03_architect.md §A1 [01 §C5]`.
- `[01_ai_research.md §C6]` (!)ENT-NÖTIG(!) — Sensitivity-Tier-Verhältnis (ENT-006) für Bild-Inputs ungeklärt; Vision-API ist Cloud, ohne PII-Stripping bricht `private`-Tier. Detail in `03_architect.md §A1 [01 §C6]`.
- `[02_ux.md §B5]` (!)ENT-NÖTIG(!) — IPA-Slot ist Schema-Erweiterung in SCHEMA.md §3.2 (`[ENT-NEU?]` für PO-Synthese). Detail in `03_architect.md §A1 [02 §B5 IPA]`.
- `[02_ux.md §B5]` (!)ARCH-FRAGE(!) — Render-Modul-Standort `scripts/` vs. `agents/render/` — sobald Multi-Konsumenten dazukommen ist `scripts/`-Imports aus dem Bot ein Smell. Architekt-Empfehlung: `agents/render/`. Detail in `03_architect.md §A1 [02 §B5 Modul]`.
- `[02_ux.md §C1]` (!)ARCH-FRAGE(!) — Bot-Token paralleler Send aus CLI-Skript vs. laufendem Long-Polling. Architekt-Verdict: kein Konflikt (sendMessage ist multi-client). Detail in `03_architect.md §A1 [02 §C1]`.

---

## QM-Risiko-Snapshot (Phase 4)

> Format: `[Quell-File:Sektion] [P1/P2/P3] — [Risiko kurz, Detail in 04_qm.md §X]`

**P1 — Blocker für MVP-2-Zweitwellen-Implementierung (Mitigation klar):**

- `[03_architect.md §C3 K1]` **[P1 R1]** — `agents/graph_writer.py:55-65` schreibt `git checkout main` + `git branch -D draft`, Branch ist `master` ([ENT-039](../doc/ENTSCHEIDUNGEN.md#ent-039-branch-namen-konvention-master-vs-main)). QM-im-Code-verifiziert. Doppelfehler (Code + Doc-Strings, drei Stellen). Mitigation: Schritt 0 in Implementierungs-Session 026. Detail in `04_qm.md §B1 R1`.
- `[03_architect.md §B4]` **[P1 R2]** — C4 Frontmatter-Migration ist destruktiv auf 7 elaborierten Vocab-Files; `anki_id`-Erhaltung ist nicht-reparabel bei Bruch ([ENT-052](../doc/ENTSCHEIDUNGEN.md#ent-052-anki-card-identität-und-re-export-stabilität)). Mitigation: drei Pflicht-Auflagen (Backup-Branch + Idempotenz-Test + `anki_id`-Hash-Snapshot, siehe QK-8). Detail in `04_qm.md §B1 R2`.
- `[03_architect.md §A1 [01 §C6]]` **[P1 R3]** — C6 Multi-Modal bricht [ENT-006](../doc/ENTSCHEIDUNGEN.md#ent-006-sensitivity-tier-modell-provider-routing) ohne Tier-Default für Bilder. Mitigation: Pre-Req ENT-NEU mit Default `sensitive` + Quick-Save ohne Hint (QK-9). Detail in `04_qm.md §B1 R3`.
- `[03_architect.md §D4]` **[P1 R4]** — `tests/`-Struktur fehlt komplett; vier destruktive Workshop-Schritte (C4, C3, C6, Render-Refactor) brauchen Test-Pattern vor Live-Schalten. Mitigation: Test-Skelett als Pre-Implementierungs-Schritt (QK-14). Detail in `04_qm.md §B1 R4`.

**P2 — wichtig, mitziehen in Implementierungs-Session:**

- `[03_architect.md §B1]` **[P2 R5]** — C1 Index-Reparatur: Fixture-Test gegen kaputten Index Pflicht.
- `[03_architect.md §B9+B10]` **[P2 R6]** — Render-Modul + RenderDict: Snapshot-Tests Pflicht.
- `[03_architect.md §B5]` **[P2 R7]** — C5a Health-Tag: Re-Export-Idempotenz, abhängig von R10/QK-10.
- `[03_architect.md §B3]` **[P2 R8]** — C3 Lint-Auto-Fixes: Before/After-Fixture-Trees Pflicht; abhängig von R9/QK-13.
- `[03_architect.md §C3 K4]` **[P2 R9]** — Draft→Master-Status-Beschluss (Pause vs. Re-Aktivierung); QM-Empfehlung: formale Pause (QK-13).
- `[03_architect.md §A1 [01 §C5]]` **[P2 R10]** — Persistenz-ENT für `last_export`-Zeitstempel; Architekt-Empfehlung `out/anki_export_log.json` (QK-10).
- `[03_architect.md §A1 [02 §B5 IPA]]` **[P2 R11]** — IPA-Schema-Erweiterung als `[ENT-NEU?]`.

**P3 — technische Schuld, dokumentieren, nicht blockieren:**

- `[03_architect.md §B11]` **[P3 R12]** — Telegram-Echo nach Anki-Export: Smoke-Send reicht.
- `[03_architect.md §B2]` **[P3 R13]** — SQLite-FTS5-Build-Skript: pre-emptiv, Pre-Req QK-12.
- `[03_architect.md §C3 K2]` **[P3 R14]** — `WIKI_PAGE_THRESHOLD` ARCHITECTURE.md §6.3 auf `30` korrigieren.
- `[03_architect.md §C3 K3]` **[P3 R15]** — `index_updater`-Phantom in ARCHITECTURE.md §6.1: Status-Hinweis-Update.
- **[QM-Bonus]** **[P3 R16]** — [graph_reader.py:3-4](../agents/graph_reader.py#L3-L4) Header-Kommentar sagt "150", Z.20 sagt "30" — interne Datei-Inkonsistenz, vom QM frisch entdeckt.
- `[03_architect.md §B6]` **[P3 R17]** — C6 Multi-Modal-Backfill: E2E-Test Pflicht; gekoppelt an R3.
- `[03_architect.md §D2]` **[P3 R20]** — `scripts/migrations/`-Pattern + `applied.json` mit C4 etablieren.
- `[03_architect.md §D3]` **[P3 R21]** — `scripts/graph_stats.py` Wachstums-Telemetrie.
- `[03_architect.md §D6]` **[P3 R22]** — `agents/frontmatter.py`-Helper-Konsolidierung.

**OK — kann mitlaufen / Backlog:**

- `[03_architect.md §B8]` **[OK R18]** — C8 User-Profile Self-Refresh, Append-Diff-Mitigation, ~$0,20/Monat.
- `[03_architect.md §D1]` **[P2 R19]** — SHA1-Asset-Dedup (gekoppelt an C6).

**[NICHT-MVP-2]:**

- `[03_architect.md §B7]` **[R23]** — C7 Concept-Cluster, dispatch ≥50 PFs.
- `[03_architect.md §B12]` **[R24]** — UX-C2 Discord-Wochen-Replay, gekoppelt an [ENT-045](../doc/ENTSCHEIDUNGEN.md#ent-045-proaktiver-kanal-grundsätzlich-freigegeben-opt-in)-Aktivierung.

---

## PO-Verdicts (Phase 5)

> Format: `[Backlog-ID] [angenommen/abgelehnt/verschoben] — [Begründung kurz, Detail in 05_po_synthesis.md §X]`

_(noch leer)_

---

## Status

- Ausgerufen: 2026-05-08
- Aktuelle Phase: 4 abgeschlossen (QM, 2026-05-08) — Phase 5 (PO-Synthese) startbereit
- Meilenstein-Urteil (QM): **Synthese mit Auflagen** — vier P1-Befunde alle heilbar in 05, fünf Pflicht-Auflagen.
- Nächster Schritt: PO startet PO-Synthese-Session mit [prompts/05_po_synthesis_prompt.md](prompts/05_po_synthesis_prompt.md). PO liest [04_qm.md](04_qm.md) + [handovers/handover_04_qm_to_po.md](handovers/handover_04_qm_to_po.md) als erstes; arbeitet ENT-NEU-Liste, Anti-Decisions, Reihenfolge ab.
