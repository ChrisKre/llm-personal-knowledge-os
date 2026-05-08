# Workshop-Prompt 01: AI-Research
> Phase 1 von 5 | Adressat: **AI-Experte Research** | Modus: **Implementierungs-Research mit GE-Anteilen**
> Diese Datei wird in eine **frische Claude-Code-Session** als Eingabe gegeben.

---

## Pflichtlektüre (in dieser Reihenfolge, vollständig)

1. `prompts_team/head_ai_research.md` — Rollen-Kopf (vollständig befolgen)
2. `workshop/README.md` — Workshop-Charta
3. `workshop/protokoll.md` — leer, du bist die erste Rolle die ergänzt
4. `sessions/024_2026-05-07.md` — letzter Stand vor Workshop (inkl. Ergebnis-Notizen, falls schon gefüllt)
5. `doc/ARCHITECTURE.md` — vollständig, insbesondere §3 Agenten, §4 LangGraph
6. `doc/SCHEMA.md` — Entitäts-Ontologie, Frontmatter-Spezifikationen
7. `doc/ENTSCHEIDUNGEN.md` — alle ENTs querlesen; relevante Kern-ENTs für Graph: ENT-006 (Sensitivity), ENT-024 (Audio), ENT-028 (Routing), ENT-031, ENT-036
8. `hinweise/technischer_hinweis.md` — bekannte Schulden
9. `agents/supervisor.py`, `agents/language_agent.py`, `agents/graph_writer.py` — querlesen, Architektur verstehen
10. `wiki/` — Struktur überfliegen, eine Vocab-Datei vollständig lesen (z.B. `wiki/language/vocab/v_es_madrugada.md`)
11. Falls existiert: `sessions_gedankenexperiment/ge_001_services-meta-routine.md` und `doc/COMP_SERVICES.md`

## Auftrag

Du machst eine **drei-teilige Analyse** des Knowledge Graphs.

### Teil A — Bestandsaufnahme (60 % der Zeit)

Beantworte präzise, mit Zeilen-Verweisen ins Repo:

1. **Was ist der Knowledge Graph in diesem Projekt?** Konkret: welche Entitäten, welche Relationen, wo gespeichert, wie gewachsen.
2. **Welche Routinen existieren heute** für (a) Indexierung, (b) Updates, (c) Retrieval, (d) Konsolidierung/Deduplizierung, (e) Multi-Modal-Extraktion?
3. **Was ist offensichtlich nicht-existent** in diesen fünf Bereichen? Sehr kritisch sein. Auch wenn etwas nur als `[STUB]` markiert ist — flagge es.
4. **Wo sind die heutigen Schwachstellen sichtbar?** Z.B. Frontmatter-Schuld (S023 §Befund), fehlende Retrieval-Schicht, fehlende Graph-Wachstums-Routinen, fehlende Konsolidierungs-Logik.

### Teil B — State-of-Art-Recherche (30 % der Zeit) — **PFLICHT-WEB-SUCHE**

**Du MUSST `WebSearch` und `WebFetch` aktiv einsetzen.** Quellen aus diesem Repo zählen NICHT.

**Mindest-Anforderung: 8 hochwertige externe Quellen** mit URL, Titel, Datum (≥ 2024 bevorzugt) und 1–2-Satz-Zusammenfassung. Anhängen am Ende von `01_ai_research.md` als Sektion `## Quellen`.

**Pflicht-Suchbegriffe (mindestens diese, mehr ist gut):**

- `LLM knowledge graph 2025 architecture`
- `GraphRAG Microsoft research paper`
- `Obsidian LLM second brain agentic`
- `agentic memory architecture 2026`
- `personal knowledge graph LLM retrieval`
- `markdown knowledge base LLM auto-update`
- `multimodal knowledge extraction LLM 2025`
- `knowledge graph indexing without vector store`

**Validierungs-Regel:** Bevor du dein File abschließt, **zähle die externen Quellen** in der Quellen-Sektion. Sind es < 8 → recherchiere weiter. Bei < 8 in der finalen Lieferung gilt sie als unvollständig — der PO wird dich zurückschicken.

Das Karpathy-Prinzip dieses Projekts bleibt nicht-verhandelbar (kein RAG, kein Vektor-Store) — aber finde heraus, **was außerhalb dieses Prinzips passiert** und was davon **innerhalb** des Prinzips übernehmbar wäre.

### Teil C — Chancen + kritischer Lücken-Bericht (10 % der Zeit)

Pro Lücke aus Teil A:

- Was wäre die kleinste sinnvolle Verbesserung? Klassifizierung: `[MACHBAR]` / `[MACHBAR-BEDINGT: …]` / `[NICHT-HEUTE: …]`
- Welcher State-of-Art-Befund aus Teil B passt hier? (Querverweis)
- Geschätzter Aufwand (Stunden, sehr grob)
- Geschätzte Kosten (LLM-Budget-Impact, falls täglich oder häufig)
- Risiko / Trade-off

**Mindestens 3 Chancen** mit `[MACHBAR]` oder `[MACHBAR-BEDINGT]`. **Mindestens 1 Chance** zur Symbiose Graph↔Frontend (Leitfrage 5 der Charta) — das ist der Anker für UX in Phase 2.

## Liefer-Files

### `workshop/01_ai_research.md`

```
# 01 — AI-Research: Knowledge-Graph-Bestandsaufnahme + State-of-Art

## Zusammenfassung (max 5 Bullets)

## Teil A — Bestandsaufnahme
### A1: Was ist der Knowledge Graph?
### A2: Existierende Routinen (Indexierung / Updates / Retrieval / Konsolidierung / Multi-Modal)
### A3: Lücken
### A4: Heutige Schwachstellen

## Teil B — State-of-Art
### B1: GraphRAG / verwandte Architekturen
### B2: Indexierung ohne Vektor-Store
### B3: Multimodale Wissens-Extraktion
### B4: Agentic Memory 2025/2026

## Teil C — Chancen
### C1, C2, C3, … (eine pro Chance, Format wie oben spezifiziert)

## Empfehlungen für UX-Phase
> Was die UX-Rolle aus diesem File zwingend mitnehmen soll. Konkret, mit Zeilen-Verweisen.

## Risiken (Top 3)

## Quellen
> Mindestens 8, mit URL/Titel/Datum/Kurz-Summary. Auto-Validierung: zähle die Einträge bevor du committest.
```

### `workshop/handovers/handover_01_research_to_ux.md`

```
# Handover: AI-Research → UX
> Erstellt: [Datum] | von: AI-Research | an: UX

## Was du aus 01_ai_research.md zwingend lesen musst
- [Sektions-Verweise]

## Konkrete Aufträge für UX
1. ...
2. ...

## Chancen, die UX prüfen soll (aus Teil C)
- [Verweise]

## Schnittstelle Graph↔Frontend — was ich zur Render-Layer-Diskussion beitrage
[Konkret und kurz]

## Was UX NICHT bearbeiten soll (Scope-Schutz)
- Sync-Layer ist Architektur-Sache, nicht UX
- [Weitere falls relevant]
```

### `workshop/protokoll.md` ergänzen

Trag die Zeile für AI-Research in die Beitrags-Tabelle ein. Datum: heute. Kern-Befunde: max 3, sehr kurz. Querverweise an UX in der Querverweis-Sektion eintragen, wenn relevant.

## Was du NICHT machst

- Kein Code schreiben (kein Edit in `agents/`, `bot.py`, `scripts/`, `wiki/`).
- Kein direktes Schreiben in `doc/` (kein neuer ENT-Eintrag — wenn nötig: `[ENT-NEU?]` markieren).
- Kein Übersteuern des Karpathy-Prinzips ohne explizite Begründung.
- Keine Empfehlung mit Budget-Verdopplung ohne Kosten-Abschätzung.

## Stop-Kriterien

- Wenn die Pflichtlektüre fundamental widersprüchlich ist → kurz im File markieren `(!)BLOCKIERT(!)` und beim PO melden.
- Wenn `WebSearch`/`WebFetch` nicht verfügbar sind → markieren und beim PO melden, **nicht** ohne Quellen weitermachen.

## Liefer-Stop

Wenn alle drei Files (`01_ai_research.md`, `handovers/handover_01_research_to_ux.md`, `protokoll.md`-Update) committet sind: Workshop-Phase 1 abgeschlossen. PO startet Phase 2.

**Git-Commit:** `Workshop-Phase 1: AI-Research — Knowledge-Graph-Bestandsaufnahme + State-of-Art`
