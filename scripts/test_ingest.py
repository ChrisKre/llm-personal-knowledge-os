"""test_ingest.py — MVP-0 CLI test script for the ingest pipeline.

Usage:
    python scripts/test_ingest.py "Heute war ein schöner Tag. Madrugada ist ein schönes Wort."
    python scripts/test_ingest.py "..." --write        # actually writes files
    python scripts/test_ingest.py "..." --intent vocab  # force intent
    python scripts/test_ingest.py "..." --hint "vocab"  # pass user hint
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv()


def _detect_provider() -> str:
    """Returns 'claude', 'ollama', or 'none'."""
    import requests as _req
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key and not key.startswith("sk-ant-PLACEHOLDER"):
        return "claude"
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        _req.get(f"{ollama_host}/api/tags", timeout=3)
        return "ollama"
    except Exception:
        return "none"


def _print_section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print('─' * 60)


def _print_wiki_write(w: dict, idx: int) -> None:
    path = w.get("path", "?")
    op = w.get("operation", "?")
    content = w.get("content", "")
    # Extract type and first heading from content
    type_match = None
    heading = path.split("/")[-1]
    for line in content.splitlines():
        if line.startswith("type:"):
            type_match = line.split(":", 1)[1].strip()
        if line.startswith("# ") and not line.startswith("## "):
            heading = line[2:].strip()
            break
    print(f"  [{idx}] {op.upper():8} {path}")
    if type_match:
        print(f"       type: {type_match}  |  title: {heading}")
    # Show story_score if present
    for line in content.splitlines():
        if "story_score:" in line:
            print(f"       {line.strip()}")
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="MVP-0 ingest test — dry-run by default")
    parser.add_argument("text", help="Input text to ingest")
    parser.add_argument("--write", action="store_true", help="Actually write files (default: dry-run)")
    parser.add_argument("--hint", default="", help="User hint (e.g. 'vocab', 'story')")
    parser.add_argument("--intent", default="", help="Force classified intent (skips classify node)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Dump full state as JSON")
    args = parser.parse_args()

    provider = _detect_provider()
    if provider == "claude":
        print("  Provider: Claude API")
    elif provider == "ollama":
        model = os.environ.get("OLLAMA_MODEL", "llama3.2")
        print(f"  Provider: Ollama ({model}) — kein API-Key nötig")
    else:
        print("[WARN] Weder ANTHROPIC_API_KEY noch Ollama erreichbar.")
        print("       Zeige nur raw_event (kein Pipeline-Lauf möglich):\n")
        print(json.dumps({
            "content": args.text, "user_hint": args.hint,
            "source": "cli", "media_type": "text",
        }, ensure_ascii=False, indent=2))
        print("\nOptionen:\n  A) ollama pull llama3.2 && ollama serve\n  B) ANTHROPIC_API_KEY=... in .env setzen")
        return

    from main_workflow import WIKI_ROOT, SupervisorState, _load_graph_index, _load_user_profile, build_workflow
    from agents.graph_writer import execute_writes

    raw_event: dict = {
        "content": args.text,
        "user_hint": args.hint,
        "source": "cli",
        "media_type": "text",
    }

    _print_section("INPUT")
    print(f"  Text:  {args.text[:120]}")
    print(f"  Hint:  {args.hint or '(none)'}")
    print(f"  Mode:  {'WRITE' if args.write else 'DRY-RUN'}")

    if not args.write:
        # Monkey-patch execute_writes in both modules — main_workflow imports it by value
        import agents.graph_writer as _gw
        import main_workflow as _mw

        def _dry_execute(writes, wiki_root=None):
            print(f"\n  [DRY-RUN] execute_writes() würde {len(writes)} Datei(en) schreiben — übersprungen.")

        _gw.execute_writes = _dry_execute
        _mw.execute_writes = _dry_execute

    graph = build_workflow(WIKI_ROOT)

    initial_state = SupervisorState(
        raw_event=raw_event,
        user_profile=_load_user_profile(WIKI_ROOT),
        graph_index=_load_graph_index(WIKI_ROOT),
        classified_intent=args.intent,
        graph_context=[],
        assigned_agents=[],
        agent_outputs={},
        supervisor_verdict="",
        review_notes="",
        wiki_writes=[],
        telegram_messages=[],
    )

    print("\n  Pipeline läuft...")
    final_state = graph.invoke(initial_state)

    _print_section("ERGEBNIS")
    print(f"  Intent:           {final_state.get('classified_intent', '?')}")
    print(f"  Supervisor:       {final_state.get('supervisor_verdict', '?')}")
    review = final_state.get("review_notes", "")
    if review:
        print(f"  Review-Notizen:   {review[:200]}")

    wiki_writes = final_state.get("wiki_writes", [])
    _print_section(f"WIKI WRITES ({len(wiki_writes)})")
    if wiki_writes:
        for i, w in enumerate(wiki_writes, 1):
            _print_wiki_write(w, i)
    else:
        print("  (keine WikiWrite-Objekte)")

    tg = final_state.get("telegram_messages", [])
    if tg:
        _print_section(f"TELEGRAM MESSAGES ({len(tg)})")
        for msg in tg:
            print(f"  • {msg[:200]}")

    graph_ctx = final_state.get("graph_context", [])
    if graph_ctx:
        _print_section(f"GRAPH CONTEXT ({len(graph_ctx)} Seiten geladen)")
        for p in graph_ctx:
            title = getattr(p, "title", "?")
            summary = getattr(p, "summary", "")[:80]
            print(f"  • {title}: {summary}")

    if args.as_json:
        _print_section("FULL STATE (JSON)")
        # Serialize non-serializable objects
        def _default(obj):
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)
        print(json.dumps(final_state, default=_default, ensure_ascii=False, indent=2))

    if not args.write:
        print("\n  Tipp: Füge --write hinzu um Dateien tatsächlich zu schreiben.")


if __name__ == "__main__":
    main()
