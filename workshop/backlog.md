# Workshop-Backlog: MVP-2-Zweitwelle + MVP-3-Vorbereitung
> Erstellt: 2026-05-08, durch Product Owner | Workshop-Phase 5 (PO-Synthese) | Quelle: [05_po_synthesis.md](05_po_synthesis.md)
> Format pro Eintrag: Priorität · Aufwand · Quelle · Architekt-Status · QM-Status · Bezug ENT · Definition of Done · vorgesehene Rolle · vorgesehene MVP-Stufe

**Sortierung:** P1 zuerst, P2, P3, Radar. Innerhalb gleicher Klasse: nach Aufwand aufsteigend.

**Reihenfolge-Treue:** Implementierungs-Reihenfolge ist scharf — siehe [05_po_synthesis.md §7](05_po_synthesis.md). Innerhalb gleicher Priorität ist die Aufwand-Sortierung dieser Datei kein Reihenfolge-Mandat.

---

## BL-01: graph_writer.py-Branch-Bug-Fix (`main` → `master`)
- **Priorität:** P1
- **Aufwand:** ~30 Minuten
- **Quelle:** [03_architect.md §C3 K1](03_architect.md), [04_qm.md §B1 R1](04_qm.md), QM-im-Code-verifiziert
- **Architekt-Status:** [MACHBAR] — trivialer Fix, drei Strings + zwei Doc-Strings in [agents/graph_writer.py:45-65](../agents/graph_writer.py#L45-L65)
- **QM-Status:** P1 / kein direkter Test-Block. Smoke-Test: `reject_draft()` aufrufen, prüfen `git rev-parse master` succeeds. Risiko: schlafende Mine — wird akut sobald Lint-Live (BL-07) `reject_draft` triggert.
- **Bezug ENT:** kein neuer ENT — bestätigt [ENT-039](../doc/ENTSCHEIDUNGEN.md#ent-039-branch-namen-konvention-master-vs-main).
- **Definition of Done:**
  1. `agents/graph_writer.py:55-65` schreibt `git checkout master` und `git checkout -b draft` (statt `main`).
  2. Doc-Strings in Z.46 und Z.55 referenzieren `master`, nicht `main`.
  3. Smoke-Test in `tests/test_graph_writer_branch.py` (oder gleichwertig) prüft, dass `reject_draft()` ohne Branch-Fehler durchläuft.
  4. `hinweise/technischer_hinweis.md`-Eintrag für diese Schuld wird mit dem Fix entfernt.
- **Vorgesehene Rolle:** Architekt
- **Vorgesehene MVP-Stufe:** **MVP-2.5 (Cleanup)** — Schritt 0 der Implementierungs-Session 026.

---

## BL-02: Test-Skelett anlegen (`tests/`-Struktur + pytest-Setup)
- **Priorität:** P1
- **Aufwand:** ~1–2 Stunden
- **Quelle:** [03_architect.md §D4](03_architect.md), [04_qm.md §B1 R4](04_qm.md), [04_qm.md §C1 QK-14](04_qm.md)
- **Architekt-Status:** [MACHBAR]
- **QM-Status:** P1 / Pre-Req für jede destruktive Workshop-Migration (BL-03, BL-07, BL-08). Pflicht-Pattern: `tests/migrations/`, `tests/lint/`, `tests/render/`, `tests/multimodal/`.
- **Bezug ENT:** kein ENT — Engineering-Konvention.
- **Definition of Done:**
  1. `tests/` mit `__init__.py` und Unter-Ordnern `migrations/`, `lint/`, `render/`, `multimodal/`.
  2. `requirements.txt` ergänzt um `pytest>=7.0`, `pytest-snapshot>=0.9`.
  3. Mindestens ein Smoke-Test pro Unter-Ordner (kann anfangs trivial sein), `pytest tests/` läuft lokal grün.
  4. README-Eintrag oder Block-Kommentar in `tests/__init__.py` mit Konventions-Beschreibung (Fixture-Layout, Snapshot-Ablage).
- **Vorgesehene Rolle:** Architekt
- **Vorgesehene MVP-Stufe:** **MVP-2.5 (Cleanup)** — Schritt 0b der Implementierungs-Session 026.

---

## BL-03: Frontmatter-Migration (C4) — 7 elaborierte Vocab-Files
- **Priorität:** P1
- **Aufwand:** ~3 Stunden (2h Migration + 1h Code-Fix in `language_agent.py`)
- **Quelle:** [03_architect.md §B4](03_architect.md), [01_ai_research.md §C4](01_ai_research.md), [04_qm.md §B1 R2 / §C1 QK-8](04_qm.md)
- **Architekt-Status:** [MACHBAR] — pyyaml-Roundtrip auf 7 Files; bestehender Regex-Workaround als Reader, sauberes YAML als Writer.
- **QM-Status:** P1 destruktiv. **Drei Pflicht-Auflagen:** (a) Backup-Branch `backup/pre-frontmatter-migration` zwingend vor Lauf; (b) Idempotenz-Test (zweiter Lauf = 0 Diffs); (c) `anki_id`-Hash-Snapshot vor + nach Migration, gleicher Hash Pflicht.
- **Bezug ENT:** kein neuer ENT — analog `anki_id`-Patch ([ENT-052](../doc/ENTSCHEIDUNGEN.md#ent-052-anki-card-identität-und-re-export-stabilität)) als deterministischer Direct-Master-Write legitim. ENT-056 deckt Direct-Write-Pause des Draft-Workflows.
- **Definition of Done:**
  1. `scripts/migrations/2026-05-09_frontmatter_yaml.py` (bzw. tatsächliches Datum) — pyyaml-Roundtrip für 7 elaborierte Vocab-Files.
  2. Backup-Branch `backup/pre-frontmatter-migration` exists vor Lauf (Pflicht-Check im Skript).
  3. `agents/language_agent.py:423-459` `_build_frontmatter()` per `yaml.dump` statt f-string-dedent.
  4. `tests/migrations/fixtures/before/`, `after/` mit den 7 Files; `anki_id`-Hash-Snapshot in JSON.
  5. Pytest-Run `tests/migrations/test_frontmatter_yaml.py` grün — inkl. Idempotenz (zweiter Lauf 0 Diffs) + `anki_id`-Erhaltung.
  6. `agents/frontmatter.py`-Helper als Konsolidierung der heute drei Implementierungen ([03 §D6](03_architect.md)) — zumindest skelett, ausgebaut in BL-04.
  7. `scripts/migrations/applied.json` mit Datums-Eintrag.
- **Vorgesehene Rolle:** Architekt
- **Vorgesehene MVP-Stufe:** **MVP-2.5 (Cleanup)** — Schritt 1 der Implementierungs-Session 026, **Top-1-Backlog-Item**.

---

## BL-04: C1 Index-Reparatur + `agents/frontmatter.py`-Helper-Konsolidierung
- **Priorität:** P1
- **Aufwand:** ~4 Stunden (3h Skript + 1h einmaliger Sonnet/Haiku-Pass über 21 Pages)
- **Quelle:** [03_architect.md §B1](03_architect.md), [01_ai_research.md §C1](01_ai_research.md), [04_qm.md §B2 R5](04_qm.md)
- **Architekt-Status:** [MACHBAR-BEDINGT: Pre-Req BL-03 (sonst pyyaml-Verweigerung auf 7 Vocab-Files)]
- **QM-Status:** P2-im-Backlog, hier P1 wegen Hebel auf Retrieval-Qualität (löst L2 + L3 in [01 §A3](01_ai_research.md)). Test gegen Fixture mit kaputtem Index. Kosten: einmalig ~$0,21 (Sonnet/Haiku-Pass für 21 Summaries).
- **Bezug ENT:** kein neuer ENT — Indexierung war bereits in [ARCHITECTURE.md §6.1](../doc/ARCHITECTURE.md#61-graph-struktur-ingestion-flow) angelegt (`index_updater`-Phantom). Doku-Korrektur (`index_updater`-Status klarstellen) gehört zu BL-11.
- **Definition of Done:**
  1. `scripts/rebuild_index.py` walkt `wiki/**/*.md`, liest Frontmatter, rendert one-line summary; falls `summary:` fehlt → einmaliger Sonnet/Haiku-Pass füllt es nach.
  2. `agents/frontmatter.py` als Single-Source-Helper für `read`/`write`/`patch` — alle drei heutigen Implementierungen (export_anki.py:79-98, language_agent.py:423-459, neues rebuild_index.py) nutzen ihn.
  3. `index.md` deckt sich nach Lauf mit Filesystem-Glob (Drift = 0).
  4. `tests/lint/index_fs_sync/` Fixture mit kaputtem Index → Skript-Lauf → Erwartung: Drift = 0, `summary`-Felder gefüllt.
  5. Idempotenz: zweiter Lauf 0 LLM-Calls (Frontmatter `summary` schon gefüllt).
- **Vorgesehene Rolle:** Architekt
- **Vorgesehene MVP-Stufe:** **MVP-2.5 (Cleanup)** — Schritt 2 der Implementierungs-Session 026.

---

## BL-05: Render-Modul `agents/render/card.py` + `RenderDict`-Vertrag
- **Priorität:** P2
- **Aufwand:** ~9 Stunden (6h Modul + Profile + Tests + 3h `RenderDict`-Adapter)
- **Quelle:** [02_ux.md §B1/B5](02_ux.md), [02_ux.md §C3](02_ux.md), [03_architect.md §B9+B10](03_architect.md), [04_qm.md §B2 R6](04_qm.md), [04_qm.md §C1 QK-11](04_qm.md)
- **Architekt-Status:** [MACHBAR] — `agents/render/__init__.py` + `agents/render/card.py` (`render_front`, `render_back`, `pick_profile`, `CSS_BLOCK`), `scripts/export_anki.py` als dünner CLI-Wrapper.
- **QM-Status:** P2 Refactor, Snapshot-Tests Pflicht (4 Profile A/B/C/D mit erwartetem HTML).
- **Bezug ENT:** kein ENT — Modul-Hygiene-Frage, fällt unter Architekt-Autorität (gemäß Rollen-Kopf).
- **Definition of Done:**
  1. Neues Modul `agents/render/card.py` mit den vier Funktionen + CSS-Block aus [02 §B3](02_ux.md).
  2. `RenderDict`-Dataclass (`@dataclass(frozen=True)`) mit Sektionen `identity`/`content`/`display`/`links` ([02 §C3](02_ux.md)-Schema).
  3. `vocab_record_to_render_dict(rec) -> RenderDict`-Adapter.
  4. `scripts/export_anki.py` importiert aus `agents.render.card`, behält Pipeline (Walk → Filter → Genanki-Build → Frontmatter-Patch).
  5. `tests/render/`-Snapshot-Tests pro Profil: `escribir` (A), `mariposa` (B mit `la`), `duende` (C mit Mnemonic), Verb mit Konjugations-Notiz (D, falls vorhanden — sonst Fallback A getestet).
  6. Mobile-Fallback `backlink-path` als Klartext-zweite-Zeile gerendert ([02 §B6](02_ux.md), nicht-verhandelbar).
- **Vorgesehene Rolle:** Architekt
- **Vorgesehene MVP-Stufe:** **MVP-3** (Vorbereitung) — Schritt 3 der Implementierungs-Session 026.

---

## BL-06: C5a Health-Tag (`health::stale-mnemonic`) + Telegram-Echo nach Anki-Export
- **Priorität:** P2
- **Aufwand:** ~5 Stunden (3h Health-Tag + 2h Telegram-Echo)
- **Quelle:** [01_ai_research.md §C5](01_ai_research.md), [02_ux.md §C1](02_ux.md), [03_architect.md §B5+B11](03_architect.md), [04_qm.md §B2 R7](04_qm.md), [04_qm.md §C1 QK-10](04_qm.md)
- **Architekt-Status:** [MACHBAR-BEDINGT: nach BL-03] — Persistenz `out/anki_export_log.json`, Granularität YYYY-MM-DD.
- **QM-Status:** P2, abhängig von ENT-054 (siehe `doc/ENTSCHEIDUNGEN.md`). Re-Export-Idempotenz-Test Pflicht.
- **Bezug ENT:** **ENT-054** in `doc/ENTSCHEIDUNGEN.md` (`out/anki_export_log.json` als Persistenz-Pfad, vom PO in dieser Session 025 angelegt).
- **Definition of Done:**
  1. `out/anki_export_log.json` wird beim Export gelesen/geschrieben (`{slug: last_export_iso}`).
  2. Vergleich `frontmatter.updated > log[slug]` → Anki-Tag `health::stale-mnemonic` setzen.
  3. `scripts/export_anki.py --notify-telegram` sendet Inline-Vorschau ([02 §C1 Mockup](02_ux.md)) via Bot-Token aus `.env`.
  4. `tests/render/test_health_tag.py` — Mock-Log-Eintrag + VocabRecord, Tag-Vergabe deterministisch.
  5. Smoke-Send-Test für Telegram-Echo (Mock-Bot oder Live-Test, abhängig von CI-Setup).
- **Vorgesehene Rolle:** Architekt
- **Vorgesehene MVP-Stufe:** **MVP-3** (Vorbereitung) — Schritt 4 der Implementierungs-Session 026.

---

## BL-07: C3 Lint-Auto-Fixes (3 Detektoren: Backlink-Symmetrie, Index-Sync, Slug-Dedup)
- **Priorität:** P2
- **Aufwand:** ~6 Stunden (3 Detektoren + Fixture-Tests)
- **Quelle:** [03_architect.md §B3](03_architect.md), [01_ai_research.md §C3](01_ai_research.md), [04_qm.md §B2 R8](04_qm.md)
- **Architekt-Status:** [MACHBAR] — drei Detektoren in [agents/lint_agent.py](../agents/lint_agent.py), keine LLM-Calls (außer Telegram-Frage für Slug-Dedup-Vorschlag).
- **QM-Status:** P2 destruktiv (schreibt ins Wiki). **Pre-Req BL-03** (Backlink-Append schreibt in Frontmatter, das heute kaputt ist). Before/After-Fixture-Trees Pflicht.
- **Bezug ENT:** kein neuer ENT — ENT-056 (formale Pause ENT-007) macht Direct-Master-Write legitim. Reaktiviert Stub aus [ENT-017](../doc/ENTSCHEIDUNGEN.md#ent-017-lintagent-mit-auto-fix-stubs).
- **Definition of Done:**
  1. `LintAgent._fix_backlink_symmetry()` — Adjazenz-Vergleich, append in `related:` der Zielseite.
  2. `LintAgent._fix_index_fs_sync()` — Glob ↔ index.md, fehlende ergänzen, tote löschen.
  3. `LintAgent._detect_slug_dedup()` — SequenceMatcher ≥ 0.9 → Telegram-Frage via Buttons.
  4. `tests/lint/backlink_symmetry/before/` + `after/`, `tests/lint/index_fs_sync/`, `tests/lint/slug_dedup/` Fixtures.
  5. `LintAgent._apply_auto_fixes()` ist nicht mehr Stub.
  6. Eintrag in `hinweise/technischer_hinweis.md` "LintAgent._apply_auto_fixes() sind Stubs" entfernen.
- **Vorgesehene Rolle:** Architekt (Implementierung), PO (Telegram-Button-Wording-Review)
- **Vorgesehene MVP-Stufe:** **MVP-3** (Vorbereitung) — Schritt 5 der Implementierungs-Session 026.

---

## BL-08: C6 Multi-Modal-Backfill (Bilder/PDFs) + SHA1-Asset-Dedup
- **Priorität:** P2
- **Aufwand:** ~4 Stunden (3h Bot-Handler + 1h Tier-Plumbing + SHA-Dedup)
- **Quelle:** [03_architect.md §B6+§D1](03_architect.md), [01_ai_research.md §C6](01_ai_research.md), [04_qm.md §B1 R3 + §B3 R17+R19](04_qm.md)
- **Architekt-Status:** [MACHBAR-BEDINGT: nach ENT-053]
- **QM-Status:** P1-Block ohne ENT — bricht ENT-006 sobald live geht. Mit ENT-053 wird das auf P2. Pflicht-E2E-Test mit Bot-Handler-Mock + Hint-Gate-Test + SHA-Dedup-Test.
- **Bezug ENT:** **ENT-053** in `doc/ENTSCHEIDUNGEN.md` (Sensitivity-Tier-Default für Bilder, Quick-Save ohne Hint, Auto-Ingest mit `#bild` oder `#vision`-Hint).
- **Definition of Done:**
  1. `bot.py`-Handler für `MessageType.PHOTO` (`handle_photo`) und `MessageType.DOCUMENT` (`handle_document` für PDFs).
  2. Bild ohne Hint → Quick-Save in `raw/assets/`, kein `image_extractor`-Aufruf.
  3. Bild mit `#bild` oder `#vision` → `image_extractor.extract(dest, tier="sensitive")` → `raw/events/`-JSON wie heute Voice → normaler Ingest.
  4. SHA1-Asset-Dedup ([03 §D1](03_architect.md)): Datei-Hash → existiert bereits → kein neues Event, sondern Update.
  5. PDF-Pfad analog (lokal, kein Cloud-Call, Tier irrelevant).
  6. `tests/multimodal/test_image_handler.py` E2E mit Mock — Hint-Gate, Tier-Routing, SHA-Dedup, Doppel-Drop.
- **Vorgesehene Rolle:** Architekt
- **Vorgesehene MVP-Stufe:** **MVP-3** — Schritt 7 der Implementierungs-Session 026.

---

## BL-09: C2 SQLite-FTS5-Build-Skript (Phase-2-Vorbereitung)
- **Priorität:** P3
- **Aufwand:** ~4 Stunden (Schema + Walker + Smoke-Test gegen [graph_reader._search_sqlite](../agents/graph_reader.py#L207-L256))
- **Quelle:** [03_architect.md §B2](03_architect.md), [01_ai_research.md §C2](01_ai_research.md), [04_qm.md §B3 R13](04_qm.md)
- **Architekt-Status:** [MACHBAR-BEDINGT: nur sinnvoll nach BL-04 (Index repariert) und BL-11 (Threshold-Doku korrigiert)]
- **QM-Status:** P3 pre-emptiv. Phase-2-Stub ist heute ungetestet — frühe Test-Validierung ist günstiger als späte Reparatur.
- **Bezug ENT:** kein neuer ENT — bestätigt [ENT-027](../doc/ENTSCHEIDUNGEN.md#ent-027-graph_reader-zweiphasig-qk-4) (Threshold `30` ist führend).
- **Definition of Done:**
  1. `scripts/build_wiki_index.py` baut `out/wiki_index.db` mit FTS5-Virtual-Table (`wiki_fts(slug, type, summary, body, tags)`).
  2. Walker iteriert `wiki/**/*.md`, parst Frontmatter via `agents/frontmatter.py`-Helper.
  3. Smoke-Test: `graph_reader._search_sqlite()` läuft gegen die DB grün, liefert sinnvolle BM25-Ranking-Treffer.
  4. Trigger-Setup (auto-Re-Build bei Wiki-Änderung) bleibt **bewusst weggelassen** — manueller Re-Build im Cron oder via `rebuild_index.py`-Hook.
  5. `WIKI_PAGE_THRESHOLD` bleibt bei `30`; FTS5 wird heute (21 Pages) nicht aktiv geschaltet, nur das Build-Skript existiert.
- **Vorgesehene Rolle:** Architekt
- **Vorgesehene MVP-Stufe:** **MVP-3+** (pre-emptiv) — Schritt 6 der Implementierungs-Session 026.

---

## BL-10: C8 User-Profile Self-Refresh (wöchentlicher Lint-Pass)
- **Priorität:** P3
- **Aufwand:** ~4 Stunden + ~$0,20/Monat LLM-Kosten
- **Quelle:** [03_architect.md §B8](03_architect.md), [01_ai_research.md §C8](01_ai_research.md), [04_qm.md §B4 R18](04_qm.md)
- **Architekt-Status:** [MACHBAR-BEDINGT: nach BL-07 (Lint-Live)]
- **QM-Status:** OK / Backlog. Append-Diff-Mitigation reicht. Sonnet-OK bestätigt (interner Lint-Pass, nicht ENT-045-tangiert).
- **Bezug ENT:** kein neuer ENT — bestätigt [ARCHITECTURE.md §3.4 Supervisor-als-Nutzer-Anwalt](../doc/ARCHITECTURE.md#34-supervisor-als-nutzer-anwalt).
- **Definition of Done:**
  1. `LintAgent.refresh_user_profile()` — Walk `wiki/personal/facts/`, aggregiert Sprach-Verteilung, Themen-Cluster, story_score-Statistiken.
  2. Sonnet-Call refresh `user_profile.md` einmal pro Woche, ~$0,05/Lauf.
  3. **Append-Diff statt Overwrite** — `telegram_state:`-Block ([ENT-043](../doc/ENTSCHEIDUNGEN.md#ent-043-telegram_state-architektur-option-a-feld-in-user_profilemd)) wird nicht überschrieben.
  4. `tests/lint/test_profile_refresh.py` — Mock-Facts → erwarteter Diff-Append.
- **Vorgesehene Rolle:** Architekt
- **Vorgesehene MVP-Stufe:** **MVP-3+** (optional) — Schritt 8 der Implementierungs-Session 026.

---

## BL-11: ARCHITECTURE.md + graph_reader.py Doku-Konsistenz
- **Priorität:** P3
- **Aufwand:** ~30 Minuten (drei kleine Edits)
- **Quelle:** [03_architect.md §C1+§C3 K2/K3](03_architect.md), [04_qm.md §B3 R14/R15/R16](04_qm.md), [04_qm.md §C1 QK-12](04_qm.md)
- **Architekt-Status:** [MACHBAR] — Doku-Korrektur, kein Code-Logik-Eingriff.
- **QM-Status:** P3 / Doku-Schuld. Konsistenz mit [ENT-027](../doc/ENTSCHEIDUNGEN.md#ent-027-graph_reader-zweiphasig-qk-4) herstellen.
- **Bezug ENT:** kein neuer ENT — bestätigt ENT-027 (Threshold `30` führend).
- **Definition of Done:**
  1. `doc/ARCHITECTURE.md §6.3` `WIKI_PAGE_THRESHOLD` von `150` auf `30` korrigieren.
  2. `agents/graph_reader.py:3-4` Header-Kommentar von "(< 150 wiki pages)" auf "(< 30 wiki pages)" korrigieren.
  3. `doc/ARCHITECTURE.md §6.1` `index_updater`-Node mit Status-Hinweis ergänzen: "*Index-Updater wird heute durch `scripts/rebuild_index.py` realisiert (siehe BL-04, Workshop S025).*"
  4. Optional: neue **§11 Render-Layer**-Sektion mit Modul-Standort, `RenderDict`-Vertrag, Multi-Konsumenten-Plan ([03 §C1.3](03_architect.md)). Architekt-Empfehlung — PO offen, ob als Sektion oder als `doc/COMP_RENDER.md`-Spec ([03 §C2](03_architect.md)).
- **Vorgesehene Rolle:** Architekt (oder PO bei reiner Doku-Korrektur ohne Code-Bezug)
- **Vorgesehene MVP-Stufe:** **MVP-2.5 (Cleanup)** — kann mit BL-04 oder BL-09 mitlaufen.

---

## BL-12: `scripts/migrations/`-Pattern + `applied.json`-Log
- **Priorität:** P3
- **Aufwand:** ~1 Stunde (mit BL-03 etablieren)
- **Quelle:** [03_architect.md §D2](03_architect.md), [04_qm.md §B3 R20](04_qm.md)
- **Architekt-Status:** [MACHBAR] — Konvention + JSON-Log, kein Tool-Bau nötig.
- **QM-Status:** P3 / dokumentarisch. Schützt vor Doppel-Anwendung auf neuen Geräten.
- **Bezug ENT:** kein ENT — Engineering-Konvention.
- **Definition of Done:**
  1. `scripts/migrations/`-Ordner mit Datums-Präfix-Konvention (`YYYY-MM-DD_<thema>.py`).
  2. `scripts/migrations/applied.json` mit `{filename: applied_iso}`-Map.
  3. README-Block am Ordner-Anfang oder in `scripts/migrations/__init__.py` mit Konvention dokumentiert.
  4. BL-03 (Frontmatter-Migration) ist erste Migration unter dieser Konvention.
- **Vorgesehene Rolle:** Architekt
- **Vorgesehene MVP-Stufe:** **MVP-2.5 (Cleanup)** — mit BL-03.

---

## BL-13: `scripts/graph_stats.py` Wachstums-Telemetrie
- **Priorität:** Radar
- **Aufwand:** ~2 Stunden
- **Quelle:** [03_architect.md §D3](03_architect.md), [04_qm.md §B3 R21](04_qm.md)
- **Architekt-Status:** [MACHBAR] — kein LLM, deterministisch, ~50 Zeilen Python.
- **QM-Status:** P3 / präventiv. Niedrige Priorität, hoher Wert. Voraussetzung für künftige ENT-027-Phase-Switch-Validierung.
- **Bezug ENT:** kein ENT.
- **Definition of Done:**
  1. `scripts/graph_stats.py` läuft optional wöchentlich; Output `out/graph_stats_YYYY-WW.json` mit Counts pro Entitäts-Typ, Drift-Flag, Phase-Empfehlung.
  2. Smoke-Test: einmaliger Lauf, Output-File existiert mit erwartetem Schema.
  3. Kein Cron, kein Auto-Trigger — manueller Lauf reicht in MVP-2-Zweitwelle.
- **Vorgesehene Rolle:** Architekt
- **Vorgesehene MVP-Stufe:** **MVP-3+** — kann auf Halde liegen, wird relevant wenn Korpus über 30 PFs wächst.

---

## Backlog-Stand: 13 Einträge

**Aufteilung:**
- P1: BL-01, BL-02, BL-03, BL-04 (4 Einträge — Schritte 0/0b/1/2)
- P2: BL-05, BL-06, BL-07, BL-08 (4 Einträge — Schritte 3/4/5/7)
- P3: BL-09, BL-10, BL-11, BL-12 (4 Einträge — Schritte 6/8 + Doku/Migration-Pattern)
- Radar: BL-13 (1 Eintrag — Telemetrie)

**Gesamt-Aufwand:** ~50 Stunden Architekt-Arbeit (inkl. ~30% Test-/Migrations-Overhead).

**Reihenfolge-Treue:** BL-01 → BL-02 → ENT-NEUs (in 05_po_synthesis-Lieferung erledigt) → BL-03 → BL-04 → BL-05 → BL-06 → BL-07 → BL-09 → BL-08 → BL-10. **BL-11 und BL-12 begleitend** (mit BL-04 oder BL-03). **BL-13 Radar** (kein Trigger heute).

**Top-1-Backlog-Item für Implementierungs-Session 026:** **BL-03 Frontmatter-Migration** (nach Schritt 0/0b/0c als Vorbereitung). Adressat: Architekt. Brief: [sessions/026_2026-05-09.md](../sessions/026_2026-05-09.md).

**Was nicht im Backlog steht (Radar, in `doc/CHANCEN.md`):**
- C7 LazyGraphRAG-Concept-Cluster — Trigger ≥50 PFs
- UX-C2 Discord-Wochen-Replay — Trigger ENT-045-Aktivierung + MVP-3-Scope
- E2E-Pipeline-Tests für Bot-Handler — Trigger BL-08-Live
