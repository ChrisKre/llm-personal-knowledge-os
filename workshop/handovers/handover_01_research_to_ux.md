# Handover: AI-Research → UX
> Erstellt: 2026-05-08 | von: AI-Research | an: UX | Workshop: [README](../README.md)

---

## Was du aus 01_ai_research.md zwingend lesen musst

- **[01_ai_research.md §A4 — Heutige Schwachstellen](../01_ai_research.md)** (Top 5, nach Schmerz priorisiert). Diese fünf definieren das Gelände, auf dem deine UX-Vorschläge landen.
- **[01_ai_research.md §A2 (e) Multi-Modal-Extraktion](../01_ai_research.md)** — fünf Extraktoren existieren, vier ungenutzt. Das ist Material für Render-Layer-Erweiterungen (siehe Aufträge unten).
- **[01_ai_research.md §C5 — Symbiose Graph↔Frontend](../01_ai_research.md)** — der UX-Anker für Phase 2 (zwei Sub-Pfade: C5a Health-Tag, C5b zweiter Backlink).
- **[01_ai_research.md §B3 — Multimodale Wissens-Extraktion](../01_ai_research.md)** — State-of-Art-Bezug für Caption-then-Index-Pattern; relevant, falls UX Bilder/Audio auf Karten vorschlägt.
- **[01_ai_research.md §Empfehlungen für UX-Phase](../01_ai_research.md)** — sechs Punkte, alle bindend.

---

## Konkrete Aufträge für UX

1. **Anki-Card-Layout-Konzept** (nach Workshop-Charta, Phase-2-Hauptauftrag):
   - Verdict zu **C5a** (Health-Tag `health::stale-mnemonic` bei Wiki-Update nach Anki-Export-Zeitstempel): sinnvoller Filter-Hebel oder Karten-Verschmutzung?
   - Verdict zu **C5b** (zweiter Backlink im Anki-Back zum aktuellen `index.md#section`-Anker): auf Mobile zumutbar oder zu viel?
   - Layout-Skizze (HTML-Snippets in `02_ux.md`) für Front und Back, mit explizitem Verdict zu den S024-UX-Fragen aus dem Anki-Live-Test (Genus-Präfix, Eselsbrücken-Länge, Tags-Filter, Beispielsatz-Niveau, Mobile-Backlink-Bruch).
2. **Multi-Modal-Karten-Format** (aus L13):
   - Soll der Anki-Back ein **Bild** tragen (Vision-Caption aus `raw/assets/`)? Wann ja, wann nein?
   - Soll der Anki-Back ein **Audio-Replay** tragen (Whisper-Source-File als Anki-`[sound:...]`-Tag)? Datei-Größen-Trade-off?
   - Format-Empfehlung pro VocabEntry-Typ (kontextabhängig: Vokabel mit kulturellem Hintergrund vs. neutrales Funktionswort).
3. **Render-Layer-Strategie für künftige Frontend-Konsumenten** (Discord/E-Mail, vorgemerkt in [ENT-049](../../doc/ENTSCHEIDUNGEN.md)):
   - UX-Empfehlung, **welche Frontmatter-Felder ein generischer Renderer mindestens braucht**, um aus einem VocabEntry eine "passable" Repräsentation zu bauen — egal ob Anki-Karte, Discord-Embed oder E-Mail-Wochen-Digest.
   - Diese Empfehlung ist Grundlage für eine künftige Render-Layer-Abstraktion, ohne sie heute zu bauen.
4. **Reihenfolge-Hinweis an Architekt im 02→03-Handover**:
   - Frontmatter-Schuld (siehe [01_ai_research.md §C4](../01_ai_research.md)) muss **vor** Lint-Auto-Fixes (C3) und vor Index-Renderer (C1) gefixt werden, sonst kaskadiert die Schuld in jedes neue Konsumenten-Tool. UX bitte als expliziten Reihenfolge-Hinweis ans Architekten-Handover anhängen.

---

## Chancen, die UX prüfen soll (aus Teil C)

- **C5 (Symbiose)** — UX-Hauptauftrag, siehe oben.
- **C6 (Multi-Modal-Backfill)** — UX-Aspekt: wie sähe ein Telegram-Flow für Bild-Drop aus, der Karpathy-konform mit "Quick-Save vs. Process-Now"-Hint funktioniert? ([KNOWLEDGE_GRAPH.md §0.2](../../doc/KNOWLEDGE_GRAPH.md))
- **C2 (SQLite-FTS5-Build)** — kein UX-Anteil, aber UX bitte signalisieren, wenn ein UX-Vorschlag (z.B. Card-Suche in Anki) implizit auf Phase-2-Retrieval angewiesen ist.
- **C8 (User-Profile Self-Refresh)** — UX-Aspekt: wäre ein Telegram-Briefing am Sonntag ("Diese Woche hast du …") ein sinnvoller Render-Layer-Konsument der `user_profile.md`?

---

## Schnittstelle Graph↔Frontend — was ich zur Render-Layer-Diskussion beitrage

**Beobachtung 1:** Heute existiert genau ein Render-Pfad (Anki-Export, [ENT-050](../../doc/ENTSCHEIDUNGEN.md) bis [ENT-052](../../doc/ENTSCHEIDUNGEN.md)). Telegram ist Input-Kanal, kein Render-Layer im engeren Sinn — die Telegram-Bestätigung "📚 Language: 3 Seiten erstellt" ([language_agent.write_entries:551-555](../../agents/language_agent.py#L551-L555)) ist Status-Echo, kein Wiki-Render.

**Beobachtung 2:** Der Anki-Render ist deterministisch (Markdown → Felder), aber **konsumiert kaputtes Frontmatter** ([sessions/023 §Befund](../../sessions/023_2026-05-07.md)). Das limitiert, wie viele Render-Layer wir parallel pflegen können — jeder neue Konsument vererbt den Workaround.

**Beobachtung 3:** Karpathy ([01_ai_research.md §B1](../01_ai_research.md)) trennt Wiki-State (kompiliert, persistiert) vom Render-Layer (transient, deterministisch). Das ist im Stack heute schwach modelliert: `language_agent.write_entries` baut Wiki-Content **und** Telegram-Render in derselben Methode. Eine UX-Empfehlung "wir wollen einen Render-Layer X" trifft heute auf eine Architektur, die Render und Compile vermischt.

**Empfehlung an UX:** Wenn Phase-2-Output eine Render-Layer-Skizze enthält, bitte sie als **eigene Komponente** denken (input: VocabEntry/PersonalFact-Frontmatter + Body; output: Format-spezifische Repräsentation), nicht als Erweiterung von `language_agent`. Das ist kein UX-Auftrag, aber ein Hinweis-Marker fürs Architekten-Handover.

---

## Was UX NICHT bearbeiten soll (Scope-Schutz)

- **Sync-Layer** (Anki ↔ Wiki Rückkanal — z.B. Anki-SRS-Status zurück in `usage_stats:` schreiben). Architektur-Sache, nicht UX.
- **Phase-2-SQLite-Indexer**. Backend-Implementierung, kein UX-Anteil.
- **Lint-Algorithmus-Detektoren**. Backend-Implementierung. UX darf höchstens **flaggen**, wenn ein UX-Vorschlag einen bestimmten Lint-Detektor voraussetzt.
- **Frontmatter-Schuld-Fix** (C4). Architekt-Auftrag — UX nimmt nur den Reihenfolge-Hinweis auf.
- **Karpathy-Prinzip-Diskussion** (kein RAG, kein Vektor-Store). Bleibt nicht-verhandelbar; UX-Vorschläge die das brechen müssen explizit als `[ENT-NEU?]` markiert werden.
- **Provider-Strategie** (Haiku/Sonnet/Ollama). UX-Vorschläge bitte ohne Modell-Zuweisung — die ist Architekten-Sache.

---

## Übergabe-Status

- [x] `01_ai_research.md` geschrieben (Teil A + B + C + Empfehlungen + Risiken + Quellen).
- [x] 14 externe Quellen zitiert (Soll ≥ 8).
- [x] Mindestens 3 `[MACHBAR]`-/`[MACHBAR-BEDINGT]`-Chancen (C1, C3, C4 als `[MACHBAR]`; C2, C5, C6, C8 als `[MACHBAR-BEDINGT]`).
- [x] Mindestens 1 Symbiose Graph↔Frontend-Chance (**C5**, der UX-Hauptanker).
- [x] Querverweise an UX in [protokoll.md](../protokoll.md) eingetragen.
- [x] Diese Handover-Datei bereit.
- [ ] Git-Commit (passiert nach Schreibe-Schluss von protokoll.md).

**Bereit für Phase 2.** UX-Session kann mit frischer Claude-Code-Session und [prompts/02_ux_prompt.md](../prompts/02_ux_prompt.md) starten.
