"""Ingest-Ledger — Verarbeitungs-Marker der Clippings-Ingestion (02 §B2).

Idempotenz-Definition (woertlich aus 02 §B2): Ein Clip gilt als verarbeitet
⇔ seine kanonische Quell-ID hat einen Eintrag im Ledger. Stufe 0 filtert
geledgerte IDs — zweiter Lauf = alles gefiltert, „nothing to do".
LLM-Output-Vergleich ist als Idempotenz-Kriterium unbrauchbar; der Marker
liegt deshalb auf der Input-Seite.

Format (versioniert, analog ``scripts/migrations/applied.json`` — Betriebs-
Zustand, verlustkritisch, klein; der Inventory-Plan dagegen ist Build-
Artefakt in ``out/`` — Brief-032 F2, nicht mischen)::

    {"<id>": {"status": "merged|skipped", "reason": "...",
              "topic_pages": ["tp_..."], "ts": "<iso>"}}

Initial-Schnitt (Brief 032, Liefer-Artefakt 1): das Ledger existiert ab S032
als leeres ``{}`` im Repo — explizit schlaegt implizit; Rekonstruktion und
Live-Lauf behandeln „fehlt" und „leer" identisch.

Selbstheilung (02 §B2): Geht das Ledger verloren, wird es aus dem Graphen
rekonstruiert — ``sources[].id`` aller TopicPages in ``wiki/topics/``
(Filesystem-Walk; der Graph ist die autoritative Quelle, das Ledger nur der
schnelle Index davor). ``skipped``-Eintraege sind nicht rekonstruierbar
(stehen in keiner Seite) — akzeptierter Preis.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents import frontmatter
from scripts.ingest import LEDGER_PATH


def load_ledger(path: Path = LEDGER_PATH) -> dict[str, dict[str, Any]]:
    """Ledger lesen; fehlendes File == leeres Ledger."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Ledger {path} ist kein JSON-Objekt")
    return data


def save_ledger(entries: dict[str, dict[str, Any]],
                path: Path = LEDGER_PATH) -> None:
    """Ledger deterministisch schreiben (sortierte Keys, LF)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(entries, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )


def make_skip_entry(reason: str, ts: str | None = None) -> dict[str, Any]:
    ts = ts or datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {"status": "skipped", "reason": reason, "topic_pages": [], "ts": ts}


def reconstruct_ledger(wiki_root: Path) -> dict[str, dict[str, Any]]:
    """Selbstheilung: Ledger aus ``wiki/topics/`` neu aufbauen.

    Walkt alle TopicPages, sammelt ``sources[].id`` ein. Wiki-Seiten sind
    KI-geschrieben und ENT-005-konform — hier ist ``agents.frontmatter``
    (voller Parse) der richtige Pfad, anders als bei Clipper-Rohdaten (F3).
    Heute ist ``wiki/topics/`` leer → leeres Ledger; die Mechanik wird per
    Fixture getestet (Brief 032 Schritt 3.2).
    """
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entries: dict[str, dict[str, Any]] = {}
    topics = wiki_root / "wiki" / "topics"
    if not topics.exists():
        return entries
    for md in sorted(topics.rglob("*.md")):
        try:
            fm, _body = frontmatter.read(md)
        except Exception:
            continue
        if fm.get("type") != "TopicPage":
            continue
        slug = md.stem
        for src in fm.get("sources") or []:
            sid = (src or {}).get("id") if isinstance(src, dict) else None
            if not sid:
                continue
            entry = entries.setdefault(sid, {
                "status": "merged",
                "reason": "rekonstruiert aus wiki/topics/ (Selbstheilung 02 §B2)",
                "topic_pages": [],
                "ts": ts,
            })
            if slug not in entry["topic_pages"]:
                entry["topic_pages"].append(slug)
    return entries
