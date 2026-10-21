"""Ingest ledger — processing markers for clippings ingestion (02 §B2).

Idempotency definition (verbatim from 02 §B2): a clip counts as processed
⇔ its canonical source ID has an entry in the ledger. Stage 0 filters out
ledgered IDs, so a second run filters everything: "nothing to do".
Comparing LLM output is useless as an idempotency criterion, which is why the
marker sits on the input side.

Format (like ``scripts/migrations/applied.json``: operational state, must not
be lost, small; the inventory plan, by contrast, is a build artifact in
``out/`` — brief 032 F2, do not mix them)::

    {"<id>": {"status": "merged|skipped", "reason": "...",
              "topic_pages": ["tp_..."], "ts": "<iso>"}}

Initial cut (brief 032, deliverable 1): the ledger starts out as an empty
``{}``; explicit beats implicit. Reconstruction and live runs treat "missing"
and "empty" the same way.

Self-healing (02 §B2): if the ledger is lost, it is rebuilt from the graph:
``sources[].id`` of all TopicPages in ``wiki/topics/`` (file system walk; the
graph is the authoritative source, the ledger only the fast index in front of
it). ``skipped`` entries cannot be reconstructed (they appear on no page),
which is an accepted cost.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents import frontmatter
from scripts.ingest import LEDGER_PATH


def load_ledger(path: Path = LEDGER_PATH) -> dict[str, dict[str, Any]]:
    """Read the ledger; a missing file == an empty ledger."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Ledger {path} is not a JSON object")
    return data


def save_ledger(entries: dict[str, dict[str, Any]],
                path: Path = LEDGER_PATH) -> None:
    """Write the ledger deterministically (sorted keys, LF)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(entries, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )


def make_skip_entry(reason: str, ts: str | None = None) -> dict[str, Any]:
    ts = ts or datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {"status": "skipped", "reason": reason, "topic_pages": [], "ts": ts}


def reconstruct_ledger(wiki_root: Path) -> dict[str, dict[str, Any]]:
    """Self-healing: rebuild the ledger from ``wiki/topics/``.

    Walks all TopicPages and collects ``sources[].id``. Wiki pages are written
    by the AI and conform to ENT-005, so ``agents.frontmatter`` (full parse) is
    the right path here, unlike for raw clipper data (F3). With an empty
    ``wiki/topics/`` the result is an empty ledger; the mechanism is tested
    with a fixture (brief 032 step 3.2).
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
                "reason": "reconstructed from wiki/topics/ (self-healing 02 §B2)",
                "topic_pages": [],
                "ts": ts,
            })
            if slug not in entry["topic_pages"]:
                entry["topic_pages"].append(slug)
    return entries
