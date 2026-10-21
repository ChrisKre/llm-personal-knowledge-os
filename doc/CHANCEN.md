# CHANCEN.md — Innovations-Radar
> Erstellt: Session 010 (2026-04-19) | Autor: Product Owner
> Zweck: Sammlung von nicht-offensichtlichen Stärken, ungenutzen Potentialen und Features mit gutem Aufwand/Nutzen-Verhältnis. Keine Roadmap — ein Radar.

---

## 1. Nicht-offensichtliche Stärken des Systems

### 1.1 Offline-First durch Ollama (unerwarteter Privacy-Vorteil)
Die Zwei-Provider-Strategie (ENT-031) hat eine Nebenwirkung, die kein Designziel war: **`sensitivity:private`-Facts verlassen nie das Gerät.** Keine Cloud-Trace, kein Logging-Risiko, kein Terms-of-Service-Drift. Für sensible Lebensbereiche (Gesundheit, Beziehung, Finanzen) ist das ein belastbares Versprechen — und kostet nichts extra, weil es Abfallprodukt der Fallback-Architektur ist.

**Vermarktungswert:** Privacy-by-design ohne Privacy-Compromise-Pitch. "Deine intimsten Einträge fasst nur dein Laptop an" ist ein starkes Narrativ.

### 1.2 Selbstverstärkender Graph
Je mehr Facts, desto präziser die `graph_context`-Treffer (ENT-027), desto besser kalibriert die `story_score`, desto gezielter die Elaboration und Impuls-Generierung. Der **erste Monat ist der schwächste** — danach steigt Qualität automatisch. Das ist ein guter Product-Lock-in: der Wert des Systems wächst mit dem Nutzer mit.

### 1.3 Obsidian-Interop ab Tag 1
Keine separate UI nötig. Der Nutzer kann ab der ersten WikiWrite-Datei seinen Graphen in Obsidian lesen, taggen, manuell verlinken. Das reduziert den **Vertrauens-Kaltstart** — der Nutzer sieht den Graphen, bevor er dem System blind vertraut.

### 1.4 Sessions-als-Gedächtnis ist selbst ein Produkt-Feature
Das `sessions/NNN.md`-Muster, das wir für Engineering verwenden, ist konzeptuell identisch mit dem, was der Nutzer mit seinem Leben tut. Das System **lebt, was es tut** — das ist konsistent und dokumentiert eine klare Ideologie.

### 1.5 Karpathy-Wiki-Prinzip ist defensiv gegen LLM-Wandel
Wenn sich LLMs, Provider oder APIs ändern, liegt das gesamte Wissen trotzdem als **menschen-lesbares Markdown** vor. Kein Vector-Lock-in, keine Migration-Nightmare. Das ist langfristige Portabilität, die Vector-Stores nicht bieten.

---

## 2. Ungenutztes Potential (im aktuellen Scope)

### 2.1 `practice_log` als Trainingsdaten-Quelle (GE-002 Kandidat)
Jeder Story-Lab-Durchlauf erzeugt einen `practice_log`-Eintrag mit Transkript + Selbstbewertung + System-Feedback. Das ist **annotierter Personal-Content** — die teuerste Zutat für Finetuning. Nach 100+ Einträgen: genug für ein experimentelles LoRA-Finetune eines kleinen Modells.

Das offene Gedankenexperiment "Graph als LLM-Trainingsdaten" (aus Session 010) sollte genau hier ansetzen — siehe `sessions_gedankenexperiment/ge_002_graph-als-trainingsdaten.md` (vorgeschlagen).

### 2.2 StyleProfile als Persönlichkeits-Signatur
Die kontext-abhängigen `context_profiles` (ENT-020) sind konzeptuell eine **empirische Persönlichkeits-Signatur** über Zeit. Nach 6 Monaten Daten: messbare Drift, Wachstum, Entwicklung. Das ist ein Feature, das Coaching-Apps normalerweise nur simulieren.

**Idee:** "StyleProfile-Diff über Zeit" als Jahresrückblick-Generator.

### 2.3 Bidirektionaler Telegram-Bot statt nur Ingest
Der Bot ist derzeit Input-first. Aber der gleiche Kanal kann **proaktiv Impulse senden** (ENT-019 baut darauf), Lernfragen stellen, Bootstrap-Erweiterungen vorschlagen. Jeder `practice_log`-Eintrag ist in Wahrheit eine **zweiseitige Konversation** — die schon modelliert ist.

### 2.4 Spanisch-Lernen als Trojan Horse für Journaling
Der Nutzer öffnet den Bot für Vokabeln — und rutscht über `LanguageBridge`-Entitäten in Personal-Facts ("Was habe ich gestern erlebt, was ich auf Spanisch erzählen könnte?"). Das ist **Gewohnheit-Stapeln** par excellence: Das stärkere Bedürfnis (Sprache lernen) trägt das schwächere (Selbstreflexion).

### 2.5 `Concept`-Seiten als emergente Themen-Landkarte
Die Korrelations-Engine (ENT-010) erzeugt Concept-Seiten bei ≥3 verwandten Facts. Das heißt: **Das System baut ohne Nutzer-Zutun eine semantische Selbstkarte**. In Obsidian als Graph-View visualisiert ist das ein "Was beschäftigt mich eigentlich wirklich?"-Spiegel — das ist das, was viele Journaling-Tools versprechen, aber nie bottom-up liefern.

---

## 3. Niedrig-hängende Früchte (hoher Value / niedriger Aufwand)

| Feature | Value | Aufwand | Begründung |
|---|---|---|---|
| **Wochen-Zusammenfassung als Telegram-Broadcast** | hoch | gering | `log.md` + Sonnet-Prompt → wöchentlicher Digest. Pure Promoting-Logik. |
| **Fact-Birthday (auf-den-Tag-genau-vor-X-Jahren)** | hoch | gering | Simpler Frontmatter-Query; trifft emotional stark. |
| **Vokabel-des-Tages aus `LanguageBridge`** | mittel | gering | Random-Pick + Telegram-Push. |
| **"Was war 2025-12-24?"-Query** | mittel | gering | Graph-Datumsquery; gute Obsidian-Ergänzung. |
| **Einfacher Export (Jahres-Journal als PDF)** | hoch | mittel | Pandoc + Template. Anfassbares Artefakt = starker Retention-Boost. |
| **Semantischer Random-Walk** | hoch | mittel | "Zeig mir 3 zufällige verbundene Facts aus meiner Vergangenheit" — inspiration-as-a-service. |
| **Story-Lab "Vergleich über Zeit"** | hoch | mittel | Gleicher Fact, unterschiedlich erzählt nach 3 Monaten. Zeigt Wachstum sichtbar. |

---

## 4. Strategische Chancen (höheres Risiko, höheres Potential)

### 4.1 Finetuning auf persönlichen Daten (GE-002)
Wenn sich genug annotierte Erzählungen angesammelt haben: **LoRA-Finetune eines Open-Source-Modells** auf dem eigenen Stil. Das Modell würde dann nicht mehr generisches Feedback geben, sondern "in deiner Stimme". Offene Fragen: Datenmenge? Overfitting? Synthetische Daten aus dem Graphen generierbar?

Das Gedankenexperiment ist in sessions/010 als Aufgabe markiert — siehe Nachtrag dort.

### 4.2 Multi-User-Variante (Familien-Graph)
Der Graph ist technisch trivial duplizierbar, aber das Konzept skaliert sozial: **gemeinsamer Familien-Graph mit persönlichen Sub-Graphen**. Geteilte Events, aber private Interpretationen. Erfordert Zugriffsschicht — großer Umbau, aber nicht unmöglich.

### 4.3 Audio-Feature, sobald API es ermöglicht
ENT-024 hat Audio aus V1 gestrichen. Sobald Claude (oder OpenAI/Gemini) nativen Audio-Input bietet: **Ton-Coaching reaktivieren** als MVP-3-Feature. Die Infrastruktur (Whisper-Pipeline, Story-Lab-Flow) liegt bereit.

### 4.4 Karpathy-Wiki-Community
Das Konzept ist open-source-freundlich. Andere Nutzer könnten eigene Graphen bauen; gemeinsam könnten **öffentliche Concept-Seiten geteilt** werden (z.B. "Spanische Flamenco-Kultur"). Netzwerkeffekt ohne Social-Graph.

---

## 5. Potentielle Engpässe / Warnungen

- **Ollama-Qualitätsgrenze:** llama3.2 liefert fehlerhafte YAML/JSON-Outputs (technischer_hinweis.md §2). Für `private`-Facts ist das akzeptabel, aber User-Erwartungen müssen kalibriert bleiben.
- **Obsidian-Dependency:** Wenn Obsidian Preis- oder Sync-Modell ändert, braucht es Plan B (z.B. Logseq, Foam).
- **Kostenwachstum bei Sonnet-Usage:** Bei stark Story-Lab-lastiger Nutzung könnten Kosten über $1/Monat steigen. Monitoring einbauen.
- **Single-Provider-Risiko:** Aktuell starke Abhängigkeit von Anthropic. Die Fallback-Ollama-Schiene mildert das, aber echter Multi-Provider-Support (OpenAI, Google) wäre resilienter.

---

## 6. Offene strategische Fragen

1. **Monetarisierung?** Ist das ein persönliches Werkzeug oder langfristig Produkt? Die Architektur stützt beides.
2. **Open Source oder proprietär?** Der Karpathy-Ansatz lebt vom Dateisystem — Code-Sharing ohne Daten-Sharing ist trivial.
3. **iOS/Android-Native-App statt Telegram?** Telegram ist pragmatisch, aber nicht marken-eigenständig. Zu früh für die Frage, aber wert im Radar zu halten.
4. **Wie groß darf der Graph werden, bevor die Markdown-Navigation bricht?** SQLite ab 30 Seiten (ENT-027) ist Phase 1; ab 1000+? 10.000+? Noch nicht getestet.

---

## 7. Workshop-Radar-Ideen (Session 025, 2026-05-08)

> Drei Ideen aus dem Knowledge-Graph-Tiefencheck-Workshop, die bewusst **nicht** in die MVP-2-Zweitwelle gezogen wurden. Detail-Begründung in [workshop/05_po_synthesis.md §3 Anti-Decisions](../workshop/05_po_synthesis.md). Klassifikation als Radar (kein Backlog-Item) heißt: relevant, nicht jetzt.

### 7.1 LazyGraphRAG-Concept-Cluster (vom Workshop als C7 erfasst)
- **Was:** Wenn der Korpus auf ≥50 PersonalFacts wächst (heute: 10), NLP-basierter Co-Occurrence-Graph (Tag-/Slug-Token-Pairs) + Community-Detection (z.B. Louvain) erzeugt Concept-Seiten ([ENT-010](ENTSCHEIDUNGEN.md#ent-010-korrelations-engine)) bottom-up. Pro Community-Erkennung **einmalig** Sonnet-Synthese (~$0,02/Concept × geschätzt 5/Quartal = ~$0,10/Quartal). **Karpathy-konform** weil NLP-statisch — kein Vektor-Store, keine Embeddings.
- **State-of-Art-Bezug:** Microsoft LazyGraphRAG (Microsoft Research Blog 2024-11), 0,1 % der Indexierungs-Kosten von Vollversion-GraphRAG, NLP-statische Indexierung. Detail in [workshop/01_ai_research.md §B1](../workshop/01_ai_research.md).
- **Aufwand:** ~1–2 Tage (NLP-Library-Integration, Cluster-Detektion, Concept-Synthese-Prompt).
- **Trigger:** **Korpus-Wachstum auf ≥50 PersonalFacts.** Heute 10. Bei aktueller Aktivität (~3–5 PFs/Woche) erreicht Mitte–Ende 2026.
- **Risiko/Trade-off:** Cluster mit zu wenig Inhalt erzeugen leere Concepts. Mitigation: Min-Cluster-Größe 3.
- **Querverweise:** [Workshop §C7](../workshop/01_ai_research.md), [Workshop §B7 Architekt](../workshop/03_architect.md), [Workshop §B4 OK-Backlog QM](../workshop/04_qm.md).

### 7.2 Discord-Outbound für Wochen-Replay (vom Workshop als UX-C2 erfasst)
- **Was:** Sonntag 20:00 — Cron-getriggerter Job rendert Discord-Embed mit Wochen-Bilanz pro Lern-Domain (Spanisch, PersonalFacts, Style). Reicheres Render-Format als Telegram-Inline (mehrere Felder, Farb-Akzent, Markdown-Subset). Mockup in [workshop/02_ux.md §C2](../workshop/02_ux.md).
- **State-of-Art-Bezug:** [ENT-045](ENTSCHEIDUNGEN.md#ent-045-proaktiver-kanal-grundsätzlich-freigegeben-opt-in) erlaubt Proaktivität opt-in mit 24h-TTL und Pausier-Kommando. [ENT-049](ENTSCHEIDUNGEN.md#ent-049-zweit-oberflächen-strategie-telegram-bleibt-primär-cli-discord-e-mail-vorgemerkt-für-mvp-3) markiert Discord als Outbound-Kandidat für MVP-3.
- **Aufwand:** Discord-Bot-Setup ~1 Tag, Render-Layer für Embed ~2 Tage (`agents/render/discord.py` analog zu `agents/render/card.py`), Cron-Trigger + ENT-045-Policy-Implementierung ~1 Tag = **~4 Tage** Architekt-Aufwand.
- **Trigger:** **ENT-045-Aktivierung** (proaktiver Kanal opt-in). MVP-3-Scope. Pre-Req: BL-04 (Index repariert), BL-05 (`RenderDict`-Vertrag etabliert).
- **Risiko/Trade-off:** Doppel-Outbound-Telemetrie (Telegram-Echo + Discord) muss konsistent sein. ENT-045-Policy-Implementierung (24h-TTL, Pausier-Kommando) ist neue Infra.
- **Querverweise:** [Workshop §C2 UX](../workshop/02_ux.md), [Workshop §B12 Architekt](../workshop/03_architect.md), [Workshop §B4 NICHT-MVP-2 QM](../workshop/04_qm.md).

### 7.3 E2E-Pipeline-Tests für Bot-Handler (Workshop-Befund §D4 Architekt)
- **Was:** End-to-End-Tests für die Bot-Pipeline (Voice + Text + künftig Bild/PDF). Heute kein E2E-Test-Pattern; Test-Skelett (BL-02 in Workshop-Backlog) liefert nur Unit-Test-Skelett. E2E würde Bot-Handler-Mock + Whisper-Mock + LLM-Mock + Wiki-Diff-Assertion kombinieren.
- **State-of-Art-Bezug:** Standard-Pattern in agentischen Pipelines (LangChain/LangGraph-E2E-Test-Frameworks). Architekt-Befund [Workshop §D4](../workshop/03_architect.md): bei Multi-Modal (BL-08) kritisch.
- **Aufwand:** ~1 Tag Pattern-Etablierung + pro neuem Pfad ~2–4h.
- **Trigger:** **BL-08 (C6 Multi-Modal-Backfill) Live-Schaltung.** Davor sind Unit-Tests + Hint-Gate-Tests ausreichend. Sobald Bilder/PDFs durch die Pipeline fließen, ist E2E-Test der einzige Schutz vor stillen Regressions in der Bot-Handler-Verkettung.
- **Risiko/Trade-off:** Mock-Aufwand kann groß werden. Mitigation: Fokus auf Smoke-E2E (kommt eine Wiki-Datei raus?) statt detaillierte Inhalts-Assertion.
- **Querverweise:** [Workshop §D4 Architekt](../workshop/03_architect.md), [Workshop §B1 R4 QM](../workshop/04_qm.md).

---

## 8. Workshop-02-Radar-Ideen (Session 030, 2026-07-04)

> Drei Ideen aus dem Fremdwissen-Ingestion-Workshop, die bewusst **nicht** ins Workshop-02-Backlog gezogen wurden. Detail-Begründung in workshop_02/04_po_synthesis.md §2 (Leitfrage 6) + §Anti-Decisions. Radar heißt: relevant, nicht jetzt.

### 8.1 Themen-Digest für TopicPages (Telegram/Discord) — Phase-2b-Rückholung
- **Was:** Kompakte, scannbare Darstellung der Konsens/Dissens-Lage pro Themen-Seite als Digest-Nachricht (Consensus-Meter-artig, mit den in workshop_02/01_ai_research.md §B2 dokumentierten Schwächen als Warnliste: keine Gleichgewichtung, Tier + Recency sichtbar). Erst dann braucht es einen eigenen `topic_page_to_render_dict`-Adapter — **keine** Generalisierung des Vocab-`RenderDict` (Anti-Decision 8, 02 §A5).
- **Trigger:** PO nimmt einen Digest-Kanal in den Scope (frühestens MVP-3, gekoppelt an ENT-045/ENT-049) **oder** der Nutzer meldet nach dem Batch das Obsidian-Format als unscannbar. Dann wird Phase 2b (klein, mit echtem Material) nachgeholt — Rückhole-Bedingung aus 02 §D3.
- **Aufwand:** ~1 Tag UX-Konzept + ~2 Tage Render-Adapter.
- **Risiko/Trade-off:** Digest ohne Nutzungs-Erfahrung wäre Spekulations-Design — genau deshalb Radar statt Backlog.

### 8.2 Seiten-Größen-Schwelle / Themen-Split-Vorschlag (Re-Merge-Drift)
- **Was:** Claims werden nie gelöscht → TopicPages wachsen monoton; Re-Merge-Input-Tokens steigen über Monate, Lesbarkeit kippt bei >~30 Claims. Lint-Detektor: Seite >25 Claims → Telegram-Vorschlag „Themen-Split" (Nutzer entscheidet). Architekt-Risiko 3 in 02 §Risiken, QM-Frage F2.
- **Trigger:** erste TopicPage überschreitet ~25 Claims (Beobachtung via Kosten-Telemetrie aus BL-19; heute hat die größte Pilot-Seite ~15).
- **Aufwand:** ~2–3h (deterministischer Zähl-Detektor + Telegram-Frage, BL-07-Muster).
- **Risiko/Trade-off:** Zu früher Split fragmentiert Themen — deshalb Vorschlag mit Nutzer-Entscheid, kein Auto-Split.

### 8.3 Statische Debunk-/Referenz-Liste für Health-Glaubwürdigkeit
- **Was:** Gepflegte statische Liste vertrauenswürdiger/diskreditierter Autoren und Domains als Zusatz-Signal neben `source_tier` (ENT-060). Die Fehlinformations-Forschung (01 §B3, Q6/Q9) belegt: externe Debunk-Listen heben die LLM-Erkennungsrate deutlich. Karpathy-konform (statische Markdown-/YAML-Liste, kein Vektor-Store, kein Live-Fact-Checking — letzteres bleibt Anti-Decision 9).
- **Trigger:** erster belegter Falsch-Claim, der den Health-Verifikations-Pass (QK-15) passiert hat — dann ist ein zweites Signal gerechtfertigt.
- **Aufwand:** ~2h (Liste + Prompt-Einbindung in Stufe 1/Klassifikation).
- **Risiko/Trade-off:** Listen-Pflege ist manuelle Arbeit; veraltete Einträge erzeugen falsche Sicherheit. Klein anfangen (nur Korpus-Autoren).
