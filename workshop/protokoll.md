# Workshop-Protokoll (Spine)
> Index aller Workshop-Beiträge. Jede Rolle ergänzt **eine Zeile** in der Beitrags-Tabelle und Querverweise/Marker in den darunter stehenden Sektionen.
> Die Detail-Inhalte stehen in den jeweiligen Rollen-Files (01–05). Hier nur Index + Verweise.

---

## Beitrags-Index

| # | Rolle | Datum | Kern-Befunde (max 3, sehr kurz) | Detail-File | Handover an |
|---|---|---|---|---|---|
| 1 | AI-Research | 2026-05-08 | (1) Index-Drift + Slug-Summaries blocken Retrieval; (2) Frontmatter-Schuld blockt alle künftigen Konsumenten; (3) Lint-Stub heißt: keine Konsolidierung. | [01_ai_research.md](01_ai_research.md) | UX |
| 2 | UX | 2026-05-08 | (1) Ein Notetype, vier Slot-Profile (A/B/C/D); Template-first, LLM-second; (2) Render-Layer als eigenes Modul `scripts/render_card.py` empfohlen + `RenderDict`-Adapter-Vertrag für künftige Discord/E-Mail-Konsumenten; (3) Mobile-Backlink-Bruch bestätigt — Klartext-Pfad als zweite Zeile Pflicht; C5a (Health-Tag) angenommen, C5b (zweiter Backlink) abgelehnt. | [02_ux.md](02_ux.md) | Architekt |
| 3 | Architekt | _TBD_ | _TBD_ | [03_architect.md](03_architect.md) | QM |
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

---

## Veto-/ENT-Marker (vom Architekt während Phase 3)

> Format: `[Quell-File:Sektion] (!)ARCH-VETO/ENT-NÖTIG/ARCH-FRAGE(!) — [Begründung kurz, Detail in 03_architect.md §X]`

_(noch leer)_

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
- Aktuelle Phase: 2 abgeschlossen (UX, 2026-05-08) — Phase 3 (Architekt) startbereit
- Nächster Schritt: PO startet Architekt-Session mit [prompts/03_architect_prompt.md](prompts/03_architect_prompt.md). Architekt liest [02_ux.md](02_ux.md) + [handovers/handover_02_ux_to_architect.md](handovers/handover_02_ux_to_architect.md) als erstes; darf in [01_ai_research.md](01_ai_research.md) und [02_ux.md](02_ux.md) Veto-/ENT-Marker setzen.
