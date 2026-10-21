# Handover: UX → Architekt
> Erstellt: 2026-05-08 | von: UX | an: Architekt | Workshop: [README](../README.md)

---

## Was du aus 02_ux.md zwingend lesen musst

- **[02_ux.md §B1 Template-System-Konzept](../02_ux.md)** — *Ein Notetype, vier Slot-Profile.* Heuristik-Tabelle (A/B/C/D) ist die UX-Empfehlung; bitte prüfen, ob die Auslöser-Bedingungen vollständig sind (Edge-Case Adverben, defektive Verben, IPA-Vorhandensein).
- **[02_ux.md §B5 Schnittstelle Markdown → HTML](../02_ux.md)** — Mapping-Tabelle Frontmatter+Body → Slots, plus die Empfehlung **`scripts/render_card.py` als eigenes Modul**. Das ist deine Architektur-Entscheidung.
- **[02_ux.md §B6 Mobile vs. Desktop](../02_ux.md)** — der `obsidian://`-Backlink-Bruch auf Anki Mobile (S024-Befund) ist der einzige nicht-verhandelbare UX-Punkt im File. Klartext-Pfad als zweite Zeile ist Pflicht.
- **[02_ux.md §C3 Render-Adapter-Vertrag](../02_ux.md)** — `RenderDict`-Skizze mit `identity`, `content`, `display`, `links` als Mindest-Vertrag für künftige Render-Konsumenten ([ENT-049](../../doc/ENTSCHEIDUNGEN.md#ent-049-zweit-oberflächen-strategie-telegram-bleibt-primär-cli-discord-e-mail-vorgemerkt-für-mvp-3) Discord/E-Mail).
- **[02_ux.md §Empfehlungen für Architekt-Phase](../02_ux.md)** — sieben Punkte, alle bindend (mindestens als Diskussionspunkte).
- **[02_ux.md §Antizipierte Skepsis Architekt](../02_ux.md)** — drei Punkte, zu denen ich Argumente vorbereitet habe; gerne Gegenrede.

---

## Konkrete Aufträge für den Architekten

### Auftrag 1 — Render-Architektur-Entscheidung

**Was:** Bestimmen, ob die Render-Logik in einem neuen `scripts/render_card.py` lebt oder in [scripts/export_anki.py](../../scripts/export_anki.py) bleibt.

**UX-Vorschlag:** eigenes Modul. Begründung in [02_ux.md §B5](../02_ux.md): Test-Determinismus, Erweiterbarkeit für Discord/E-Mail-Konsumenten ([ENT-049](../../doc/ENTSCHEIDUNGEN.md#ent-049-zweit-oberflächen-strategie-telegram-bleibt-primär-cli-discord-e-mail-vorgemerkt-für-mvp-3)), Trennung Render-Lebenszyklus von Sync-Lebenszyklus ([ENT-050](../../doc/ENTSCHEIDUNGEN.md#ent-050-anki-export-scope-quell-selektion-trigger-format)/[ENT-052](../../doc/ENTSCHEIDUNGEN.md#ent-052-anki-card-identität-und-re-export-stabilität)).

**Was du entscheidest:**
- Modul-Standort und Namensraum (`scripts/render_card.py` oder `agents/render/` oder anderes).
- Schnittstelle der Render-Funktionen (`render_front`, `render_back`, `pick_profile`, `CSS_BLOCK`-Konstante).
- Snapshot-Test-Strategie (pytest-snapshot? rohe Stringvergleiche?).

**Was du *nicht* entscheidest:** den HTML/CSS-Inhalt (siehe [02_ux.md §B2/B3](../02_ux.md)). Das ist UX-Empfehlung.

### Auftrag 2 — Felder-Maps prüfen (Frontmatter ↔ Slot)

**Was:** Mapping-Tabelle in [02_ux.md §B5](../02_ux.md) gegen das aktuelle Schema ([SCHEMA.md §3](../../doc/de/SCHEMA.md), [v_es_madrugada.md](../../wiki/language/vocab/v_es_madrugada.md), [v_es_duende.md](../../wiki/language/vocab/v_es_duende.md)) prüfen.

**Konkrete Prüfpunkte:**
1. **`pos` (Word-Klasse)** — heute extrahiert der Renderer kein `pos`. Body-Sektion `## Grammatik > **Typ:** Verb|Nomen|…` ist da. UX schlägt vor, das in den Renderer aufzunehmen für Profil-D-Switch. Prüfen: Regex stabil? Was bei mehreren `**Typ:**`-Zeilen?
2. **`ipa` (Lautschrift)** — heute *nicht* im Schema. UX-`[TODO]`: bevorzugt Frontmatter-Feld `ipa: "[ˈdwen.de]"`. Prüfen: ist das eine Schema-Änderung wert? Wenn ja, `[ENT-NEU?]` markieren und in PO-Synthese tragen. Wenn nein, IPA bleibt aus B2/B3-Mockups raus, kein Drama.
3. **`updated`-Vergleich für Health-Tag** (siehe Auftrag 4) — wo wird der letzte Anki-Export-Zeitstempel persistiert? UX-Vorschlag: `out/anki_export_log.json` (gitignored). Architekt-Alternative wäre `usage_stats: { last_anki_export: ... }` im VocabEntry-Frontmatter (graph-nativ, aber jeder Export schreibt Wiki — Bedenken?).

### Auftrag 3 — `RenderDict`-Vertrag (Adapter-Schnittstelle)

**Was:** Die in [02_ux.md §C3](../02_ux.md) skizzierte Adapter-Struktur (`identity` / `content` / `display` / `links`) als gemeinsame Datenstruktur für *alle* Render-Konsumenten festlegen.

**UX-Empfehlung:** Dataclass oder TypedDict in `render_card.py`. Pydantic wäre overkill für diese statische Struktur.

**Was du entscheidest:**
- Datentyp (Dataclass / TypedDict / Pydantic).
- Pflicht- vs. Optional-Felder pro Sektion (UX-Vorschlag in §C3).
- Adapter-Funktion `vocab_record_to_render_dict(rec: VocabRecord) -> RenderDict`.

**Was du *nicht* entscheidest:** wie viele Render-Konsumenten es gibt. Heute einer (Anki). Für MVP-3 vorgemerkt (Discord, E-Mail). Der Vertrag muss *hinreichend* für künftige sein, nicht *vollständig*.

### Auftrag 4 — Health-Tag `health::stale-mnemonic` (C5a)

**Was:** Annahme der UX-Empfehlung **C5a**: Anki-Tag `health::stale-mnemonic` setzen, wenn `frontmatter.updated > anki_export_log.last_run` für eine Vocab-Datei.

**Was du entscheidest:**
- Persistenz-Ort des Zeitstempels (siehe Auftrag 2.3).
- Zeitvergleich-Toleranz (z.B. ±1 Tag, um Zeitzonen-Drift zu schlucken).
- Tag-Schema: `health::stale-mnemonic` (UX-Vorschlag) oder anderer Name? Konsistenz mit künftigen Health-Tags (`health::missing-example`, etc.) bedenken.

**Was du *nicht* entscheidest:** *ob* der Tag kommt. UX hat ja gesagt; AI-Research empfiehlt es ([01_ai_research §C5](../01_ai_research.md)). Wenn du Veto siehst (`(!)ARCH-VETO(!)`), bitte in [02_ux.md](../02_ux.md) markieren.

### Auftrag 5 — Reihenfolge: Frontmatter-Schuld zuerst

**Bindend:** Frontmatter-Schuld-Migration ([01_ai_research §C4](../01_ai_research.md)) **vor** allem anderen Render-Layer-Refactor.

**Begründung:** der Renderer schleppt heute schon einen Regex-Workaround mit ([scripts/export_anki.py:79-131](../../scripts/export_anki.py#L79-L131)). Jeder neue Render-Konsument (Telegram-Echo, Discord, E-Mail-Digest) erbt diesen Workaround, wenn die Migration nicht zuerst läuft. Kosten skalieren mit Konsumenten-Zahl.

**Konkrete Migrations-Skript-Vorschlag (aus [01_ai_research §C4](../01_ai_research.md)):** `scripts/migrate_vocab_frontmatter.py` mit pyyaml-Roundtrip. Architekt entscheidet final.

**Risiko:** Migration ist destruktiv. UX bittet um Backup-Branch vor Lauf. `anki_id` muss stabil bleiben — sonst SRS-State-Verlust gemäß [ENT-052](../../doc/ENTSCHEIDUNGEN.md#ent-052-anki-card-identität-und-re-export-stabilität).

### Auftrag 6 — IPA-Schema-Frage (`[ENT-NEU?]`-Kandidat)

**Was:** Entscheiden, ob ein `ipa`-Feld ins VocabEntry-Schema kommt (Frontmatter oder Body-Sektion) — für Profil-A/B-Karten, die auf Wort + Aussprache fokussieren.

**UX-Empfehlung:** Frontmatter-Feld `ipa: "[ˈdwen.de]"`. Begründung: robust gegen Body-Edits, leichtes Mapping zu Slot, Anki-Render und Discord-Embed nutzen denselben Wert.

**Wenn du das ziehst:** in PO-Synthese als `[ENT-NEU?]` tragen, weil [SCHEMA.md §3](../../doc/de/SCHEMA.md) Schema-Schwenk ist.

**Wenn du das *nicht* ziehst:** B2/B3-Mockups bleiben gültig, IPA-Block fehlt einfach, kein Bruch.

---

## Was UX *nicht* entscheidet (Scope-Schutz)

- **Sync-Schicht** ([ENT-050](../../doc/ENTSCHEIDUNGEN.md#ent-050-anki-export-scope-quell-selektion-trigger-format)/[ENT-052](../../doc/ENTSCHEIDUNGEN.md#ent-052-anki-card-identität-und-re-export-stabilität) genanki + GUID-Strategie). UX hat gelesen und respektiert sie; keine Änderungen vorgeschlagen.
- **Lint-Algorithmen** — Architekt-Auftrag, UX flaggt nur, dass C5a (Health-Tag) implizit den Vergleich `updated`-vs-`anki_export_log` braucht.
- **Phase-2-SQLite-Indexer** — kein UX-Anteil.
- **Provider-Strategie** (Haiku/Sonnet/Ollama) — UX-Vorschläge sind bewusst *modell-frei* gehalten; deterministisches Render hat keinen LLM-Call.
- **Karpathy-Prinzip-Diskussion** — alle UX-Vorschläge sind innerhalb. Keine Vektor-Stores, kein RAG, keine eigene App ohne Telegram-Bedarfsnachweis.

---

## UX-Empfehlungen, zu denen Architekt-Verdict erbeten ist

| UX-Empfehlung | Architekt-Aktion gewünscht |
|---|---|
| `scripts/render_card.py` als neues Modul | Akzeptieren / Veto / Veränderter Standort |
| `RenderDict`-Vertrag (§C3) | Akzeptieren / Vereinfachen / Verwerfen |
| Health-Tag `health::stale-mnemonic` (C5a annehmen) | Tag-Name OK? Persistenz-Ort? |
| Zweiter Backlink C5b ablehnen | Akzeptieren / Architektur-Argument für Ja? |
| IPA als Frontmatter-Feld `[ENT-NEU?]` | Schema-Schwenk wert oder zu früh? |
| Klartext-Pfad als Mobile-Fallback (§B6) | Form: relativer / absoluter / `repo://`-Pfad? |
| C2 Discord-Outbound `[MVP-3]` | Vormerken oder als `[RADAR]` weiter zurückstufen? |

---

## Schnittstelle Wiki↔Render — was ich für die Render-Architektur-Diskussion beitrage

**Beobachtung 1:** Heute gibt es genau einen Render-Konsumenten ([scripts/export_anki.py](../../scripts/export_anki.py)). Der Render-Code ist mit der Genanki-Pipeline und dem Frontmatter-Patch (`anki_id`-Back-Write) in derselben Datei verklebt. Das war für ENT-052 die richtige Entscheidung; für MVP-3 (Discord/E-Mail) wird sie zur Bremse.

**Beobachtung 2:** Der Renderer ist deterministisch — das ist unsere Stärke ggü. RemNote/Mochi (siehe [02_ux.md §B4 Q4](../02_ux.md)). Eine Trennung in eigenes Modul behält diese Stärke und fügt Test-Determinismus hinzu.

**Beobachtung 3:** Der `RenderDict`-Vertrag (§C3) ist der minimale Fingerabdruck eines VocabEntry, der für *jeden* Render-Konsumenten reicht. Wenn der Architekt diesen Vertrag annimmt, wird der zweite Render-Konsument (Discord, in MVP-3) eine reine Adapter-Aufgabe und kein Wiki-Body-Re-Parsing.

**Mein Bias:** Ich bin UX, nicht Architekt — wenn meine Modul-Trennungs-Empfehlung gegen ein Architektur-Prinzip verstößt, das ich nicht sehe, **bitte ohne Zögern verwerfen**. Die Render-Inhalts-Empfehlungen (HTML/CSS in §B2/B3, Slot-Profile in §B1) bleiben davon unberührt — sie funktionieren, egal wo das Modul lebt.

---

## Übergabe-Status

- [x] [02_ux.md](../02_ux.md) geschrieben (Teil A + B + C + Empfehlungen + Skepsis + Quellen).
- [x] 8 externe Quellen zitiert (Soll ≥ 3).
- [x] 2 HTML+CSS-Karten-Varianten konkret entworfen (§B2 Profil A, §B3 Profil C).
- [x] Mindestens **eine** Variante zeigt elegante Eselsbrücken-Render (§B3 `aside.mnemonic`).
- [x] Render-Layer-Schnittstelle Markdown→HTML spezifiziert (§B5).
- [x] Mobile vs. Desktop konkret benannt mit Befund (§B6).
- [x] Drei Symbiose-Vorschläge (§C1–C3, alle markiert mit Aufwand + MVP-Stufe).
- [x] Reihenfolge-Hinweis (Frontmatter-Schuld zuerst) in dieser Handover-Datei §Auftrag 5 verankert.
- [x] Querverweise an Architekt in [protokoll.md](../protokoll.md) eingetragen.
- [ ] Git-Commit (passiert nach Schreibe-Schluss von protokoll.md).

**Bereit für Phase 3.** Architekt-Session kann mit frischer Claude-Code-Session und [prompts/03_architect_prompt.md](../prompts/03_architect_prompt.md) starten.

---

## Anti-Erwartungen

- Architekt darf alle UX-Vorschläge ablehnen, sofern Begründung gegeben. UX-Radar-Modus: ich blockiere nichts.
- Architekt darf Veto-Marker `(!)ARCH-VETO: [Grund](!)` direkt in [02_ux.md](../02_ux.md) setzen, *bevor* er sein eigenes File schreibt — laut Workshop-Charta § "Architekt darf bereits in 01 und 02 Stellen markieren".
- Architekt darf `[ENT-NEU?]` markieren (z.B. für IPA, für `health::*`-Tag-Schema), Entscheidung liegt beim PO in Phase 5.
