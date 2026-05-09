"""graph_reader.py — Index abstraction layer for the Knowledge Graph.

Phase 1 (< 30 wiki pages): keyword search over index.md
Phase 2 (>= 30 wiki pages): SQLite FTS5 full-text search

The switch is automatic via _wiki_size(). Nothing outside this module needs to know
which phase is active.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic

WIKI_PAGE_THRESHOLD = 30
WIKI_ROOT = Path(__file__).parent.parent  # repo root
INDEX_PATH = WIKI_ROOT / "index.md"
SQLITE_PATH = WIKI_ROOT / "wiki_index.db"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class WikiPage:
    path: str           # relative path from repo root, e.g. "wiki/personal/facts/pf_..."
    title: str
    page_type: str      # "PersonalFact" | "VocabEntry" | "CulturalEntry" | "Concept" | ...
    summary: str        # one-line summary (from index.md or DB)
    content: str = ""   # full markdown content, loaded on demand
    tags: list[str] = field(default_factory=list)
    story_score: int | None = None
    language: str | None = None   # ISO 639-1, for VocabEntry

    def load_content(self, wiki_root: Path = WIKI_ROOT) -> "WikiPage":
        """Load full file content into self.content. Returns self for chaining."""
        full_path = wiki_root / self.path
        if full_path.exists():
            self.content = full_path.read_text(encoding="utf-8")
        return self


# ---------------------------------------------------------------------------
# Public API — used by all agents and the supervisor
# ---------------------------------------------------------------------------

def search_wiki(
    query: str,
    page_type: str | None = None,
    language: str | None = None,
    limit: int = 10,
    wiki_root: Path = WIKI_ROOT,
) -> list[WikiPage]:
    """Search the knowledge graph. Automatically uses Phase 1 or Phase 2.

    Args:
        query:     Free-text search query.
        page_type: Optional filter — "PersonalFact", "VocabEntry", etc.
        language:  Optional filter for VocabEntry (ISO 639-1).
        limit:     Maximum number of results.
        wiki_root: Root of the knowledge-os repo.

    Returns:
        List of WikiPage objects, sorted by relevance (best first).
    """
    if _wiki_size(wiki_root) < WIKI_PAGE_THRESHOLD:
        return _search_index_md(query, page_type, language, limit, wiki_root)
    else:
        return _search_sqlite(query, page_type, language, limit, wiki_root)


def fetch_context(state: dict, wiki_root: Path = WIKI_ROOT) -> dict:
    """LangGraph node: extract keywords from raw_event and populate graph_context.

    Reads state["raw_event"], extracts keywords via Haiku, searches the graph,
    and writes results into state["graph_context"].
    """
    raw_event = state.get("raw_event", {})
    content = raw_event.get("content", "")
    user_hint = raw_event.get("user_hint", "")

    if not content:
        return {"graph_context": []}

    keywords = _extract_keywords(content + " " + user_hint)
    intent = state.get("classified_intent", "")

    # Intent-specific type filter for more precise results
    type_filter = None
    if intent == "vocab":
        type_filter = "VocabEntry"
    elif intent == "personal_fact":
        type_filter = "PersonalFact"

    pages = search_wiki(
        query=" ".join(keywords),
        page_type=type_filter,
        limit=8,
        wiki_root=wiki_root,
    )

    # Load full content for top results so agents have all the detail they need
    pages_with_content = [p.load_content(wiki_root) for p in pages[:5]]
    pages_summary_only = pages[5:]

    return {"graph_context": pages_with_content + pages_summary_only}


# ---------------------------------------------------------------------------
# Phase 1 — index.md keyword search
# ---------------------------------------------------------------------------

def _slug_to_tags(slug: str) -> list[str]:
    """Extract pseudo-tags from a slug like 'pf_2026-03-15_fahrrad-unfall'."""
    # Strip prefix (pf_, v_es_, c_es_, etc.) and date segments
    parts = re.split(r"[_\-]", slug)
    tags = []
    for part in parts:
        # Skip type prefixes, lang codes, and date parts
        if len(part) <= 2 or re.fullmatch(r"\d{4}|\d{2}", part):
            continue
        tags.append(part.lower())
    return tags


def _search_index_md(
    query: str,
    page_type: str | None,
    language: str | None,
    limit: int,
    wiki_root: Path,
) -> list[WikiPage]:
    index_path = wiki_root / "index.md"
    if not index_path.exists():
        return []

    index_text = index_path.read_text(encoding="utf-8")
    keywords = set(_extract_keywords(query))

    results: list[tuple[float, WikiPage]] = []

    # index.md format:
    #   ## PersonalFacts (12)
    #   - [[pf_2026-03-15_fahrrad-unfall]] — Unfall in München, story_score: 8
    current_section_type = ""
    section_re = re.compile(r"^## (.+?) \(\d+\)", re.MULTILINE)
    entry_re = re.compile(r"- \[\[(.+?)\]\](?: — (.+))?$")

    lines = index_text.splitlines()
    for line in lines:
        section_match = section_re.match(line)
        if section_match:
            current_section_type = _normalize_type(section_match.group(1))
            continue

        entry_match = entry_re.match(line.strip())
        if not entry_match:
            continue

        page_ref = entry_match.group(1)
        summary = entry_match.group(2) or ""

        if page_type and current_section_type != page_type:
            continue

        if language:
            if not page_ref.startswith(f"v_{language}_"):
                continue

        # Tags = slug parts + summary keywords
        entry_tags = set(_slug_to_tags(page_ref)) | set(_extract_keywords(summary))
        overlap = len(keywords & entry_tags) / max(len(keywords), 1)
        if overlap == 0:
            continue

        page = WikiPage(
            path=_ref_to_path(page_ref, current_section_type),
            title=page_ref,
            page_type=current_section_type,
            summary=summary,
            tags=sorted(entry_tags),
            story_score=_parse_story_score(summary),
            language=_parse_language(page_ref),
        )
        results.append((overlap, page))

    results.sort(key=lambda x: x[0], reverse=True)
    seen: set[str] = set()
    deduped = []
    for _, page in results:
        if page.path not in seen:
            seen.add(page.path)
            deduped.append(page)
    return deduped[:limit]


# ---------------------------------------------------------------------------
# Phase 2 — SQLite FTS5
# ---------------------------------------------------------------------------

def _search_sqlite(
    query: str,
    page_type: str | None,
    language: str | None,
    limit: int,
    wiki_root: Path,
) -> list[WikiPage]:
    db_path = wiki_root / "wiki_index.db"
    if not db_path.exists():
        # Fall back to index.md if SQLite hasn't been built yet
        return _search_index_md(query, page_type, language, limit, wiki_root)

    conn = sqlite3.connect(str(db_path))
    try:
        where_clauses = ["wiki_fts MATCH ?"]
        params: list[Any] = [query]

        if page_type:
            where_clauses.append("page_type = ?")
            params.append(page_type)
        if language:
            where_clauses.append("language = ?")
            params.append(language)

        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT path, title, page_type, summary, tags, story_score, language,
                   rank
            FROM wiki_fts
            WHERE {where_sql}
            ORDER BY rank
            LIMIT ?
        """
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        return [
            WikiPage(
                path=row[0],
                title=row[1],
                page_type=row[2],
                summary=row[3],
                tags=(row[4] or "").split(",") if row[4] else [],
                story_score=row[5],
                language=row[6],
            )
            for row in rows
        ]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wiki_size(wiki_root: Path) -> int:
    """Count markdown files in wiki/ directory."""
    wiki_dir = wiki_root / "wiki"
    if not wiki_dir.exists():
        return 0
    return sum(1 for _ in wiki_dir.rglob("*.md"))


def _extract_keywords(text: str) -> list[str]:
    """Extract search keywords from text. Uses simple heuristics — no LLM cost."""
    # Strip markdown, punctuation; keep meaningful tokens ≥ 4 chars
    text = re.sub(r"[#*_\[\]()]", "", text)
    tokens = re.findall(r"\b[a-zA-ZäöüÄÖÜß]{4,}\b", text)

    # German stopwords to exclude
    stopwords = {
        "dass", "aber", "auch", "noch", "mehr", "sehr", "dann", "when", "with",
        "this", "that", "have", "been", "from", "they", "will", "would", "beim",
        "nicht", "eine", "einem", "einer", "haben", "wurde", "werden",
    }
    keywords = [t.lower() for t in tokens if t.lower() not in stopwords]

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)

    return unique[:10]  # max 10 keywords


def _normalize_type(section_title: str) -> str:
    """Map index.md section header to canonical entity type."""
    mapping = {
        "personalfacts": "PersonalFact",
        "vocabentries": "VocabEntry",
        "vocabentries — es": "VocabEntry",
        "vocabentries — en": "VocabEntry",
        "culturalentries": "CulturalEntry",
        "languagebridges": "LanguageBridge",
        "concepts": "Concept",
        "styleprofiles": "StyleProfile",
    }
    return mapping.get(section_title.lower(), section_title)


def _ref_to_path(page_ref: str, page_type: str) -> str:
    """Convert a wiki ref like 'pf_2026-03-15_fahrrad-unfall' to a file path."""
    type_dirs = {
        "PersonalFact":   "wiki/personal/facts",
        "VocabEntry":     "wiki/language/vocab",
        "CulturalEntry":  "wiki/language/culture",
        "LanguageBridge": "wiki/language/bridges",
        "Concept":        "wiki/concepts",
        "StyleProfile":   "wiki/personal/style_refs",
    }
    base_dir = type_dirs.get(page_type, "wiki")
    return f"{base_dir}/{page_ref}.md"


def _parse_story_score(summary: str) -> int | None:
    match = re.search(r"story_score[:\s]+(\d+)", summary)
    return int(match.group(1)) if match else None


def _parse_language(page_ref: str) -> str | None:
    """Extract ISO language code from VocabEntry ref like 'v_es_madrugada'."""
    match = re.match(r"v_([a-z]{2})_", page_ref)
    return match.group(1) if match else None
