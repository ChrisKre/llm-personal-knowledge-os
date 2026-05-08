# 03 — Architekt: Machbarkeit + Vetos + Implementierungs-Skizzen
> Phase 3 von 5 | Erstellt: 2026-05-08 | Rolle: Senior System Architect | Modus: **Machbarkeit + Veto + Implementierungs-Skizze**
> Vor-Phasen: [01_ai_research.md](01_ai_research.md), [02_ux.md](02_ux.md). Folge-Phase: QM. Handover: [handovers/handover_03_architect_to_qm.md](handovers/handover_03_architect_to_qm.md).

---

## Zusammenfassung (max 5 Bullets)

- **Keine harten ARCH-VETOs.** Alle 01/02-Vorschläge sind Karpathy-konform und respektieren WikiWrite/ENT-006/ENT-039/Branch-master. Sechs Marker setze ich (3× ENT-NÖTIG, 3× ARCH-FRAGE) — Detail-Begründungen in §A.
- **Reihenfolge ist scharf:** **C4 (Frontmatter-Migration) → C1 (Index-Reparatur) → Render-Modul-Trennung (UX-B5) → Health-Tag (C5a) → Lint-Live (C3).** Jede Stufe entriegelt die nächste; vorzeitige Schritte erben den jeweils ungelösten Schmerz.
- **Architektur-Schulden, die der Workshop trifft, sind älter als der Workshop:** [graph_writer.py:55-65](../agents/graph_writer.py#L55-L65) verweist auf Branch `main` (verletzt ENT-039); `WIKI_PAGE_THRESHOLD = 30` in [graph_reader.py:20](../agents/graph_reader.py#L20) widerspricht [ARCHITECTURE.md §6.3](../doc/ARCHITECTURE.md#63-graph-reader--index-abstraktion) (`150`); `index_updater`-Node existiert im LangGraph-Plan, aber als Modul nicht im Repo. Diese drei sind keine Workshop-Themen, aber jeder neue Implementierungs-Pfad stolpert über sie.
- **`out/anki_export_log.json` schlägt `usage_stats:` im Wiki** für den Health-Tag-Zeitstempel: deterministischer Pfad außerhalb des Wiki-Vertrags, kein graph_writer-Kontaktpunkt, kein Frontmatter-Schreib-Loop. Klare ARCH-Empfehlung an PO (§B5).
- **C7 (LazyGraphRAG-Concepts) und UX-C2 (Discord-Wochen-Replay) bleiben `[NICHT-HEUTE]`** — Concepts brauchen Korpus-Größe (≥50 PFs, heute 10), Discord ist an [ENT-045](../doc/ENTSCHEIDUNGEN.md#ent-045-proaktiver-kanal-grundsätzlich-freigegeben-opt-in)-Aktivierung gekoppelt. Beide bleiben Backlog für MVP-3.

---

## Teil A — Eingebrachte Vetos und Marker

| Quell-File:Sektion | Marker-Typ | Begründung-Detail | Bezug zu Vertrag/ENT |
|---|---|---|---|
| `01_ai_research.md §C4` | (!)ARCH-FRAGE(!) | Migration schreibt direkt auf `wiki/` — Verhältnis zum Draft→Master-Workflow | [ENT-007](../doc/ENTSCHEIDUNGEN.md#ent-007-draft--master-git-workflow-für-llm-writes) |
| `01_ai_research.md §C5` | (!)ENT-NÖTIG(!) | Persistenz-Ort des `last_export`-Zeitstempels — `out/` vs. Wiki-Frontmatter | WikiWrite-Vertrag, [ENT-005](../doc/ENTSCHEIDUNGEN.md#ent-005-schema-v03-entitäts-ontologie) |
| `01_ai_research.md §C6` | (!)ENT-NÖTIG(!) | Sensitivity-Tier-Verhältnis für Bild-Inputs (Vision-API ist Cloud) | [ENT-006](../doc/ENTSCHEIDUNGEN.md#ent-006-sensitivity-tier-modell-provider-routing) |
| `02_ux.md §B5` | (!)ENT-NÖTIG(!) | IPA-Frontmatter-Slot ist Schema-Erweiterung | [ENT-005](../doc/ENTSCHEIDUNGEN.md#ent-005-schema-v03-entitäts-ontologie), [SCHEMA.md §3.2](../doc/SCHEMA.md) |
| `02_ux.md §B5` | (!)ARCH-FRAGE(!) | Render-Modul-Standort `scripts/` vs. `agents/render/` | Modul-Hygiene, [SCHEMA.md §6.2](../doc/SCHEMA.md) |
| `02_ux.md §C1` | (!)ARCH-FRAGE(!) | Bot-Token paralleler Send vs. Long-Polling | [bot.py](../bot.py), python-telegram-bot |

### A1 — Detail-Begründung pro Marker

**[01 §C4 — ARCH-FRAGE Frontmatter-Migration vs. Draft-Branch]**
[ENT-007](../doc/ENTSCHEIDUNGEN.md#ent-007-draft--master-git-workflow-für-llm-writes) verlangt: LLM-Writes über `draft → master`. Die geplante Migration ist **deterministisch** (kein LLM, pyyaml-Roundtrip auf 7 Files) — vergleichbar zur `anki_id`-Frontmatter-Patch-Logik in [export_anki.py:219-234](../scripts/export_anki.py#L219-L234), die laut [ENT-052](../doc/ENTSCHEIDUNGEN.md#ent-052-anki-card-identität-und-re-export-stabilität) explizit als Direct-Write-auf-`master` legitimiert ist. **Empfehlung:** Migration darf direkt schreiben, **wenn** sie unter explizitem Backup-Branch läuft (`git checkout -b backup/pre-frontmatter-migration` vor Lauf) und **idempotent** ist (zweiter Lauf: keine Änderung). Architekt-Verdict: keine ENT-Eskalation nötig — Pattern existiert bereits.

**[01 §C5 — ENT-NÖTIG Persistenz-Ort des Export-Zeitstempels]**
UX-Empfehlung: `out/anki_export_log.json` (gitignored). Alternative aus UX-Handover §Auftrag 2.3: `usage_stats: { last_anki_export: ... }` im VocabEntry-Frontmatter (graph-nativ). **Architekt-Empfehlung: `out/anki_export_log.json`.** Drei Gründe:
1. **WikiWrite-Vertrag-Schutz:** Der Wiki-Vertrag ist *LLM-Schreib-Wiki*. Jeder Frontmatter-Patch außerhalb Agent-Pfaden vergrößert die Liste der "Sonderwege" (heute genau einer: `anki_id`).
2. **Atomarität:** Ein Export-Lauf produziert *eine* Log-Schreibe statt N Frontmatter-Patches. Re-Export-Idempotenz wird trivial.
3. **Diff-Sauberkeit:** Wiki-Diffs in Obsidian zeigen weiterhin nur Inhalt, nicht Tooling-Metadaten.
**Aber:** [SCHEMA.md §2 "raw/ ist heilig"](../doc/SCHEMA.md) gilt nicht für `out/` — `out/` ist Build-Artefakt-Ordner (gitignored). Trotzdem PO-Beschluss als ENT empfohlen, weil Persistenz-Pfad architektur-relevant.

**[01 §C6 — ENT-NÖTIG Sensitivity-Tier für Bilder]**
[ENT-006](../doc/ENTSCHEIDUNGEN.md#ent-006-sensitivity-tier-modell-provider-routing): `private` → Ollama lokal. **Bilder gehen in [image_extractor.py](../agents/extractors/image_extractor.py) heute pauschal an Claude Vision (Cloud).** Wenn ein Bild-Drop mit PII-Inhalt (Selfie, Whiteboard mit Namen) ohne Tier-Markierung an die Vision-API geschickt wird, bricht das Privacy-Versprechen. **Erst-Empfehlung:** Bilder erben Default-Tier `sensitive`; Hint-Gate analog zu ENT-047 (`#privat`/`privatbild` → kein Cloud-Call, nur in `raw/assets/` archivieren). PO-Beschluss in 05.

**[02 §B5 — ENT-NÖTIG IPA-Schema-Erweiterung]**
[SCHEMA.md §3.2 VocabEntry](../doc/SCHEMA.md#32-vocabentry) listet keine `ipa`-Spalte. UX bevorzugt Frontmatter-Feld `ipa: "[ˈdwen.de]"`. **Architekt-Verdict:** ja, Frontmatter ist robuster als Body-Sektion (kein Markdown-Heading-Parsing, kein Konflikt mit `## Aussprache`-Bereichen). **Empfehlung an PO:** `[ENT-NEU?]` für SCHEMA.md §3.2-Erweiterung (`ipa: <string|null>`, optional, sprachspezifisch). Migration: Language-Agent füllt `ipa` bei Neu-Erstellung; Bestand bleibt leer (keine Backfill-Pflicht — Renderer skipt leer).

**[02 §B5 — ARCH-FRAGE Render-Modul-Standort]**
UX schlägt `scripts/render_card.py` vor. **Architekt-Verdict:** `scripts/` passt für **CLI-Entry** (heute `export_anki.py`), nicht für **Rendering-Bibliothek**. Sobald Discord/E-Mail-Konsumenten dazukommen ([ENT-049](../doc/ENTSCHEIDUNGEN.md#ent-049-zweit-oberflächen-strategie-telegram-bleibt-primär-cli-discord-e-mail-vorgemerkt-für-mvp-3)), wird `scripts/render_card.py` von Bot-Code (in `bot.py` oder `agents/`) importiert — `scripts/`-Imports aus dem Bot sind ein Code-Smell.
**Empfehlung:** `agents/render/__init__.py` + `agents/render/card.py` (`render_front`, `render_back`, `pick_profile`, `CSS_BLOCK`) + perspektivisch `agents/render/discord.py`, `agents/render/email.py`. `scripts/export_anki.py` wird zum dünnen CLI-Wrapper (Walk + Filter + `agents.render.card`-Aufruf + Genanki-Build). **Kein neuer ENT — Modul-Hygiene-Frage, fällt unter Architekt-Autorität.**

**[02 §C1 — ARCH-FRAGE Telegram-Echo + Polling-Bot]**
Risiko: zwei Prozesse mit demselben Bot-Token können sich mit Long-Polling und Send-API in die Quere kommen. **Architekt-Verdict:** kein Konflikt, weil **Send-Operationen sind state-los** und die Telegram-API multi-client-fähig auf `sendMessage` ist. Long-Polling ist nur für `getUpdates` exklusiv. Skript-Send über denselben Token ist seit langer Zeit Standard-Praxis (cron-Skripte, GitHub-Actions-Notifier). **Mitigation:** Skript erstellt einen *neuen* `Bot`-Client pro Lauf, kein Webhook-Setup, kein `getUpdates`-Call. Risiko: vernachlässigbar.

---

## Teil B — Analyse + Skizzen

> Format pro Chance: Machbarkeit · Skizze (≤10 Zeilen) · Aufwand (h) · Risiken/Schulden · Reihenfolge.

### B1: C1 — Index-Reparatur (`scripts/rebuild_index.py` + `summary:`-Frontmatter-Feld)

- **Machbarkeit:** `[MACHBAR]`
- **Skizze:**
  ```python
  # scripts/rebuild_index.py
  WIKI = REPO / "wiki"
  for md in WIKI.rglob("*.md"):
      fm, body = split_frontmatter(md.read_text(...))
      meta = parse_frontmatter(fm)
      if not meta.get("summary"):
          meta["summary"] = haiku_oneline(meta, body)   # einmalig
          patch_frontmatter(md, "summary", meta["summary"])
      register(meta["type"], md.stem, meta["summary"])
  write_index_md(buckets_by_type)
  ```
- **Aufwand:** 3h Skript + 1h Sonnet/Haiku-Pass (~21 Calls einmalig).
- **Risiken/Schulden:** Pre-Req **C4** (sonst pyyaml-Verweigerung auf 7 Vocab-Files); abhängig von einem konsistenten `_split_frontmatter` (heute zwei Implementierungen: [export_anki.py:79-98](../scripts/export_anki.py#L79-L98) regex-basiert, [language_agent.py:423-459](../agents/language_agent.py#L423-L459) f-string-dedent — Konsolidierung in eine Helper-Datei `agents/frontmatter.py` empfohlen, **kein Workshop-Scope, aber Schuld dokumentieren**).
- **Reihenfolge:** **2** (nach C4).

### B2: C2 — SQLite-FTS5-Build-Skript

- **Machbarkeit:** `[MACHBAR-BEDINGT: nur sinnvoll nach C1]` — ohne saubere Summaries hat FTS5 dieselben Slug-Token-Probleme wie heute Phase 1.
- **Skizze:**
  ```python
  # scripts/build_wiki_index.py
  conn = sqlite3.connect("out/wiki_index.db")
  conn.executescript("CREATE VIRTUAL TABLE wiki_fts USING fts5(slug, type, summary, body, tags);")
  for md in REPO.glob("wiki/**/*.md"):
      fm, body = split_frontmatter(md.read_text())
      meta = parse_frontmatter(fm)
      conn.execute("INSERT INTO wiki_fts VALUES(?, ?, ?, ?, ?)",
                   (md.stem, meta["type"], meta["summary"], body, " ".join(meta["tags"])))
  conn.commit()
  ```
- **Aufwand:** 4h (Schema + Walker + Smoke-Test gegen [graph_reader._search_sqlite](../agents/graph_reader.py#L207-L256)).
- **Risiken/Schulden:** **Inkonsistenz-Befund** `WIKI_PAGE_THRESHOLD = 30` in Code vs. `150` in [ARCHITECTURE.md §6.3](../doc/ARCHITECTURE.md#63-graph-reader--index-abstraktion) — vor C2 in PO-Synthese klären, welcher Wert gilt. Heute 21 Pages, in beiden Welten unter Schwelle — kein Sofort-Schmerz, aber Verträge müssen einig sein.
- **Reihenfolge:** **6** (nach Render-Stabilisierung; pre-emptiv ziehen, weil Phase-2-Stub heute ungetestet ist).

### B3: C3 — Lint-Auto-Fixes (3 Detektoren)

- **Machbarkeit:** `[MACHBAR]`
- **Skizze:**
  ```python
  # agents/lint_agent.py — _apply_auto_fixes (heute Stub, ENT-017)
  def _fix_backlink_symmetry(self) -> list[Fix]:    # Adjazenz-Vergleich, append in related:
  def _fix_index_fs_sync(self) -> list[Fix]:        # Glob ↔ index.md, fehlende ergänzen, tote löschen
  def _detect_slug_dedup(self) -> list[Question]:   # SequenceMatcher ≥ 0.9 → Telegram-Frage
  ```
- **Aufwand:** 6h (drei Detektoren + ein Test-Run).
- **Risiken/Schulden:** Pre-Req **C4** (Backlink-Append schreibt in Frontmatter, das heute kaputt ist). Lint-Schreibe braucht Draft-Branch — **deshalb wieder ENT-007**. Heute schreibt der Bot direkt auf `master` ([01_ai_research §A2(b) L11](01_ai_research.md)) — **wenn Lint-Live geht, ist das Re-Aktivierung des Draft-Workflows nötig**, was ein eigener Architektur-Aufwand ist (siehe §C1 unten).
- **Reihenfolge:** **5** (nach Render-Stabilisierung, vor Multi-Modal).

### B4: C4 — Frontmatter-Schuld-Migration (Pre-Req für alles)

- **Machbarkeit:** `[MACHBAR]`
- **Skizze:**
  ```python
  # scripts/migrate_vocab_frontmatter.py
  for md in (REPO / "wiki" / "language" / "vocab").glob("v_*.md"):
      fm_block, body = split_frontmatter(md.read_text(encoding="utf-8"))
      data = parse_frontmatter_regex(fm_block)        # bestehender Workaround
      new_fm = yaml.dump(data, sort_keys=False, allow_unicode=True)
      md.write_text(f"---\n{new_fm}---\n{body}", encoding="utf-8")
  # parallel: agents/language_agent.py:423-459 — _build_frontmatter() per yaml.dump statt f-string-dedent
  ```
- **Aufwand:** 2h Migration + 1h Code-Fix in language_agent.
- **Risiken/Schulden:** Destruktiv. Backup-Branch `backup/pre-frontmatter-migration` vor Lauf zwingend. **`anki_id` muss bit-exakt überleben** (sonst SRS-Verlust via [ENT-052](../doc/ENTSCHEIDUNGEN.md#ent-052-anki-card-identität-und-re-export-stabilität)). Idempotenz-Test: zweiter Lauf darf 0 Files ändern.
- **Reihenfolge:** **1** (Pre-Req für alles, was Frontmatter-Konsumenten erweitert).

### B5: C5a — Health-Tag `health::stale-mnemonic` + UX-Auftrag 4

- **Machbarkeit:** `[MACHBAR-BEDINGT: nach C4]`
- **Skizze:**
  ```python
  # scripts/export_anki.py — neue Funktion
  log_path = REPO / "out" / "anki_export_log.json"
  log = json.loads(log_path.read_text()) if log_path.exists() else {}
  for rec in records:
      last = log.get(rec.slug)
      if last and rec.updated and rec.updated > last:
          tags.append("health::stale-mnemonic")
      log[rec.slug] = today_iso()
  log_path.write_text(json.dumps(log, indent=2, sort_keys=True))
  ```
- **Aufwand:** 3h (Log-Lesen/Schreiben, Tag-Vergabe, Snapshot-Test).
- **Risiken/Schulden:** Toleranz-Frage (Zeit-Drift, ISO-Datum vs. Datetime). **Empfehlung: Granularität YYYY-MM-DD; `updated`-Vergleich ohne Zeitkomponente.** `out/anki_export_log.json` ist gitignored — bei Repo-Klon auf neuem Gerät kein Health-Tag, bis erster Export gelaufen ist (akzeptabler Cold-Start).
- **Reihenfolge:** **4** (nach Render-Modul-Trennung, weil im Refactor mit konsolidiert werden kann).

### B6: C6 — Multi-Modal-Backfill (Bilder/PDFs)

- **Machbarkeit:** `[MACHBAR-BEDINGT: nach Sensitivity-ENT]`
- **Skizze:**
  ```python
  # bot.py — neue Handler
  async def handle_photo(update, ctx):
      file = await context.bot.get_file(update.message.photo[-1].file_id)
      dest = REPO / "raw" / "assets" / f"{ts}_telegram.jpg"
      await file.download_to_drive(dest)
      tier = "sensitive"   # Default ohne Hint
      if "#privat" in (update.message.caption or "").lower():
          return  # Quick-Save, kein Auto-Ingest
      ev = image_extractor.extract(dest, tier=tier)   # NEU: tier-Parameter
      write_event(ev)   # raw/events/, normaler Ingest
  ```
- **Aufwand:** 3h Handler + 1h Tier-Plumbing.
- **Risiken/Schulden:** **Sensitivity-ENT vorher** (siehe §A1 [01 §C6]). PDF-Pfad analog (kein Cloud-Call, lokal — Tier irrelevant).
- **Reihenfolge:** **7** (nach Lint, weil Bild-Inputs Index-Wachstum beschleunigen — Lint sollte parat sein).

### B7: C7 — Concept-Cluster mit LazyGraphRAG-Idee

- **Machbarkeit:** `[NICHT-HEUTE: 10 PFs, Schwelle 50]`
- **Skizze:** entfällt (Auslöser nicht erreicht).
- **Aufwand:** ~1–2 Tage (siehe 01 §C7), aber dispatch erst bei Korpus-Wachstum.
- **Risiken/Schulden:** Trigger-Mechanik fehlt heute (kein Cron, kein graph-size-watcher). Bei Implementierung: NLP-Co-Occurrence ist Karpathy-konform (kein Vektor-Store) — kein ENT-Bedarf, solange Implementierung statisch bleibt.
- **Reihenfolge:** **9** (Backlog für MVP-3+).

### B8: C8 — User-Profile Self-Refresh

- **Machbarkeit:** `[MACHBAR-BEDINGT: nach C3]`
- **Skizze:**
  ```python
  # agents/lint_agent.py — neuer wöchentlicher Pass
  def refresh_user_profile(self):
      facts = walk("wiki/personal/facts/")
      stats = aggregate(facts)   # lang-share, theme-clusters, story_score-percentiles
      diff = sonnet_compose_profile_update(stats, current_profile)   # ~$0.05/Lauf
      append_diff_to_user_profile(diff)
  ```
- **Aufwand:** 4h + ~$0,20/Monat.
- **Risiken/Schulden:** Append-Diff statt Overwrite (sonst Drift mit aktiver Bot-Session-Read). [ENT-043](../doc/ENTSCHEIDUNGEN.md) `telegram_state:`-Block-Eintragung darf nicht überschrieben werden — Append-Bereich klar unter eigener Sektion.
- **Reihenfolge:** **8** (optional MVP-2+, nicht-blockierend).

### B9: UX-B1+B5 — Slot-Profile (A/B/C/D) + Render-Modul-Trennung

- **Machbarkeit:** `[MACHBAR]`
- **Skizze:**
  ```python
  # agents/render/card.py
  CSS_BLOCK = "..."   # 80 Regeln aus 02_ux.md §B3
  def pick_profile(rec: VocabRecord) -> Literal["A","B","C","D"]:
      if rec.pos == "Verb" and rec.conjugation: return "D"
      if rec.mnemonic and rec.difficulty in {"B2","C1","C2"}: return "C"
      if rec.genus in {"el","la"}: return "B"
      return "A"
  def render_front(rec): ...
  def render_back(rec): ...
  ```
- **Aufwand:** 6h (Modul + Profile + Snapshot-Tests + `export_anki.py`-Refactor).
- **Risiken/Schulden:** `pos`-Extraktion heute nicht im Renderer (UX-§B5 [TODO]); Regex `r"^\s*-\s*\*\*Typ:\*\*\s*(\w+)"` analog zu `_GENUS_RE`. **Snapshot-Tests:** pytest-snapshot oder `expected/`-HTML-Files; ohne Anki/genanki-Setup. **Edge-Case Adverb:** UX hat in §Empfehlungen Punkt 7 erwähnt — Default Profil A; Pflichtfeld `pos == "Adverb"` triggert kein Profil → fällt automatisch auf A.
- **Reihenfolge:** **3** (nach C1/C4, Pre-Req für C5a und alle Render-Konsumenten).

### B10: UX-C3 — `RenderDict`-Vertrag

- **Machbarkeit:** `[MACHBAR]`
- **Skizze:**
  ```python
  # agents/render/card.py
  @dataclass(frozen=True)
  class RenderDict:
      identity: dict      # slug, anki_id, language
      content:  dict      # word, translation_primary, example_primary, mnemonic
      display:  dict      # cefr, genus, tags
      links:    dict      # obsidian, filesystem
  def vocab_record_to_render_dict(rec: VocabRecord) -> RenderDict: ...
  ```
- **Aufwand:** 3h (Dataclass + Adapter + Tests).
- **Risiken/Schulden:** Pflicht-/Optional-Trennung pro Sektion: `identity.slug`/`identity.language` Pflicht; `content.word`/`content.translation_primary` Pflicht; alles andere optional. Implementierung als `dataclass` (UX-Empfehlung), nicht TypedDict — `frozen=True` erzwingt Render-Determinismus.
- **Reihenfolge:** **3b** (gemeinsam mit B9, nicht separat).

### B11: UX-C1 — Telegram-Inline-Echo nach Anki-Export

- **Machbarkeit:** `[MACHBAR]`
- **Skizze:**
  ```python
  # scripts/export_anki.py — neuer Flag
  if args.notify_telegram:
      from telegram import Bot
      bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
      bot.send_message(chat_id=os.environ["TELEGRAM_CHAT_ID"],
                       text=format_anki_summary(summary), parse_mode="MarkdownV2")
  ```
- **Aufwand:** 2h (Flag + Format + Smoke-Test).
- **Risiken/Schulden:** ARCH-FRAGE [02 §C1] geklärt (kein Polling-Konflikt). `TELEGRAM_CHAT_ID` muss in `.env` (Single-User → ein Chat). Falls in CI gelaufen: Flag default false, kein Send.
- **Reihenfolge:** **4b** (gemeinsam mit B5/Health-Tag).

### B12: UX-C2 — Discord-Wochen-Replay

- **Machbarkeit:** `[NICHT-HEUTE: gekoppelt an ENT-045-Aktivierung]`
- **Skizze:** entfällt — abhängig von Discord-Bot-Setup, ENT-045-Policy-Implementierung, MVP-3-Scope.
- **Aufwand:** ~4 Tage (siehe 02 §C2).
- **Risiken/Schulden:** Doppel-Outbound-Telemetrie (siehe Teil D). Discord-Embeds brauchen `agents/render/discord.py` — der `RenderDict`-Vertrag (B10) muss dafür genau passen.
- **Reihenfolge:** **MVP-3-Backlog**.

---

## Teil C — Architektur-Konsequenzen

### C1: Änderungen in `doc/ARCHITECTURE.md`

Konkrete Sektion-Änderungen, die der PO später committen oder verwerfen kann:

1. **§6.3 Graph Reader — `WIKI_PAGE_THRESHOLD`-Korrektur:** Dokument sagt `150`, [Code](../agents/graph_reader.py#L20) sagt `30`, [ENT-027](../doc/ENTSCHEIDUNGEN.md#ent-027-graph_reader-zweiphasig-qk-4) sagt `30`. **Empfehlung:** ARCHITECTURE.md auf `30` korrigieren (Code + ENT sind die führenden Quellen).
2. **§6.1 LangGraph-Diagramm — `index_updater`-Node:** heute im Diagramm enthalten (Zeile `workflow.add_node("update_index", index_updater.update)`), aber **kein `agents/index_updater.py` existiert**. **Empfehlung:** Sektion ergänzen mit Status-Hinweis: "*Index-Updater wird heute manuell durch `scripts/rebuild_index.py` realisiert (siehe [Workshop §B1](../workshop/03_architect.md))*". PO entscheidet, ob als ARCHITECTURE-Schritt oder als COMP-Spec.
3. **Neue §11 Render-Layer:** Kurzkapitel zur Trennung von Sync-Layer (Anki-Export-CLI) und Render-Layer (`agents/render/`). Inhalt: Modul-Standort, `RenderDict`-Vertrag, Multi-Konsumenten-Pfad ([ENT-049](../doc/ENTSCHEIDUNGEN.md#ent-049-zweit-oberflächen-strategie-telegram-bleibt-primär-cli-discord-e-mail-vorgemerkt-für-mvp-3) Vorbereitung).
4. **§8 Draft→Master Workflow — Status-Korrektur:** Workflow ist heute **dormant** (Bot schreibt direkt auf `master`, [01 §A2(b) L11](01_ai_research.md)). **Empfehlung:** Sektion mit `(?)Status: dormant — re-aktivieren wenn Lint live geht (siehe Workshop §B3)(?)` markieren. Alternativ: Sektion auf "geplant für post-MVP-2" verschieben.

### C2: Neue Komponenten-Specs (Kandidaten)

- **`doc/COMP_RENDER.md`** — *empfohlen:* Render-Layer-Spec. Inhalt: Slot-Profile (A/B/C/D-Heuristik aus UX §B1), `RenderDict`-Vertrag, Profile-Auswahl-Logik, Multi-Konsumenten-Plan (Anki, Discord-MVP-3, E-Mail-MVP-3), Test-Strategie (Snapshot-Tests). **Begründung:** Render-Layer wird Multi-Konsumenten — eine Spec hält Verträge stabil.
- **`doc/COMP_LINT.md`** — *empfohlen:* Lint-Auto-Fixes-Spec. Heute nur als [SCHEMA.md §8](../doc/SCHEMA.md#8-selbstheilungs-definition-was-ist-ein-kranker-graph)-Tabelle und [ENT-017](../doc/ENTSCHEIDUNGEN.md). Inhalt: Detektor-Liste (3 Pflicht aus Workshop §B3 + 2 perspektivisch), Trigger-Mechanik (heute nicht da), Telegram-Frage-Pattern für unklare Fixes, Idempotenz-Garantien.
- **`doc/COMP_INDEX.md`** — *optional:* Index-Updater-Spec. Heute nur als LangGraph-Node-Name. Inhalt: Walker-Algorithmus, Frontmatter-`summary:`-Extraktion, Phase-1/Phase-2-Übergangs-Verhalten, Re-Build-Idempotenz. **Niedrige Priorität** — kann auch in `COMP_LINT.md` als Sub-Sektion.

### C3: Schulden-Bezug — was Workshop-Ideen treffen

| Workshop-Idee | Trifft Schuld in `hinweise/technischer_hinweis.md` | Konsequenz |
|---|---|---|
| C3 (Lint live) | "`LintAgent._apply_auto_fixes()` sind Stubs" + "kein Error-Handling im Bot" | Lint-Live entriegelt Stub-Schuld. Bot-Error-Handling parallel ziehen. |
| C2 (FTS5) | "`graph_reader` Phase 2 (SQLite) ungetestet" | C2 entriegelt diese Schuld direkt. |
| C4 (Frontmatter) | (nicht in technischer_hinweis.md erfasst — neuer Eintrag fällig) | Schuld retrospektiv in `hinweise/technischer_hinweis.md` aufnehmen. |
| C5a (Health-Tag) | (nicht erfasst) | Mit Render-Modul-Trennung in einem Aufwasch. |
| C6 (Multi-Modal) | (nicht erfasst) | Sensitivity-ENT vorher, dann Bot-Handler-Erweiterung. |

**Bestehende Inkonsistenzen, die der Workshop aufdeckt** (Architekt-Befund, kein Workshop-Auftrag):

- (?)`(?)agents/graph_writer.py:55-65 — reject_draft macht git checkout main, Branch heißt aber master ([ENT-039](../doc/ENTSCHEIDUNGEN.md#ent-039-branch-namen-konvention-master-vs-main)). reject_draft() würde im echten Repo brechen. PO-Befund.(?)`
- (?)`(?)agents/graph_reader.py:20 — WIKI_PAGE_THRESHOLD = 30, doc/ARCHITECTURE.md §6.3 sagt 150. Code + ENT-027 sind führend, ARCHITECTURE-Doku-Korrektur fällig.(?)`
- (?)`(?)agents/index_updater.py existiert nicht, ARCHITECTURE.md §6.1 nennt es als LangGraph-Node. Faktisch ist Index-Pflege manuell/intransparent (Drift-Belege in 01 §A1). C1 dieses Workshops behebt es als Skript.(?)`
- (?)`(?)Draft→Master-Workflow ([ENT-007](../doc/ENTSCHEIDUNGEN.md#ent-007-draft--master-git-workflow-für-llm-writes), ARCHITECTURE.md §8) ist dormant — Bot schreibt direkt auf master. Wenn Lint-Auto-Fixes live gehen (C3), ist Re-Aktivierung nötig oder ENT-007 muss formal pausiert werden.(?)`

---

## Teil D — Eigene Ergänzungen

> Was in 01/02 nicht vorkam, aber aus Architektur-Sicht **kritisch** ist.

**D1 — Idempotenz-Garantien für Multi-Modal-Backfill (C6):**
Wenn dasselbe Bild zweimal an den Bot geschickt wird (z.B. WhatsApp-Forward, Re-Upload), entstehen heute **zwei `raw/events/`-Einträge und zwei Wiki-Writes**. Voice-Pfad hat dasselbe Problem (heute akzeptiert, weil Voice-Re-Send selten). Bei Bildern aber typisch: User schickt dasselbe Foto mehrfach mit unterschiedlichen Captions.
**Empfehlung:** SHA1-basierte Asset-Deduplizierung in `raw/assets/` (Datei-Hash → existiert bereits → kein neues Event, sondern Update an bestehendem Event). Kein Workshop-Scope, aber **Pre-Req für C6**.

**D2 — Migrations-Pfade als wiederkehrendes Pattern:**
Frontmatter-Migration (C4) ist die *zweite* Migration nach `anki_id`-Stempel ([ENT-052](../doc/ENTSCHEIDUNGEN.md#ent-052-anki-card-identität-und-re-export-stabilität)). Es wird weitere geben (IPA-Schema-Erweiterung, Sensitivity-Tier-Default, etc.). **Empfehlung:** `scripts/migrations/` als Ordner mit Datums-Präfix-Konvention (`scripts/migrations/2026-05-08_frontmatter_yaml.py`), plus ein zentraler `scripts/migrations/applied.json`-Log (wer wurde wann gelaufen). Verhindert versehentliches Doppel-Anwenden auf neuen Geräten.

**D3 — Telemetry für Graph-Wachstum:**
Heute hat das System **keine Wachstums-Telemetrie**. `index.md`-Bucket-Counts sind die einzige sichtbare Metrik — und die ist drift-anfällig (siehe 01 §A1). [ENT-027](../doc/ENTSCHEIDUNGEN.md#ent-027-graph_reader-zweiphasig-qk-4)-Phase-Schwelle ist ohne stabile Wachstums-Messung blind. **Empfehlung:** Wöchentlicher `scripts/graph_stats.py`-Lauf in `out/graph_stats_YYYY-WW.json` (Counts pro Entitäts-Typ, Drift-Flag, Phase-Empfehlung). Kein LLM, deterministisch, ~50 Zeilen Python. **Niedrige Priorität, hoher Wert.**

**D4 — Test-Strategie-Lücken:**
- **Renderer-Snapshot-Tests** (UX-§B5) — gut.
- **Lint-Auto-Fixes-Tests** — fehlend. Vorschlag: `tests/lint/fixtures/before/` + `tests/lint/fixtures/after/` mit kleinen Wiki-Mock-Trees, Detektor läuft, Diff prüft.
- **Migrations-Tests** (C4) — fehlend. Vorschlag: 7 Vocab-Files als Fixture, Migration läuft, pyyaml-Roundtrip schlägt zu, zweiter Lauf 0 Diffs.
- **End-to-End-Tests für Bot-Pipeline** — heute nicht da; bei Multi-Modal (C6) kritisch.
**Konsolidiert:** `tests/`-Ordner-Struktur ist heute leer/uneinheitlich (kein Eintrag in technischer_hinweis.md). PO-Hinweis fällig.

**D5 — Draft-Branch-Re-Aktivierungs-Plan:**
Wenn C3 (Lint-Auto-Fixes) live geht, schreibt Lint in das Wiki. [ENT-007](../doc/ENTSCHEIDUNGEN.md#ent-007-draft--master-git-workflow-für-llm-writes) verlangt Draft→Master für LLM-Writes. **Lint-Auto-Fixes sind deterministisch** (kein LLM für Backlink-Symmetrie und Index-Sync; LLM nur für Slug-Dedup-Telegram-Frage), also formal direkt-write-legitim — analog zu `anki_id`-Patch und Frontmatter-Migration. **Aber:** der allgemeine Wiki-Schreib-Pfad aus dem Bot (PersonalFact, VocabEntry, etc.) **ist heute ebenfalls direkt-master**, ohne ENT-007-Konformität. Das ist eine offene Schuld, die der Workshop berührt aber nicht löst. **Empfehlung:** PO-Synthese §05 entweder formell ENT-007-Pause beschließen (mit Begründung "MVP-2-Pragmatik, MVP-3-Wiederaufnahme") oder Bot-Pfad auf Draft-Branch umstellen — **ein eigenes Mini-Projekt**, kein Workshop-Output.

**D6 — `_split_frontmatter`-Konsolidierung:**
Heute zwei Implementierungen: [export_anki.py:79-98](../scripts/export_anki.py#L79-L98) (regex-basiert, dedent-tolerant) und [language_agent.py:423-459](../agents/language_agent.py#L423-L459) (f-string-dedent-Builder, der Schuld erzeugt). Plus implizit ein dritter Konsument im geplanten `rebuild_index.py` (B1). **Empfehlung:** `agents/frontmatter.py` als zentrale Helper-Datei. Nach C4 ist pyyaml die Single-Source-Of-Truth — Regex-Workaround wird obsolet, Helper kapselt `read`/`write`/`patch`. **Pre-Req für saubere Migration zu Mehr-Konsumenten.**

---

## Empfehlungen für QM-Phase

> Was der QM zwingend prüfen muss.

1. **Sensitivity-Pfade in C6:** Ist die Default-Tier-Annahme (`sensitive`) für Bilder ausreichend? Was, wenn Hint `#privat` fehlt und das Bild PII enthält? Welche Mitigation greift, bevor Vision-API gerufen wird?
2. **Budget-Risiken:**
   - C1 einmalig ~$0.21 (21 Sonnet/Haiku-Calls für Summaries) — vernachlässigbar.
   - C8 wöchentlich ~$0.05 → ~$0.20/Monat — innerhalb $5–10-Budget.
   - C6 Vision-Calls bei 5 Bildern/Woche — ~$0.02/Monat — vernachlässigbar.
   - Bei kombinierter MVP-2-Zweitwelle inkl. Bot-Voice-Hot-Path (Sonnet pro Voice ~$0.012): Monatslast bleibt deutlich unter Budget. **QM bestätigen.**
3. **Test-Lücken** (siehe §D4):
   - Renderer-Snapshot-Tests Pflicht für B9/B10.
   - Lint-Detektor-Tests Pflicht für B3.
   - Migrations-Idempotenz-Test Pflicht für B4.
   - End-to-End-Test für Multi-Modal Pflicht für B6.
4. **Idempotenz-Checks:**
   - C4: zweiter Lauf = 0 Diffs?
   - C5a: Re-Export setzt Tag deterministisch?
   - C6: Doppel-Bild-Drop erzeugt nur ein Event (siehe §D1)?
5. **Inkonsistenz-Befunde aus §C3** als P1 in QM-Risiko-Snapshot, nicht erst in PO-Synthese.

---

## Risiken (Top 5, geordnet)

1. **Frontmatter-Schuld als Erbe-Risiko.** Heute Anki-Renderer; morgen Discord/E-Mail/Lint/Story-Lab. Jeder neue Konsument erbt den Regex-Workaround, wenn C4 nicht zuerst läuft. **Wahrscheinlichkeit: hoch. Schaden: hoch. Mitigation: B4 als Pre-Req.**
2. **Draft→Master-Workflow ist faktisch dormant (Befund C3).** [ENT-007](../doc/ENTSCHEIDUNGEN.md#ent-007-draft--master-git-workflow-für-llm-writes) ist Vertrag, Code lebt anders. Re-Aktivierung bei Lint-Live ist ein eigener Aufwand. **Wahrscheinlichkeit: mittel (passiert sobald C3 live geht). Schaden: mittel. Mitigation: PO entscheidet in 05 zwischen formaler Pause und Re-Aktivierung.**
3. **`graph_writer.py:55-65` `git checkout main` ist Bug** ([ENT-039](../doc/ENTSCHEIDUNGEN.md#ent-039-branch-namen-konvention-master-vs-main) verletzt). Wenn `reject_draft()` jemals real aufgerufen wird, bricht der gesamte Draft-Workflow im Repo (Branch existiert nicht). **Wahrscheinlichkeit: gering (heute nicht aufgerufen). Schaden: hoch. Mitigation: triviale Fix-PR, Workshop-Output dokumentiert es.**
4. **Sensitivity-Tier-Bruch durch Multi-Modal (C6).** Bilder ohne Tier-Markierung gehen direkt an Vision-API. **Wahrscheinlichkeit: hoch (sobald C6 live). Schaden: hoch (Privacy-Vertrags-Bruch). Mitigation: ENT vor Implementierung.**
5. **Index-Drift wächst weiter pro Wiki-Write.** Solange `index_updater` als Modul fehlt, vergrößert jeder Wiki-Write potenziell die Drift. **Wahrscheinlichkeit: gewiss (kontinuierlich). Schaden: mittel (Retrieval-Schwäche). Mitigation: B1 + neuer `index_updater`-Modul-Pfad.**

---

## Implementierungs-Reihenfolge (Vorschlag)

> Numerierte Liste mit Abhängigkeiten. Kein Aufwand-Posten als Empfehlung, sondern als Reihenfolge-Wunsch.

1. **B4 — C4 Frontmatter-Migration** (3h, Pre-Req für alles)
   - Backup-Branch zwingend, Idempotenz-Test.
2. **B1 — C1 Index-Reparatur** (4h, abhängig von 1)
   - `scripts/rebuild_index.py` + einmaliger Sonnet/Haiku-Pass für Summaries.
   - parallel: `agents/frontmatter.py` als Konsolidierung (§D6).
3. **B9+B10 — Render-Modul-Trennung + RenderDict-Vertrag** (9h, abhängig von 1)
   - Neuer Pfad `agents/render/card.py`, `scripts/export_anki.py` als dünner CLI-Wrapper.
4. **B5 + B11 — Health-Tag + Telegram-Echo** (5h, abhängig von 3)
   - `out/anki_export_log.json`, `--notify-telegram`-Flag.
5. **B3 — C3 Lint-Auto-Fixes** (6h, abhängig von 1, 2)
   - Pre-Decision: Draft-Branch re-aktivieren oder ENT-007 pausieren? (siehe §D5)
6. **B2 — C2 SQLite-FTS5-Build-Skript** (4h, abhängig von 2)
   - inkl. ARCHITECTURE.md-Threshold-Korrektur.
7. **B6 — C6 Multi-Modal-Backfill** (4h, abhängig von ENT zu Sensitivity)
   - Bot-Handler + Asset-SHA-Dedup (§D1).
8. **B8 — C8 User-Profile Self-Refresh** (4h, abhängig von 5)
   - Append-Diff statt Overwrite.
9. **MVP-3-Backlog:** B7 (C7 Concept-Cluster, dispatch ≥50 PFs), B12 (UX-C2 Discord-Wochen-Replay, gekoppelt an [ENT-045](../doc/ENTSCHEIDUNGEN.md#ent-045-proaktiver-kanal-grundsätzlich-freigegeben-opt-in)).

**Gesamt-MVP-2-Zweitwelle (Schritte 1–8):** ~39h Architekt-Aufwand. Plus Test- und Migrations-Aufwand (etwa +30%).

**Pre-MVP-3-Klärung (PO-Synthese-Aufträge):**
- IPA-Schema-Erweiterung als ENT.
- Sensitivity-Tier für Bilder als ENT.
- `out/anki_export_log.json` als architektur-relevante Persistenz-Entscheidung als ENT.
- Inkonsistenz `WIKI_PAGE_THRESHOLD` (30 vs. 150) als ARCHITECTURE.md-Korrektur.
- `graph_writer.py`-Branch-Bug als technische Schuld in `hinweise/technischer_hinweis.md`.
- Draft-Branch-Workflow-Status (dormant vs. re-aktiviert) als ENT.

---
