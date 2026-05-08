# Workshop: Knowledge-Graph-Tiefencheck vor MVP-3
> Ausgerufen: 2026-05-08, durch Product Owner | Typ: **5-Phasen-Workshop, kein Implementierungs-Code** | Session-Bezug: S025

---

## Warum dieser Workshop

MVP-2 ist faktisch geschlossen — Anki-Export läuft, Voice-Capture läuft, Hint-Gate wirkt. Bevor MVP-3 anrollt, prüfen wir den Kern: den **LLM Knowledge Graph**. Ist er gut definiert? Gibt es genug Routinen, ihn sauber wachsen zu lassen? Sind Indexierung, Retrieval, Multi-Modal-Extraktion und die Symbiose mit dem Frontend ausreichend bedacht?

Der Workshop ist **kein Architekturschwenk**. Er ist Bestandsaufnahme + Standortbestimmung + priorisierter Backlog. Der bestehende Implementierungsplan bleibt der Default — der Workshop liefert **Ergänzungen**, keinen Reset.

## Leitfragen (vom PO gesetzt)

1. Ist der Knowledge Graph in seiner aktuellen Form (Markdown + Frontmatter + Wiki-Struktur) ausreichend für MVP-3 und darüber hinaus?
2. Welche Routinen brauchen wir für **Indexierung** und **Updates**?
3. Wie funktioniert **Retrieval** heute, was fehlt für Fakten-Vergleich/-Konsolidierung?
4. Wie nutzen wir die **Graph-Struktur** für unerwartete Verknüpfungen / Insight-Generierung?
5. Wie ist die **Schnittstelle Graph ↔ Frontend** (Telegram, Anki, künftige Renderer) — heute und im Soll?
6. Wie extrahieren wir Wissen aus **Multi-Modal-Quellen** (Foto, Video, Audio)? (ENT-024 Audio-Einschränkung beachten.)

## Teilnehmer & Reihenfolge

| # | Rolle | Aufgabe | liefert | übergibt an |
|---|---|---|---|---|
| 1 | AI-Research | Bestandsaufnahme + State-of-Art-Recherche (Web!) + Chancen | `01_ai_research.md` | UX |
| 2 | UX | Anki-HTML-Konzept + Schnittstelle Graph→Karte (+ Frontend-Symbiose) | `02_ux.md` | Architekt |
| 3 | Architekt | Machbarkeit, Vetos, Implementierungsskizze | `03_architect.md` | QM |
| 4 | QM | Risiken, P1/P2/P3, Testbarkeit, Kosten | `04_qm.md` | PO |
| 5 | PO | Synthese, Backlog, Anti-Decisions, ENT-Updates, S026-Brief | `05_po_synthesis.md`, `backlog.md` | (Ende) |

Architekt darf bereits in `01` und `02` Stellen markieren (per Edit) mit `(!)ARCH-VETO: [Grund](!)` oder `(!)ENT-NÖTIG: [Grund](!)` — bevor er sein eigenes File schreibt. Das macht Vetos früh sichtbar.

## Doku-Struktur

```
workshop/
├── README.md                  ← dies hier (Charta)
├── protokoll.md               ← Spine: Index-Tabelle, von jeder Rolle ergänzt
├── 01_ai_research.md          ← Rolle 1
├── 02_ux.md                   ← Rolle 2
├── 03_architect.md            ← Rolle 3
├── 04_qm.md                   ← Rolle 4
├── 05_po_synthesis.md         ← Rolle 5 (PO-Synthese)
├── backlog.md                 ← PO-Output: priorisierte Aufgaben
├── refs/
│   └── anki_html_examples/    ← vom PO bereitgestellte HTML-Anker-Beispiele
├── handovers/
│   ├── handover_01_research_to_ux.md
│   ├── handover_02_ux_to_architect.md
│   ├── handover_03_architect_to_qm.md
│   └── handover_04_qm_to_po.md
└── prompts/
    ├── 01_ai_research_prompt.md
    ├── 02_ux_prompt.md
    ├── 03_architect_prompt.md
    ├── 04_qm_prompt.md
    └── 05_po_synthesis_prompt.md
```

## Workshop-Regeln (nicht-verhandelbar)

- **Kein Code.** Keine Rolle schreibt produktiven Code in `agents/`, `bot.py`, `scripts/`, `wiki/`. Empfehlungen, Skizzen, HTML-Code in Workshop-Files — ja. Ausnahme: Architekt-Veto-Edits in `01`/`02` (sind Workshop-Files, kein Code).
- **Kein neuer ENT ohne PO-Synthese.** Rollen schlagen ENT-Bedarf vor (markiert als `[ENT-NEU?]`); der PO entscheidet final in `05`.
- **Karpathy-Prinzip bleibt.** Vorschläge die RAG/Vektor-Stores einführen brauchen explizite Begründung. PO-Synthese nimmt sie entweder mit ENT an oder verwirft sie mit Begründung.
- **WikiWrite-Vertrag bleibt.** Vorschläge die direktes Schreiben in `wiki/` einführen werden vom Architekt vetiert oder kommen als ENT in die PO-Synthese.
- **Budget-Realismus.** Jeder Vorschlag mit täglichen LLM-Calls braucht eine Kosten-Abschätzung in der jeweiligen Rolle-Sektion (~$5–10/Monat-Rahmen).
- **Sprache:** Deutsch (Projekt-Konvention).
- **Symbol-Konventionen:** wie in den jeweiligen `prompts_team/head_*.md` festgelegt — `(?)…(?)`, `(!)…(!)`, `[TODO]`, etc.

## Was der PO am Ende des Workshops liefert

- `05_po_synthesis.md` mit:
  - Synthese der 4 Rollen-Beiträge
  - **Anti-Decisions-Sektion**: was bewusst NICHT geändert wird (schützt MVP-3-Plan + Verträge)
  - Verdict pro Leitfrage (1–6 oben)
- `backlog.md` mit priorisierten Aufgaben (P1/P2/P3 + Aufwand-Schätzung + ENT-Bezug)
- Updates in `doc/ENTSCHEIDUNGEN.md` (nur entschiedene ENTs)
- Updates in `doc/CHANCEN.md` (Radar-Ideen)
- `sessions/025_2026-05-08.md` mit gefüllten Ergebnis-Notizen
- `sessions/026_DATUM.md` als Handover an die nächste Implementierungs-Session

## Voraussetzungen vor Workshop-Start
- [ ] PO committed Vorbereitung mit Message: `Workshop-Phase 0: Vorbereitung — Anker-Beispiele + S024 geschlossen`.

## Ablauf-Status

| Phase | Datum | Status |
|---|---|---|
| 0 — Workshop ausgerufen (PO) | 2026-05-08 | ✓ |
| 1 — AI-Research | TBD | offen |
| 2 — UX | TBD | offen |
| 3 — Architekt | TBD | offen |
| 4 — QM | TBD | offen |
| 5 — PO-Synthese | TBD | offen |

## Wie der Nutzer den Workshop fährt

Pro Phase: **eine frische Claude-Code-Session** starten und den jeweiligen Prompt aus `workshop/prompts/` als Eingabe geben. Die Rolle erledigt ihre Phase, committet (Commit-Message ist im jeweiligen Prompt vorgegeben), dann startet die nächste Phase. Zwischen Phasen kann der Nutzer/PO Befunde überfliegen — aber nicht nachjustieren, sonst zerfasert das Protokoll.
