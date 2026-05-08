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
| 4 | QM | _TBD_ | _TBD_ | [04_qm.md](04_qm.md) | PO |
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

_(noch leer)_

---

## PO-Verdicts (Phase 5)

> Format: `[Backlog-ID] [angenommen/abgelehnt/verschoben] — [Begründung kurz, Detail in 05_po_synthesis.md §X]`

_(noch leer)_

---

## Status

- Ausgerufen: 2026-05-08
- Aktuelle Phase: 3 abgeschlossen (Architekt, 2026-05-08) — Phase 4 (QM) startbereit
- Nächster Schritt: PO startet QM-Session mit [prompts/04_qm_prompt.md](prompts/04_qm_prompt.md). QM liest [03_architect.md](03_architect.md) + [handovers/handover_03_architect_to_qm.md](handovers/handover_03_architect_to_qm.md) als erstes; arbeitet sechs Architekt-Prüfpunkte ab (Sensitivity, Budget, Tests, Idempotenz, Inkonsistenzen, Reihenfolge).
