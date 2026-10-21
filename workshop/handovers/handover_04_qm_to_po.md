# Handover: QM → PO
> Erstellt: 2026-05-08 | von: QM | an: Product Owner | Workshop: [README](../README.md)

---

## Meilenstein-Urteil: **Synthese mit Auflagen**

> Detail in [04_qm.md §C2](../04_qm.md). Auflagen sind in §Pflicht-ENT-Liste / §Pflicht-Backlog-Aufnahme / §Pflicht-Reihenfolge-Treue dieses Handovers nochmals kompakt.

---

## P1-Liste (oben, Pflicht-Lesung)

| # | ID | Befund | Mitigation | Quelle |
|---|---|---|---|---|
| 1 | R1 | `graph_writer.py:55-65` schreibt `git checkout main` — Branch ist `master` ([ENT-039](../../doc/ENTSCHEIDUNGEN.md#ent-039-branch-namen-konvention-master-vs-main)). `reject_draft()` würde brechen. | Trivialer Fix, drei Strings + zwei Doc-Strings. **Schritt 0** der Implementierungs-Session 026. | [04_qm.md §B1 R1](../04_qm.md), QM-verifiziert |
| 2 | R2 | C4 Frontmatter-Migration ist destruktiv (7 elaborierte Vocab-Files), `anki_id`-Erhaltung ist nicht-reparabel bei Bruch ([ENT-052](../../doc/ENTSCHEIDUNGEN.md#ent-052-anki-card-identität-und-re-export-stabilität)). | **Drei Auflagen Pflicht:** Backup-Branch + Idempotenz-Test + `anki_id`-Hash-Snapshot. Siehe QK-8. | [04_qm.md §B1 R2](../04_qm.md) |
| 3 | R3 | C6 Multi-Modal bricht [ENT-006](../../doc/ENTSCHEIDUNGEN.md#ent-006-sensitivity-tier-modell-provider-routing) ohne Tier-Default für Bilder. Vision-API ist Cloud. | Pre-Req: ENT-NEU für Sensitivity-Default + Hint-Gate-Mechanik. Siehe QK-9. | [04_qm.md §B1 R3](../04_qm.md) |
| 4 | R4 | `tests/`-Struktur fehlt komplett — vier destruktive Workshop-Schritte (C4, C3, C6, Render) brauchen Test-Pattern vor Live-Schalten. | Test-Skelett als Pre-Implementierungs-Schritt. Siehe QK-14. | [04_qm.md §B1 R4](../04_qm.md) |

**Keine P0-Befunde** (Workshop-Output ist nicht abzulehnen).
**Kein Vollblocker** (alle vier P1 sind heilbar in der PO-Synthese ohne Aufschiebung).

---

## ENT-Bedarfs-Liste

| # | ENT-Vorschlag | Quelle | QM-Empfehlung |
|---|---|---|---|
| ENT-NEU-A | Sensitivity-Tier-Default für Bilder (Pre-Req C6) | QK-9 / [03 §A1 [01 §C6]](../03_architect.md) | Default `sensitive` + Quick-Save ohne Hint, Auto-Ingest mit explizitem `#bild`/`#vision`. **Asymmetrisch** zu ENT-047/048 — bewusst, weil Privacy-Default. |
| ENT-NEU-B | `out/anki_export_log.json` als Persistenz-Pfad für Health-Tag | QK-10 / [03 §A1 [01 §C5]](../03_architect.md) | Architekt-Empfehlung annehmen. Cold-Start nach `out/`-Löschung akzeptabel. |
| ENT-NEU-C | IPA-Frontmatter-Slot in [SCHEMA.md §3.2](../../doc/de/SCHEMA.md) | R11 / [03 §A1 [02 §B5 IPA]](../03_architect.md) | Optional, sprachspezifisch. Frontmatter-Feld `ipa: <string\|null>`. Keine Backfill-Pflicht — Renderer skipt leer. |
| ENT-007-Update | Status-Update für Draft→Master-Workflow | QK-13 / [03 §D5](../03_architect.md) | Formale Pause für MVP-2-Zweitwelle. Re-Aktivierungs-Trigger: LLM-getriggerte Lint-Fixes mit Halluzinations-Risiko (post-MVP-3). |
| ENT-027-Status | Threshold `30` ist führend, ARCHITECTURE.md korrigieren | QK-12 / [03 §C3 K2](../03_architect.md) | Doku-Korrektur an drei Stellen (ARCHITECTURE.md §6.3, graph_reader.py Header). Kein neuer ENT, nur Konsistenz-Bestätigung mit ENT-027. |

---

## Anti-Decisions-Empfehlungen (was bewusst NICHT geändert wird)

> Pflicht-Sektion in [05_po_synthesis.md](../05_po_synthesis.md) gemäß Workshop-Charta.

1. **Karpathy-Prinzip** bleibt nicht-verhandelbar. Kein Vektor-Store, kein RAG. C7 (LazyGraphRAG) bleibt Karpathy-konform (NLP-statisch).
2. **Discord-Wochen-Replay (UX-C2)** bleibt MVP-3-Backlog. Heute nicht ziehen, gekoppelt an [ENT-045](../../doc/ENTSCHEIDUNGEN.md#ent-045-proaktiver-kanal-grundsätzlich-freigegeben-opt-in)-Aktivierung.
3. **C7 Concept-Cluster** bleibt Backlog ≥50 PFs. Heute 10.
4. **C5b zweiter Backlink** im Anki-Back bleibt abgelehnt (UX-Verdict). Mobile-Bruch + Pixel-Verbrauch + kein Lerner-Mehrwert.
5. **Render-Layer-Inhalte** (HTML/CSS in [02 §B2/B3](../02_ux.md)) bleiben unverändert UX-Mandat — der Architekt hat Modul-Standort gewählt, **nicht** Inhalt.
6. **AnkiConnect-Eintrag in `hinweise/technischer_hinweis.md`** ist obsolet — ENT-050 hat genanki-Pfad gewählt. Eintrag streichen (siehe [04_qm.md §Aktualisierungs-Vorschlag](../04_qm.md)).

---

## Reihenfolge-Treue (nicht-verhandelbar)

> [03 §Implementierungs-Reihenfolge](../03_architect.md), QM-bestätigt.

```
0. graph_writer.py-Branch-Bug fixen (R1)               ← Pre-Workshop-Schuld, Schritt 0
0b. Test-Skelett anlegen (QK-14)                        ← Pre-Implementierungs-Pflicht
0c. ENT-NEU-A/B/C in doc/ENTSCHEIDUNGEN.md (PO)         ← QK-9, QK-10, QK-11

1. C4 Frontmatter-Migration                             ← Pre-Req für alles
2. C1 Index-Reparatur + agents/frontmatter.py-Helper    ← entriegelt Retrieval
3. Render-Modul (B9+B10) agents/render/card.py          ← Pre-Req für 4
4. C5a Health-Tag + B11 Telegram-Echo                   ← gemeinsam
5. C3 Lint-Auto-Fixes                                   ← braucht ENT-007-Status (QK-13)
6. C2 SQLite-FTS5-Build                                 ← braucht QK-12-Korrektur
7. C6 Multi-Modal                                       ← braucht ENT-NEU-A
8. C8 User-Profile Self-Refresh                         ← optional, nach 5
```

**MVP-3-Backlog:** C7 (Concept-Cluster), UX-C2 (Discord-Wochen-Replay).

**PO darf Schritte 0/0b/0c vorziehen** (das ist hilfreich).
**PO darf nicht** Schritte 1–8 umsortieren ohne Abhängigkeit zu adressieren.

---

## Was QM *nicht* entscheidet (Scope-Schutz)

- **Was als "gut genug" gilt** — Scope-Wahl ist PO. QM legt Risiken offen, PO entscheidet, was im Backlog landet.
- **Architektur-Wahl als Fix** — z.B. `agents/render/` vs. `scripts/` ist Architekt-Empfehlung, QM hat in QK-11 nur ratifiziert.
- **Anti-Decisions formulieren** — QM-Empfehlung ist Vorschlag, PO formuliert final in 05.
- **ENT-Einträge schreiben** — QM nennt ENT-Bedarf, PO schreibt nach `doc/ENTSCHEIDUNGEN.md`.
- **Budget-Erweiterung** — wenn PO sagt "C8 wöchentlich Sonnet OK", ist das PO-Beschluss, nicht QM.

---

## QM-Empfehlungen, zu denen PO-Verdict erbeten ist

| QM-Empfehlung | PO-Aktion gewünscht |
|---|---|
| **QK-8** Frontmatter-Migration mit drei Auflagen als Pre-Req | Annehmen / verändern / ablehnen (mit Begründung) |
| **QK-9** Sensitivity-Default `sensitive` + Quick-Save ohne Hint | ENT-NEU-Eintrag schreiben — Default + Hint-Schema-Wahl |
| **QK-10** `out/anki_export_log.json` als Persistenz-Pfad | ENT-NEU-Eintrag schreiben (oder Architekt-Alternative `usage_stats:` ziehen) |
| **QK-11** `agents/render/` als Modul-Standort | Architekt-Override formal annehmen oder begründet ablehnen |
| **QK-12** ARCHITECTURE.md §6.3 Threshold-Korrektur auf 30 | Doku-Korrektur in 05 oder als Schritt 0d in 026 |
| **QK-13** ENT-007 formale Pause | Status-Update in `doc/ENTSCHEIDUNGEN.md` |
| **QK-14** Test-Strategie als Pre-Implementierungs-Pflicht | `requirements.txt` ergänzen + Test-Ordner-Skelett im Backlog |
| ENT-NEU-C IPA-Schema-Erweiterung | Annehmen / verschieben (UX-Mockups in [02 §B2/B3](../02_ux.md) bleiben gültig auch ohne IPA) |
| C8 Sonnet vs. Haiku (R18) | Bestätigen: interner Lint-Pass ist nicht ENT-045-tangiert? |

---

## Schnittstelle QM↔PO — was ich für die Synthese beitrage

**Beobachtung 1:** Der Workshop hat **die richtigen Themen aufgemacht** — Frontmatter, Index, Lint, Render-Layer, Multi-Modal. Aber er hat **nicht alle Schulden produziert**, die er aufdeckt. Vier davon sind älter (R1 Branch-Bug, R14 Threshold-Doku, R15 index_updater-Phantom, R16 Header-Kommentar). PO-Synthese sollte das transparent benennen, sonst wirkt der Backlog wie pure Workshop-Last.

**Beobachtung 2:** Reihenfolge ist scharf, **aber Schritte 0/0b/0c vorzuziehen ist günstig**. Der `graph_writer`-Bug (R1) und das Test-Skelett (QK-14) verschlanken die Implementierungs-Session 026 erheblich, weil sie destructive-failure-modes preemptiv eindämmen. Drei ENT-NEUs in 05 sind 1–2 Stunden PO-Arbeit, kein Implementierungs-Aufwand.

**Beobachtung 3:** Test-Pattern-Etablierung (QK-14) ist die größte verdeckte Investition. Heute wirkt das wie "QM bittet um Pflicht-Gold-Plating", aber es schützt vor `anki_id`-Verlust (R2 → SRS-Verlust), Frontmatter-Korruption (C3 ohne Fixture), Privacy-Vertragsbruch (C6 ohne Mock-Test). Ohne Tests ist die MVP-2-Zweitwelle ein Schreib-und-Hoffe-Projekt.

**Beobachtung 4:** Sensitivity-Pfad für Bilder (R3/QK-9) ist das einzige echte Privacy-Risiko im Workshop. Architekt hat das als ENT-NÖTIG markiert; QM stuft auf P1, weil **kein anderer Vorschlag** den Privacy-Vertrag überhaupt berührt. Die ENT-Wahl in 05 ist binär: entweder "Default Quick-Save, opt-in Vision" (QM-Empfehlung) oder "Default Vision, opt-out via Hint" (Architekt-Erstvorschlag). Beide funktionieren, das erste ist konservativer.

**Mein Bias:** Ich bin QM, kein PO. Wenn meine Auflagen-Liste den MVP-2-Zweitwelle-Plan zeitlich sprengt — bitte explizit einzelne Auflagen verschieben (mit Begründung), nicht alle gleichzeitig durchwinken. Test-Skelett (QK-14) und `graph_writer`-Fix (R1) halte ich für nicht-verhandelbar; bei den anderen drei P1 (R2 Migration mit Auflagen, R3 Sensitivity-ENT) gibt es Wahlmöglichkeiten in der Schärfe.

---

## Übergabe-Status

- [x] [04_qm.md](../04_qm.md) geschrieben (Zusammenfassung + Teil A + Teil B + Teil C + Empfehlungen + Aktualisierungs-Vorschlag).
- [x] Sieben QK-Vorschläge formuliert (QK-8 bis QK-14).
- [x] Drei ENT-NEU-Vorschläge plus zwei ENT-Updates (ENT-007, ENT-027) für PO.
- [x] Vier P1-Befunde mit Mitigation und Test-Pflichten.
- [x] Bonus-Befund (R16, [graph_reader.py:3-4](../../agents/graph_reader.py#L3-L4) interne Doku-Inkonsistenz) eigenverantwortlich nachgereicht.
- [x] Vier Architekt-Inkonsistenz-Befunde verifiziert (R1, R14, R15) — R1 in Code direkt nachgelesen, R14/R15 verifiziert.
- [x] Meilenstein-Urteil als Header dieses Files.
- [x] Klare ENT-Bedarfs-Liste.
- [x] Querverweise an PO in [protokoll.md](../protokoll.md) eingetragen.
- [x] QM-Risiko-Snapshot in [protokoll.md](../protokoll.md) gefüllt.
- [x] Diese Handover-Datei bereit.
- [ ] Git-Commit (passiert nach Schreibe-Schluss von protokoll.md).

**Bereit für Phase 5.** PO-Session kann mit frischer Claude-Code-Session und [prompts/05_po_synthesis_prompt.md](../prompts/05_po_synthesis_prompt.md) starten.

---

## Anti-Erwartungen

- PO darf alle QK-Vorschläge übernehmen, abändern oder ablehnen — Begründung in `05_po_synthesis.md` reicht.
- PO darf P1-Befunde **nicht stillschweigend ignorieren**, aber als P2/P3 herabstufen mit expliziter Risiko-Abwägung.
- PO darf neue Anti-Decisions formulieren, die das QM nicht angesprochen hat.
- PO darf **die Reihenfolge brechen**, wenn er Abhängigkeiten explizit adressiert (z.B. C5a vor Render-Modul ist möglich, wenn man das Health-Tag-Ergebnis erstmal nur in `out/anki_export_log.json` schreibt und Anki-Tag-Vergabe verschiebt — würde QM nicht empfehlen, aber blockt nicht).
- PO darf Test-Skelett (QK-14) verschieben **nur** mit explizitem Risiko-Statement im 05_po_synthesis.md (und Akzeptanz, dass die destruktiven Schritte ohne Test-Backstop laufen).
