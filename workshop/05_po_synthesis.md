# 05 — PO-Synthese: Workshop-Schluss + Backlog + ENT-Updates
> Phase 5 von 5 | Erstellt: 2026-05-08 | Rolle: Product Owner | Modus: **Synthese + Verdict + Anti-Decisions + ENT-Beschluss**
> Vor-Phasen: [01_ai_research.md](01_ai_research.md), [02_ux.md](02_ux.md), [03_architect.md](03_architect.md), [04_qm.md](04_qm.md). Folge-Phase: (Ende des Workshops). Nächste Implementierungs-Session: [sessions/026_2026-05-09.md](../sessions/026_2026-05-09.md).

---

## Zusammenfassung (max 5 Bullets)

- **Workshop-Verdict: erfolgreich, Synthese mit Auflagen.** Alle vier QM-Auflagen werden angenommen, alle drei ENT-NEU-Vorschläge werden zu konkreten ENT-Einträgen (ENT-053, ENT-054, ENT-055), ENT-007 wird formal pausiert (ENT-056 mit `revidiert: ENT-007`).
- **MVP-3-Plan bleibt unangetastet.** Der Workshop liefert keine Reset-Forderung. Das, was er liefert, ist ein **MVP-2-Zweitwellen-Backlog** mit 13 Items (P1 + P2 + P3 + Radar), eingebettet in die scharfe Reihenfolge aus [03 §Implementierungs-Reihenfolge](03_architect.md). C7 (LazyGraphRAG) und Discord-Wochen-Replay bleiben Radar — beide kommen nach `doc/CHANCEN.md`.
- **Reihenfolge ist nicht-verhandelbar:** Schritt 0 (`graph_writer.py`-Branch-Bug-Fix) → Schritt 0b (Test-Skelett) → Schritt 0c (drei ENT-NEUs in `doc/ENTSCHEIDUNGEN.md`) → C4 → C1 → Render-Modul → C5a + Telegram-Echo → C3 → C2 → C6 → C8. Die Implementierungs-Session 026 startet mit Schritt 0/0b/0c als Vorbereitung, dann C4 als ihr Top-1-Item.
- **Top-3-Workshop-Insights** (Sektion 6 unten): (1) Frontmatter-Schuld ist Erbe-Risiko, nicht lokales Symptom — sie blockiert systematisch jeden neuen Render-Konsumenten; (2) der Workshop hat vier Pre-Workshop-Inkonsistenzen aufgedeckt, die älter sind als der Workshop und transparent benannt werden müssen; (3) "Synthese mit Auflagen" als QM-Urteil ist exakt das richtige Format für einen reifenden MVP-2 — kein Reset, aber auch kein Free-Pass.
- **S026-Brief-Adressat:** **Architekt.** Top-1-Backlog-Item ist `BL-01 graph_writer.py-Branch-Bug-Fix` als Schritt 0; das eigentliche Workshop-Implementierungs-Top-1 ist `BL-03 Frontmatter-Migration` (C4) als Schritt 1. Beides liegt in Architekt-Autorität. PO-Synthese-Phase ist abgeschlossen — keine weiteren PO-Sessions vor S027 nötig.

---

## 1 — Synthese der 4 Rollen-Beiträge

### 1.1 Gemeinsames Bild

Alle vier Rollen ziehen ohne Bruch: **MVP-2 ist faktisch geschlossen, der Knowledge-Graph-Kern ist tragfähig, aber der Bootstrap-Stand hat fünf Schmerzpunkte, die zwischen Erstwelle und MVP-3 priorisiert werden sollten.**

- **AI-Research** ([01](01_ai_research.md)): Karpathy-Knoten hält, Index ist heute kaputt (Slug-Replikate als Summaries), Frontmatter-Schuld blockiert jeden künftigen Konsumenten, Lint-Stub heißt "keine Konsolidierung", Multi-Modal-Pfade sind code-fertig aber Trigger-frei. Acht konkrete Chancen (C1–C8), sortiert nach Schmerz: P1 = C1 + C4, P2 = C3 + C5, P3 = C2/C6/C8, Off-Radar = C7.
- **UX** ([02](02_ux.md)): Ein-Notetype, vier-Slot-Profile (A/B/C/D), Template-first/LLM-second; Render-Layer als eigenes Modul empfohlen; `RenderDict`-Adapter-Vertrag für künftige Discord/E-Mail-Konsumenten; Mobile-Backlink-Befund ist hart (S024-Live-Test); C5a (Health-Tag) angenommen, C5b (zweiter Backlink) abgelehnt.
- **Architekt** ([03](03_architect.md)): Keine harten ARCH-VETOs. Sechs Marker (3× ENT-NÖTIG, 3× ARCH-FRAGE). Reihenfolge ist scharf. Vier Pre-Workshop-Inkonsistenzen aufgedeckt (`graph_writer`-Branch-Bug, `WIKI_PAGE_THRESHOLD` 30-vs-150, `index_updater`-Phantom, Draft-Branch dormant). Render-Modul-Standort: `agents/render/` statt `scripts/` (Override gegen UX-Vorschlag, mit Begründung Multi-Konsumenten).
- **QM** ([04](04_qm.md)): Meilenstein-Urteil "Synthese mit Auflagen". Vier P1-Befunde, alle heilbar in 05. Sieben QK-Vorschläge (QK-8 bis QK-14). Bonus-Befund: `graph_reader.py:3-4` Header-Kommentar widerspricht Z.20 derselben Datei.

### 1.2 Wo sich die Rollen widersprechen

**Asymmetrien dokumentiert, alle aufgelöst:**

| # | Sache | 01 | 02 | 03 | 04 | PO-Auflösung |
|---|---|---|---|---|---|---|
| A1 | C5b zweiter Backlink (Anki-Back → `index.md#section`) | vorgeschlagen | abgelehnt (Mobile-Bruch) | UX-Verdict akzeptiert | OK | **C5b bleibt abgelehnt** (siehe §3 Anti-Decisions). |
| A2 | Render-Modul-Standort | nicht adressiert | `scripts/render_card.py` | Override `agents/render/card.py` | QK-11 ratifiziert Architekt | **Architekt-Override angenommen.** Modul-Hygiene-Frage, kein ENT nötig (Architekt-Autorität). |
| A3 | Persistenz-Pfad Health-Tag-Zeitstempel | `out/` ODER `usage_stats:` | nicht festgelegt | `out/anki_export_log.json` empfohlen | QK-10 ratifiziert | **`out/anki_export_log.json`** als ENT-054 (siehe §4). |
| A4 | Sensitivity-Default für Bilder | nicht klar | nicht adressiert | Default `sensitive` + Hint blockt | QK-9: stuft auf Default = Quick-Save, Vision nur mit Hint | **QM-Empfehlung übernommen** (asymmetrisch zu ENT-047/048, siehe ENT-053 §4). Privacy-Default schlägt Lern-Default. |
| A5 | C8 Sonnet vs. Haiku | C8 nutzt Sonnet | nicht adressiert | Sonnet-OK (interner Lint, nicht ENT-045) | "PO bestätigt Sonnet?" | **Sonnet-OK bestätigt.** C8 ist interner Lint-Pass, **nicht** proaktiv-impulsiv im Sinne ENT-045. ~$0,20/Monat im Budget. |

**Drift Index↔Filesystem (01 §A1) als P3 in Backlog aufgenommen** — QM hat das in §A1 als kleine Asymmetrie markiert (zwischen 01 als gravierend, 03 als Konsequenz von "kein index_updater"). PO-Verdict: Symptom-Grad ist gravierend, aber Mitigation ist BL-04 (C1 Index-Reparatur, P1) — also kein eigener Backlog-Eintrag, sondern als Begründung in BL-04 dokumentiert.

### 1.3 Stand der Verträge nach Workshop

| Vertrag | Stand vor Workshop | Stand nach Workshop |
|---|---|---|
| Karpathy-Prinzip (kein RAG, kein Vektor-Store) | gehalten | **gehalten** (kein Vorschlag bricht es; C7 nutzt LazyGraphRAG = NLP-statisch) |
| WikiWrite-Vertrag (LLM-Schreib-Wiki) | gehalten | **gehalten** (C4 + C5a + C3 sind deterministisch; analog `anki_id`-Patch ENT-052) |
| MVP-3-Stufung | unangetastet | **unangetastet** (Workshop liefert MVP-2-Zweitwelle, kein MVP-3-Vorzug) |
| Branch `master` (ENT-039) | gehalten in Doku, **gebrochen in `graph_writer.py:55-65`** | **wird gefixt** als BL-01 (Schritt 0) |
| Sensitivity-Routing (ENT-006) | gehalten (heute keine Bild-Trigger) | **wird durch ENT-053 stabilisiert** (Pre-Req für C6) |
| Draft→Master-Workflow (ENT-007) | dormant in Code | **formal pausiert** durch ENT-056 (revidiert ENT-007) |
| Budget (~$5–10/Monat) | gehalten | **gehalten** (Aggregat ~$1,50–3/Monat im Worst-Case) |

---

## 2 — Verdict pro Leitfrage (1–6)

> Leitfragen aus [workshop/README.md §Leitfragen](README.md). Pro Frage: Status (gut / okay / lückenhaft / kritisch), kurze Begründung, Backlog-Bezug.

### Leitfrage 1 — Ist der Knowledge Graph in seiner aktuellen Form (Markdown + Frontmatter + Wiki-Struktur) ausreichend für MVP-3 und darüber hinaus?
- **Status:** **okay** (mit Heilung).
- **Begründung:** Karpathy-Wiki-Pattern hält [01 §B1](01_ai_research.md). Bei 21 Wiki-Pages weit unter Schwellwert ([ENT-027](../doc/ENTSCHEIDUNGEN.md#ent-027-graph_reader-zweiphasig-qk-4)). Bootstrap-Phase ist exakt der Moment, in dem präzise graph_context-Treffer den größten Hebel hätten — und der Hebel kommt gleich (C1).
- **Backlog-Bezug:** **BL-04** (C1 Index-Reparatur — entriegelt Retrieval).

### Leitfrage 2 — Welche Routinen brauchen wir für Indexierung und Updates?
- **Status:** **lückenhaft.**
- **Begründung:** Index wird heute ohne Code-Pfad gepflegt → Drift sichtbar (Index meldet 18 PFs, FS hat 10). `index_updater` ist Phantom-Modul ([03 §C3 K3](03_architect.md)). Updates per `graph_writer.update` sind komplette Überschreibungen, kein Diff-Merge ([01 §A2(b)](01_ai_research.md)).
- **Backlog-Bezug:** **BL-04** (C1 + `agents/frontmatter.py`-Helper). Mittel-/Langfrist: BL-09 (C2 FTS5-Build).

### Leitfrage 3 — Wie funktioniert Retrieval heute, was fehlt für Fakten-Vergleich/-Konsolidierung?
- **Status:** **lückenhaft.**
- **Begründung:** Phase-1-Retrieval ist faktisch nur Slug-Token-Match, weil `index.md`-Summaries Slug-Replikate sind ([01 §A2(c)](01_ai_research.md)). Konsolidierung passiert nicht (Lint-Stub, [ENT-017](../doc/ENTSCHEIDUNGEN.md#ent-017-lintagent-mit-auto-fix-stubs)).
- **Backlog-Bezug:** **BL-04** (C1, repariert Summaries) + **BL-07** (C3 Lint-Auto-Fixes). Langfrist: BL-09 (C2 FTS5).

### Leitfrage 4 — Wie nutzen wir die Graph-Struktur für unerwartete Verknüpfungen / Insight-Generierung?
- **Status:** **lückenhaft, aber nicht heute akut.**
- **Begründung:** [ENT-010](../doc/ENTSCHEIDUNGEN.md#ent-010-korrelations-engine) Korrelations-Engine nicht implementiert; 0 Concepts. Auslöser ≥50 PFs, heute 10. **Nicht-heute-Schmerz** — der Hebel kommt erst bei Korpus-Wachstum.
- **Backlog-Bezug:** **C7 LazyGraphRAG-Concept-Cluster** → Radar-Item, Eintrag in [doc/CHANCEN.md](../doc/CHANCEN.md). Trigger: Korpus-Wachstum auf ≥50 PFs.

### Leitfrage 5 — Wie ist die Schnittstelle Graph ↔ Frontend (Telegram, Anki, künftige Renderer) — heute und im Soll?
- **Status:** **gut für heute, vorbereitet für morgen.**
- **Begründung:** Heute ist Anki der einzige Render-Konsument, mit Obsidian-Backlink im Anki-Back ([ENT-052](../doc/ENTSCHEIDUNGEN.md#ent-052-anki-card-identität-und-re-export-stabilität)). Workshop liefert: Render-Modul-Trennung (BL-05), `RenderDict`-Adapter-Vertrag (BL-05), Telegram-Echo nach Anki-Export (BL-06), Health-Tag (BL-06). **C5b zweiter Backlink** wurde von UX abgelehnt — Mobile-Bruch + Pixel-Verbrauch. **Multimodale Karten** (Audio-Replay, Bild) bleiben Backlog für später (im Renderer-Vertrag bedacht, nicht heute gezogen).
- **Backlog-Bezug:** **BL-05** (Render-Modul + RenderDict) + **BL-06** (Health-Tag + Telegram-Echo). MVP-3-Vorbereitung. Discord-Wochen-Replay bleibt Radar (siehe Anti-Decisions §3).

### Leitfrage 6 — Wie extrahieren wir Wissen aus Multi-Modal-Quellen (Foto, Video, Audio)?
- **Status:** **kritisch im Sinne von "schlafendes Risiko".**
- **Begründung:** Voice-Pfad live ([ENT-044](../doc/ENTSCHEIDUNGEN.md#ent-044-mvp-2-erstes-feature-voice-ingest)). Bilder/PDFs/URLs/YouTube-Extraktoren existieren, aber **keine Trigger im Bot**. **Ohne Sensitivity-ENT bricht jeder erste Bild-Drop den ENT-006-Vertrag** (Vision ist Cloud). Audio bleibt textbasiert ([ENT-024](../doc/ENTSCHEIDUNGEN.md#ent-024-audio-api-bug--v1-ohne-ton-coaching-qk-1)) — keine Änderung im Workshop, weil Claude-API immer noch keinen Audio-Input bietet (CHANCEN §4.3).
- **Backlog-Bezug:** **ENT-053 Sensitivity-Tier-Default für Bilder** (Pre-Req) → **BL-08** (C6 Multi-Modal-Backfill mit SHA1-Dedup §D1). YouTube/PDF folgen analog, später.

---

## 3 — Anti-Decisions-Sektion (was wir bewusst NICHT ändern)

> Pflicht-Sektion gemäß [Workshop-Charta](README.md). Mindestens 5 Punkte. Schützt MVP-3-Plan + nicht-verhandelbare Verträge.

1. **Karpathy-Prinzip bleibt nicht-verhandelbar.** Kein RAG, kein Vektor-Store. Kein Embedding-basiertes Retrieval. C7 (LazyGraphRAG) ist okay, weil NLP-statisch (Co-Occurrence-Graph + Community-Detection). Wenn jemand in MVP-3+ Embeddings einführen will: neuer ENT mit `revidiert: ENT-002`-Verweis erforderlich — kein "schleichendes" Hinzufügen.

2. **WikiWrite-Vertrag bleibt.** Der Wiki ist LLM-Schreib-Wiki. Workshop-Vorschläge mit deterministischen Direct-Writes (C4 Migration, C3 Lint-Auto-Fixes, C5a Health-Tag-Log) sind analog zu `anki_id`-Patch ([ENT-052](../doc/ENTSCHEIDUNGEN.md#ent-052-anki-card-identität-und-re-export-stabilität)) legitim — sie bleiben deterministisch und nicht-LLM. Ein neuer LLM-getriggerter Schreib-Pfad (z.B. Reflective-Pass aus 01 §B4) braucht eigene ENT-Diskussion.

3. **MVP-3-Stufung bleibt unangetastet.** Der Workshop liefert MVP-2-Zweitwelle, kein MVP-3-Vorzug. C7 (Concept-Cluster) und UX-C2 (Discord-Wochen-Replay) bleiben Radar / Backlog für MVP-3+. Beide kommen nach `doc/CHANCEN.md`.

4. **Bestehende ENTs bleiben gültig — Revisionen brauchen neue ENT-Nummer.** ENT-007 wird durch **ENT-056** formal pausiert (`revidiert: ENT-007`), nicht stillschweigend. ENT-027 wird **nicht** revidiert (Threshold-Wert `30` ist führend) — die Doku-Korrektur (ARCHITECTURE.md §6.3) ist Bestätigung, kein neuer ENT.

5. **Kein Refactoring der Supervisor-Architektur ohne separates ENT.** Der Hint-Gate-Pfad ([ENT-047](../doc/ENTSCHEIDUNGEN.md#ent-047-vocabentry-hint-gate-extraktion-nur-bei-hint-oder-deutsch-dominantem-input)/[ENT-048](../doc/ENTSCHEIDUNGEN.md#ent-048-ent-047-auslegung-hint-gate-nur-bei-gesetztem-language_detected)) bleibt unangetastet. Wenn C6 Multi-Modal Hint-Gate-Asymmetrie für Bilder einführt (ENT-053), ist das **eine** dokumentierte Asymmetrie zum Vocab-Hint-Gate, kein Architektur-Schwenk.

6. **C5b zweiter Backlink im Anki-Back bleibt abgelehnt.** UX-Verdict respektiert: Mobile-Bruch, Pixel-Verbrauch, kein Lerner-Mehrwert im Übungsmoment ([02 §B6](02_ux.md)). Die Symbiose Graph↔Card bleibt durch C5a (Health-Tag) und C1 (Telegram-Echo) bedient.

7. **Render-Layer-Inhalte (HTML/CSS in [02 §B2/B3](02_ux.md)) bleiben UX-Mandat.** Der Architekt hat Modul-Standort gewählt, **nicht** Inhalt. PO bestätigt UX-Vorschlag inhaltlich (Genus-Pillen, Mnemonic-Box, Sans-Serif-Typografie, Mobile-Breakpoint, Klartext-Pfad als Fallback). Implementierung passt sich UX an, nicht andersherum.

8. **AnkiConnect bleibt nicht-Pfad.** [ENT-050](../doc/ENTSCHEIDUNGEN.md#ent-050-anki-export-scope-quell-selektion-trigger-format) hat genanki gewählt. Eintrag "AnkiConnect nicht implementiert" wird aus `hinweise/technischer_hinweis.md` gestrichen (siehe §7 Hinweis-Update).

9. **Discord-Wochen-Replay bleibt Radar / MVP-3-Backlog.** Heute nicht ziehen — gekoppelt an [ENT-045](../doc/ENTSCHEIDUNGEN.md#ent-045-proaktiver-kanal-grundsätzlich-freigegeben-opt-in)-Aktivierung und Discord-Bot-Setup. Eintrag in [doc/CHANCEN.md](../doc/CHANCEN.md).

10. **C7 LazyGraphRAG-Concept-Cluster bleibt Radar.** Trigger: Korpus auf ≥50 PFs (heute 10). Bottom-up-Emergenz von Themen ist Designziel ([ENT-010](../doc/ENTSCHEIDUNGEN.md#ent-010-korrelations-engine)) — kommt automatisch, wenn der Korpus reift. Eintrag in [doc/CHANCEN.md](../doc/CHANCEN.md).

---

## 4 — Reaktion auf Vetos und Marker

> Pro `(!)ARCH-VETO(!)` / `(!)ENT-NÖTIG(!)` / `(!)ARCH-FRAGE(!)` aus [protokoll.md §Veto-/ENT-Marker](protokoll.md): angenommen / abgelehnt / verschoben + Begründung.

| # | Quelle | Marker | PO-Verdict | Begründung |
|---|---|---|---|---|
| M1 | `01 §C4` | (!)ARCH-FRAGE(!) Migration vs. Draft→Master | **angenommen — Migration darf direkt schreiben** | Architekt-Empfehlung: Pattern existiert (analog `anki_id`-Patch), idempotent + Backup-Branch + `anki_id`-Hash-Snapshot. ENT-007 wird sowieso pausiert (ENT-056), Reibung damit obsolet. |
| M2 | `01 §C5` | (!)ENT-NÖTIG(!) Persistenz `out/` vs. Wiki | **angenommen → ENT-054** | `out/anki_export_log.json` (gitignored). WikiWrite-Vertrag-Schutz (kein zweiter Frontmatter-Sonderweg neben `anki_id`), Atomarität, Diff-Sauberkeit. Cold-Start nach Löschung akzeptabel. |
| M3 | `01 §C6` | (!)ENT-NÖTIG(!) Sensitivity-Tier für Bilder | **angenommen → ENT-053** | QM-verschärfte Variante: Default = Quick-Save in `raw/assets/` ohne Hint, Auto-Ingest mit Vision-Call **nur** mit explizitem Hint (`#bild` oder `#vision`). Asymmetrisch zu ENT-047/048 — bewusst, weil Privacy-Default stärker schützt. |
| M4 | `02 §B5` | (!)ENT-NÖTIG(!) IPA-Slot Schema-Erweiterung | **angenommen → ENT-055** | Frontmatter-Feld `ipa: <string\|null>`, optional, sprachspezifisch. Renderer skipt leer. Keine Backfill-Pflicht. Language-Agent füllt bei Neu-Erstellung. |
| M5 | `02 §B5` | (!)ARCH-FRAGE(!) Render-Modul `scripts/` vs. `agents/render/` | **angenommen — `agents/render/`** | Architekt-Override gegen UX-Vorschlag, mit Begründung Multi-Konsumenten ([ENT-049](../doc/ENTSCHEIDUNGEN.md#ent-049-zweit-oberflächen-strategie-telegram-bleibt-primär-cli-discord-e-mail-vorgemerkt-für-mvp-3)). Modul-Hygiene-Frage, kein neuer ENT (Architekt-Autorität, gemäß Rollen-Kopf). |
| M6 | `02 §C1` | (!)ARCH-FRAGE(!) Bot-Token paralleler Send vs. Polling | **angenommen — kein Konflikt** | Architekt-Verdict: `sendMessage` ist multi-client; nur `getUpdates` ist exklusiv. CLI-Skript erstellt eigenen Bot-Client, kein Webhook, kein `getUpdates`. Risiko vernachlässigbar. |

**Keine harten ARCH-VETOs zu adressieren** ([03 §Zusammenfassung](03_architect.md)). Das Workshop-Ergebnis ist innerhalb aller bestehenden Verträge.

---

## 5 — Reaktion auf QK-Vorschläge (QK-8 bis QK-14)

> Pro QK aus [04_qm.md §C1](04_qm.md): angenommen / abgelehnt + Begründung. Angenommene QKs werden zu ENT (wo formal nötig) oder bleiben workshop-intern dokumentiert.

| QK | Inhalt | PO-Verdict | Aktion |
|---|---|---|---|
| **QK-8** | Frontmatter-Migration als P1-Pflicht-Schritt mit drei Auflagen (Backup-Branch, Idempotenz-Test, `anki_id`-Hash-Snapshot) | **angenommen** | Workshop-intern: BL-03 mit drei Pflicht-Auflagen. Kein eigener ENT — ENT-052 deckt `anki_id`-Erhaltungspflicht bereits, ENT-056 deckt Direct-Write-Legitimation. |
| **QK-9** | Sensitivity-Tier-Default für Bilder (Pre-Req für C6) | **angenommen, in QM-Variante** | **ENT-053** in `doc/ENTSCHEIDUNGEN.md` (siehe §6 unten). Default = Quick-Save ohne Hint, Auto-Ingest mit explizitem Hint. |
| **QK-10** | `out/anki_export_log.json` als Persistenz-Pfad | **angenommen** | **ENT-054** in `doc/ENTSCHEIDUNGEN.md`. |
| **QK-11** | Render-Modul-Standort `agents/render/` statt `scripts/` | **angenommen, kein ENT** | Workshop-intern: BL-05 verortet das. Modul-Hygiene = Architekt-Autorität. |
| **QK-12** | ARCHITECTURE.md §6.3 Threshold-Korrektur auf `30` (führend) | **angenommen** | BL-11 (Doku-Korrekturen). Kein neuer ENT — ENT-027 bleibt führend, Doku-Konsistenz wird hergestellt (ARCHITECTURE.md §6.3 + `graph_reader.py:3-4` Header-Kommentar). |
| **QK-13** | ENT-007 formale Pause für MVP-2-Zweitwelle | **angenommen** | **ENT-056** in `doc/ENTSCHEIDUNGEN.md` mit `revidiert: ENT-007`-Verweis. Re-Aktivierungs-Trigger: LLM-getriggerte Wiki-Writes mit Halluzinations-Risiko (post-MVP-3). |
| **QK-14** | Test-Strategie etablieren (`tests/`-Struktur als Pre-Req) | **angenommen** | Workshop-intern: BL-02 (Test-Skelett). `requirements.txt` ergänzen um `pytest`, `pytest-snapshot`. Kein eigener ENT — Test-Strategie ist Engineering-Konvention, kein Architektur-Beschluss. |

**Zusätzlich** (vom QM in [04 §Empfehlungen Punkt 9](04_qm.md) gefragt): **Sonnet für C8 User-Profile-Refresh ist OK.** Begründung: interner wöchentlicher Lint-Pass, kein proaktiv-impulsiver Outbound-Kanal — nicht ENT-045-tangiert. ~$0,20/Monat im Budget. PO bestätigt formal.

---

## 6 — Top-3-Workshop-Insights

> Was nimmt die Organisation aus diesem Workshop dauerhaft mit — auch wenn keine Implementierung folgt?

### Insight 1: **Frontmatter-Schuld ist Erbe-Risiko, nicht lokales Symptom.**
Die 7 elaborierten Vocab-Files mit kaputtem YAML wirken zunächst wie ein Anki-Renderer-Problem. Der Workshop hat klar gemacht: **jeder neue Render-Konsument** (Discord-Embed, E-Mail-Digest, Telegram-Inline-Echo, Story-Lab-Vocab-Anbindung, Lint-Auto-Fixes) **erbt den Regex-Workaround**, wenn Migration nicht zuerst läuft. Kosten skalieren mit Konsumenten-Zahl, nicht mit Daten-Volumen. Diese Sicht hilft auch außerhalb dieses spezifischen Bugs: **Frontmatter-Korruption ist immer Konsumenten-multiplikativ.** Architektur-Lehre: Single-Source-Helper (`agents/frontmatter.py`) ist die richtige Antwort, nicht Workaround-Vermehrung.

### Insight 2: **Der Workshop hat vier Pre-Workshop-Inkonsistenzen aufgedeckt, die älter sind als der Workshop.**
`graph_writer.py:55-65` (Branch-Bug `main`/`master`), `WIKI_PAGE_THRESHOLD` 30 vs. 150 in ARCHITECTURE.md, `index_updater`-Phantom-Modul, Draft-Branch dormant — alle vier sind keine Workshop-Artefakte, sondern Schulden des MVP-2-Erstwellen-Stands. Das ist das **wertvollste Nebenprodukt** eines Tiefenchecks: er findet, was Implementierungs-Sessions übersehen, weil sie auf Feature-Lieferung optimieren. Die Lehre für künftige Workshops: **explizit Doku-/Code-/Vertrag-Konsistenz als eigenes Audit-Item ausweisen** — nicht als Nebenfund hoffen.

### Insight 3: **"Synthese mit Auflagen" ist das richtige Format für reifende MVP-Stände.**
Der QM hätte "Vollabnahme" oder "Blocker" geben können. Beides wäre falsch gewesen — Vollabnahme hätte vier P1-Befunde in den nächsten Implementierungs-Schritt geschoben, Blocker hätte einen heilbaren Stand künstlich aufgehalten. Das **Synthese-mit-Auflagen-Pattern** (Workshop läuft durch, fünf Auflagen werden in der Synthese-Phase sauber adressiert) ist ein Format, das man für künftige Phasen-Übergänge wiederverwenden sollte. Lehre: **QM-Urteile nicht als binär "go/no-go" denken** — die Granularität "OK mit dokumentierten Auflagen" produziert besseren Output bei reifenden Systemen.

---

## 7 — Reihenfolge der Implementierung (PO-bestätigt)

> Aus [03 §Implementierungs-Reihenfolge](03_architect.md), QM-bestätigt in [04 §Empfehlungen Pflicht-Reihenfolge-Treue](04_qm.md), PO-bestätigt hier.

```
0. BL-01  graph_writer.py-Branch-Bug-Fix (main → master, drei Stellen + zwei Doc-Strings)
0b. BL-02 Test-Skelett (tests/ + pytest + pytest-snapshot)
0c. BL-?  drei ENT-NEUs in doc/ENTSCHEIDUNGEN.md (ENT-053/054/055/056) — passiert in dieser Synthese, siehe §8.

1. BL-03  C4 Frontmatter-Migration (mit Backup-Branch + Idempotenz-Test + anki_id-Snapshot)
2. BL-04  C1 Index-Reparatur + agents/frontmatter.py-Helper
3. BL-05  Render-Modul agents/render/card.py + RenderDict-Vertrag (B9+B10)
4. BL-06  C5a Health-Tag + B11 Telegram-Echo (gemeinsam)
5. BL-07  C3 Lint-Auto-Fixes (3 Detektoren)
6. BL-09  C2 SQLite-FTS5-Build-Skript (Pre-Req: BL-11 Doku-Korrektur)
7. BL-08  C6 Multi-Modal-Backfill (Pre-Req: ENT-053)
8. BL-10  C8 User-Profile Self-Refresh (optional, nach BL-07)

Parallel/Begleitend:
   BL-11  ARCHITECTURE.md Doku-Korrekturen (Threshold + Header + index_updater)
   BL-12  scripts/migrations/-Pattern + applied.json (mit BL-03 etablieren)

Radar (CHANCEN):
   C7 LazyGraphRAG Concept-Cluster — Trigger ≥50 PFs
   UX-C2 Discord-Wochen-Replay — Trigger ENT-045-Aktivierung
   E2E-Test-Pipeline — Trigger BL-08 (Multi-Modal)
```

**MVP-2-Zweitwelle Aufwand:** ~39h Architekt-Aufwand (Schritte 1–8) + Test/Doku-Overhead +30%, also realistisch ~50h. Auf mehrere Sessions verteilt.

---

## 8 — Was passiert in dieser Synthese-Phase konkret

PO-Lieferung in dieser Session 025 (PO-Phase 5):

1. ✅ Diese Datei `workshop/05_po_synthesis.md` (Liefer-Punkt 1).
2. ✅ `workshop/backlog.md` mit 13 Einträgen (Liefer-Punkt 2).
3. ✅ Vier ENT-Einträge ergänzt in `doc/ENTSCHEIDUNGEN.md` (ENT-053, ENT-054, ENT-055, ENT-056) (Liefer-Punkt 3).
4. ✅ Drei Einträge ergänzt in `doc/CHANCEN.md` (C7 LazyGraphRAG, UX-C2 Discord-Replay, E2E-Test-Investment) (Liefer-Punkt 4).
5. ✅ `sessions/025_2026-05-08.md` Ergebnis-Notizen gefüllt (Liefer-Punkt 5).
6. ✅ `sessions/026_2026-05-09.md` als Brief an Architekt geschrieben (Liefer-Punkt 6).
7. ✅ `hinweise/technischer_hinweis.md` aktualisiert (Liefer-Punkt 7) — neue Schulden + behobene Schulden + AnkiConnect-Eintrag gestrichen.
8. ✅ `workshop/protokoll.md` PO-Verdicts-Sektion gefüllt + Beitrags-Index Phase 5 ergänzt.

---

## 9 — Was diese Synthese **nicht** macht

- **Kein Code, kein Detail-Review, keine Architektur-Diskussion innerhalb dieses Files.** Nur Was und Warum. Skizzen-Code in 03/04 bleibt dort.
- **Kein ENT für Render-Modul-Standort, Test-Skelett, Frontmatter-Migration-Auflagen, Doku-Korrekturen** — alles workshop-intern bzw. Architekt-Autorität, kein PO-Beschluss-Bedarf.
- **Keine retroaktive Modifikation von 01–04** außer Tippfehler-Fixes. Die Vetos und Befunde stehen wie sie stehen.
- **Keine Bewertung von Code-Qualität** (war QM-Territorium, [04](04_qm.md)).
- **Kein neuer Stop-Kriterien-Check** — QM hat "Synthese mit Auflagen" gegeben, nicht "Blocker". Workshop läuft glatt durch.

---

## Liefer-Status

- [x] Synthese der 4 Rollen-Beiträge (§1)
- [x] Verdict pro Leitfrage 1–6 (§2)
- [x] Anti-Decisions-Sektion mit 10 Punkten (§3)
- [x] Reaktion auf Vetos und Marker (§4)
- [x] Reaktion auf QK-Vorschläge (§5)
- [x] Top-3-Workshop-Insights (§6)
- [x] Reihenfolge-Bestätigung (§7)
- [x] Konkrete Liefer-Liste (§8)

**Workshop offiziell geschlossen am 2026-05-08.** Implementierungs-Pfad zurück zum normalen Session-Rhythmus (S026 startet mit Architekt-Auftrag).
