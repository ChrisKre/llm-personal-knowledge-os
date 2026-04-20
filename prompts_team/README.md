# prompts_team/ — Rollen-Templates

Dieses Verzeichnis enthält die unveränderlichen **Rollen-Köpfe** für jede Team-Rolle.
Jedes `head_*.md` definiert Identität, Autorität, Prinzipien und Interaktions-Symbole einer Rolle — einmal, stabil, wiederverwendbar.

---

## Dateien

| Datei | Rolle | Kurzbeschreibung |
|---|---|---|
| [head_architect.md](head_architect.md) | Senior System Architect | Implementierung, technische Richtung, WikiWrite-Vertrag |
| [head_product_owner.md](head_product_owner.md) | Product Owner | Scope, ENT-* Entscheidungen, MVP-Plan |
| [head_quality_manager.md](head_quality_manager.md) | Quality Manager | Abnahme, QK-Entscheidungen, Bugs priorisieren |
| [head_ai_research.md](head_ai_research.md) | AI-Experte Research | Modell-Qualität, Agenten-Autonomie, Gedankenexperimente |
| [head_ux.md](head_ux.md) | UI/UX Spezialist | Telegram-UX, Radar-Ideen, Interaction Design |

---

## Wie man die Templates benutzt

### Prinzip: Kopf + Session-Brief = vollständiger Prompt

Jede Session-Datei (`sessions/NNN_DATUM.md`) hat oben eine **Merge-Zeile**:

```markdown
> Rolle: [Senior System Architect](../prompts_team/head_architect.md) — lies diesen Kopf zuerst, dann diese Session.
```

Das LLM liest zuerst das Template, dann den Session-Brief. Die Rolle ist damit immer vollständig definiert — ohne Kopieren, ohne Duplizieren.

### Schritt für Schritt

**1. Rolle des Adressaten bestimmen.**
Wer soll diese Session ausführen? Architect, PO, QM, AI-Research oder UX?

**2. Merge-Zeile in den Session-Brief einfügen** (zweite Zeile, direkt nach dem Titel):
```markdown
# Session 017 — MVP-1 Telegram Integration
> Rolle: [Senior System Architect](../prompts_team/head_architect.md) — lies diesen Kopf zuerst, dann diese Session.
> Datum: 2026-04-21 | Typ: IMPLEMENTIERUNG | Vorgänger: Session 016
```

**3. Session-Brief aus Perspektive des Adressaten formulieren.**
Nicht: "Ich als PO möchte dass du..." — sondern: "Deine Aufgabe in dieser Session ist..."
Die Motivation bleibt im Brief, aber das Framing gehört der Rolle.

---

## Warum dieser Ansatz

**Problem vorher:** Nach einer PO-Session war der Ton und das Framing der nächsten Session noch PO-geprägt — auch wenn die nächste Rolle der Architect war. Jede Rolle dachte durch die Brille der vorherigen.

**Lösung:** Der Rollen-Kopf setzt Mindset, Autorität und Scope-Grenzen **bevor** der Session-Brief gelesen wird. Die Rolle denkt in ihrer eigenen Logik — nicht in der des Absenders.

---

## Interaktions-Symbole (rollenübergreifend)

Diese Symbole gelten in allen Sessions und allen Templates:

| Symbol | Bedeutung |
|---|---|
| `(?)text(?)` | Frage / Best-Practice gesucht — nicht übergehen |
| `(!)text(!)` | Kritische Anforderung oder Blocker |
| `[TODO]` | Technische oder inhaltliche Lücke |
| `[ENT-NNN]` | Verweis auf bestehende Entscheidung in `doc/ENTSCHEIDUNGEN.md` |

Zusätzliche rollenspezifische Symbole stehen im jeweiligen Template.

---

## Templates aktuell halten

Templates ändern sich selten — nur wenn sich die Rolle strukturell ändert (z.B. neue nicht-verhandelbare Prinzipien, neue Signatur-Artefakte). Kleinere Anpassungen an einzelnen Sessions gehören **nicht** ins Template.

Wenn du eine Änderung am Template vornimmst: kurz im Git-Commit begründen warum.

---

## Neue Rolle hinzufügen

1. `head_<rollenname>.md` anlegen — Struktur von einem bestehenden Template übernehmen.
2. Diese README-Tabelle ergänzen.
3. Git-Commit: `prompts_team: <Rollenname> Template hinzugefügt`
