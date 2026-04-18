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
