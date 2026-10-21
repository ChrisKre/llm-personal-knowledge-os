"""Stage 0 — deterministic inventory/dedup pass over the source mounts.

Source: ENT-058 extractor contract (a)–(f) verbatim, 02 §B2 (stage sketch),
QM R12 (is-a-clip check), brief 032 step 2. $0 — no LLM call anywhere in this
module (scope protection: if the script contains even one LLM call, the scope
is missed).

Extractor contract (ENT-058)
============================
(a) ``source`` URL → canonical ID: YouTube → ``yt:<video_id>`` (strip query
    fragments such as ``&t=…``/``&list=…``), otherwise ``url:<normalized>``.
(b) No-frontmatter fallback: title from the file name, ``id: sha1:<content-hash>``
    (a long report without frontmatter is the known case, 01 §A2). Also applies
    to ``.html``.
(c) Format switch ``.md``/``.html`` (html → BeautifulSoup text extraction;
    ``bs4`` is already a dependency, brief 032 F4).
(d) Empty-clip filter: body < ``EMPTY_CLIP_MIN_WORDS`` words →
    ``skipped: empty_clip``.
(e) ``tags: [clippings]`` is ignored (constant, carries no information).
(f) Is-a-clip check (QM R12): see below.

Reading of the is-a-clip check (f) — documented architecture decision
=====================================================================
R12 verbatim: "frontmatter has a ``source:`` URL **or** a derivable canonical
ID; otherwise → ``skipped: not_a_clipping``." So that (b) and (f) both have a
non-empty scope:

- Frontmatter present **with** a ``source`` URL → clipping (ID from (a)).
- **No** frontmatter (or a parse error, see below) → clipping via the (b)
  fallback (the ``sha1:`` ID is the derivable ID; long reports without
  frontmatter must stay processable).
- Frontmatter present but **without** a usable ``source`` URL →
  ``not_a_clipping`` (the web clipper always writes ``source``; frontmatter
  without a source = a manual note or a broken export, exactly the R12 edge).

Deviation from brief 032 (escalated in the session report): the candidates
named there all carry real ``source`` URLs and are, by the letter of ENT-058,
**clippings**. Skipping them deterministically would require a content
judgment (forbidden here; that is stage 1 / S033) or a domain blocklist (which
would also hit legitimate clips). The contract beats the brief's expectation.

Frontmatter: clean parse ONLY (brief 032 F3)
============================================
``yaml.safe_load`` on the unmodified FM block. The legacy repair in
``agents.frontmatter.parse`` is calibrated for wiki pages, not for Obsidian
clipper output, so it is deliberately NOT used here (lesson from S029). If the
parse fails, the (b) fallback applies; the file stays processable.

Three-stage dedup (deterministic, no embeddings — ENT-002)
==========================================================
1. ``byte``  — byte-identical file content.
2. ``id``    — same canonical ID (catches the same video clipped twice with
   ``&t=50s``/``&t=55s``).
3. ``near``  — ``SequenceMatcher.ratio() >= NEAR_DUPE_RATIO`` on the body,
   compared at **word-token level** (``body.split()``).
   ``real_quick_ratio``/``quick_ratio`` run first as upper bounds: a pure
   runtime optimization with identical results (brief 032 F5).
   Why tokens instead of raw characters (F5 case; the runtime was a real
   problem): at character level ``quick_ratio`` (character frequencies) is
   almost always > 0.9 for transcripts in the same language, so the expensive
   ``ratio()`` ran on dozens of 20–50 KB pairs (> 7 min CPU on a 49-file
   corpus). At token level the threshold stays 0.9 (contract value), the
   result is deterministic and more robust against whitespace/punctuation
   noise; a corpus run takes < 10 s.

Keeper rule per dupe group (deterministic): earliest ``created``, then the
shortest file name, then lexicographic order — the first clip without the
`` 1`` suffix wins.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit

import yaml

from scripts.ingest import EMPTY_CLIP_MIN_WORDS, NEAR_DUPE_RATIO, SOURCE_DIRS

_FM_DELIM_RE = re.compile(r"^\s*---\s*$")

# YouTube hosts for the canonical ``yt:`` ID (ENT-058 (a)).
_YT_HOSTS = ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be")
_YT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,}$")

# Tracking parameters stripped during ``url:`` normalization.
_TRACKING_PARAMS = ("utm_", "fbclid", "gclid", "ref")


@dataclass
class ClipRecord:
    """Inventory entry for one file from the source mounts (stage 0)."""

    path: str                    # vault-relative, POSIX
    title: str
    fmt: str                     # "md" | "html"
    canonical_id: str | None     # yt:/url:/sha1: — None only for not_a_clipping
    words: int
    created: str                 # ISO date from FM, "" if unknown
    status: str = "usable"       # usable|dupe|empty_clip|not_a_clipping|ledgered
    reason: str = ""
    dupe_of: str | None = None   # keeper path when status=dupe
    dedup_tier: str | None = None  # byte|id|near
    body: str = field(default="", repr=False)
    raw_sha1: str = field(default="", repr=False)


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def _fm_bounds(lines: list[str]) -> tuple[int, int]:
    """Indices of the two ``---`` delimiters, (-1, -1) if there is no FM block.

    Local copy of the delimiter logic (pattern ``2026-07-04_owner_flag``);
    deliberately does not use ``agents.frontmatter``, see the module docstring (F3).
    """
    start = end = -1
    for i, line in enumerate(lines):
        if _FM_DELIM_RE.match(line):
            if start == -1:
                start = i
            else:
                end = i
                break
    return start, end


def _parse_clean(text: str) -> tuple[dict[str, Any] | None, str]:
    """Clean parse: ``(frontmatter | None, body)``. None = (b) fallback.

    No legacy repair (F3): unparsable or missing FM → ``None`` and the whole
    text as the body (rather than the rest after a broken block; we
    conservatively take the whole text so the ``sha1:`` hash is stable).
    """
    lines = text.splitlines()
    start, end = _fm_bounds(lines)
    if start == -1 or end == -1 or start != 0:
        return None, text
    try:
        fm = yaml.safe_load("\n".join(lines[start + 1:end]))
    except yaml.YAMLError:
        return None, text
    if not isinstance(fm, dict):
        return None, text
    body = "\n".join(lines[end + 1:])
    return fm, body


def _html_to_text(html: str) -> tuple[str, str]:
    """(title, text) from an HTML file (format switch (c))."""
    from bs4 import BeautifulSoup  # already a dependency (brief 032 F4)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = (soup.title.get_text(strip=True) if soup.title else "")
    return title, soup.get_text(" ", strip=True)


def canonical_id_from_source(source: str) -> str | None:
    """ENT-058 (a): ``source`` URL → ``yt:<video_id>`` | ``url:<normalized>``.

    None if ``source`` is not an http(s) URL.
    """
    if not isinstance(source, str) or not source.strip():
        return None
    parts = urlsplit(source.strip())
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return None
    host = parts.netloc.lower().removeprefix("www.")

    if parts.netloc.lower() in _YT_HOSTS:
        video_id = ""
        if host == "youtu.be":
            video_id = parts.path.strip("/").split("/")[0]
        else:
            qs = dict(parse_qsl(parts.query))
            video_id = qs.get("v", "")
            if not video_id and parts.path.startswith(("/shorts/", "/embed/")):
                video_id = parts.path.split("/")[2] if len(parts.path.split("/")) > 2 else ""
        if _YT_ID_RE.match(video_id):
            return f"yt:{video_id}"
        # YouTube URL without an extractable video ID → generic url: form.

    # url:<normalized>: scheme-agnostic, host lowercased without www.,
    # no fragment, no tracking parameters, no trailing slash.
    query = urlencode([
        (k, v) for k, v in parse_qsl(parts.query)
        if not k.lower().startswith(_TRACKING_PARAMS[0])
        and k.lower() not in _TRACKING_PARAMS[1:]
    ])
    path = parts.path.rstrip("/")
    norm = f"{host}{path}"
    if query:
        norm += f"?{query}"
    return f"url:{norm}"


def _sha1_id(body: str) -> str:
    """(b) fallback ID: content hash. ``\\r\\n`` is normalized so the ID is
    stable regardless of autocrlf checkout variants."""
    normalized = body.replace("\r\n", "\n").encode("utf-8")
    return f"sha1:{hashlib.sha1(normalized).hexdigest()}"


def extract_clip(path: Path, repo_root: Path) -> ClipRecord:
    """One file from a source mount → ``ClipRecord`` (status without ledger or
    dedup knowledge yet: ``usable``, ``empty_clip`` or ``not_a_clipping``).
    """
    rel = path.relative_to(repo_root).as_posix()
    raw_bytes = path.read_bytes()
    # errors="replace": raw data must never crash the run (mojibake file
    # names are known to exist); the bytes themselves are never touched.
    # Strip the BOM, otherwise the FM delimiter match misses line 0.
    text = raw_bytes.decode("utf-8", errors="replace").lstrip("﻿")
    raw_sha1 = hashlib.sha1(
        text.replace("\r\n", "\n").encode("utf-8")).hexdigest()

    fmt = path.suffix.lower().lstrip(".")
    fm: dict[str, Any] | None
    if fmt == "html":
        html_title, body = _html_to_text(text)
        fm = None
        title = html_title or path.stem
    else:
        fm, body = _parse_clean(text)
        title = str((fm or {}).get("title") or "").strip() or path.stem

    created = str((fm or {}).get("created") or "")
    words = len(body.split())

    # Is-a-clip check (f) — see the module docstring for how it is read.
    if fm is None:
        canonical_id = _sha1_id(body)          # (b) fallback: long report / HTML case
    else:
        canonical_id = canonical_id_from_source(fm.get("source"))
        if canonical_id is None:
            return ClipRecord(
                path=rel, title=title, fmt=fmt, canonical_id=None,
                words=words, created=created, status="not_a_clipping",
                reason="frontmatter without source: URL (QM R12)",
                body=body, raw_sha1=raw_sha1,
            )

    record = ClipRecord(
        path=rel, title=title, fmt=fmt, canonical_id=canonical_id,
        words=words, created=created, body=body, raw_sha1=raw_sha1,
    )
    if words < EMPTY_CLIP_MIN_WORDS:
        record.status = "empty_clip"
        record.reason = f"{words} words < {EMPTY_CLIP_MIN_WORDS}"
    return record


def walk_sources(repo_root: Path,
                 source_dirs: tuple[str, ...] = SOURCE_DIRS) -> list[Path]:
    """All ``.md``/``.html`` files in the mounts, sorted deterministically."""
    files: list[Path] = []
    for mount in source_dirs:
        base = repo_root / Path(mount)
        if not base.exists():
            continue
        files.extend(p for p in base.rglob("*")
                     if p.is_file() and p.suffix.lower() in (".md", ".html"))
    return sorted(files, key=lambda p: p.relative_to(repo_root).as_posix())


# ---------------------------------------------------------------------------
# Dedup (three stages)
# ---------------------------------------------------------------------------

def _keeper_sort_key(rec: ClipRecord) -> tuple[str, int, str]:
    return (rec.created or "9999-99-99", len(rec.path), rec.path)


def _mark_dupes(group: list[ClipRecord], tier: str) -> None:
    group.sort(key=_keeper_sort_key)
    keeper = group[0]
    for rec in group[1:]:
        rec.status = "dupe"
        rec.dedup_tier = tier
        rec.dupe_of = keeper.path
        rec.reason = f"{tier} dupe of {keeper.path}"


def dedup(records: list[ClipRecord]) -> None:
    """Three-stage dedup, in place, over all ``status == "usable"`` records.

    Order byte → id → near; a record already marked as a dupe takes no part
    in later stages.
    """
    # Stage 1: byte-identical.
    by_hash: dict[str, list[ClipRecord]] = {}
    for rec in records:
        if rec.status == "usable":
            by_hash.setdefault(rec.raw_sha1, []).append(rec)
    for group in by_hash.values():
        if len(group) > 1:
            _mark_dupes(group, "byte")

    # Stage 2: same canonical ID.
    by_id: dict[str, list[ClipRecord]] = {}
    for rec in records:
        if rec.status == "usable" and rec.canonical_id:
            by_id.setdefault(rec.canonical_id, []).append(rec)
    for group in by_id.values():
        if len(group) > 1:
            _mark_dupes(group, "id")

    # Stage 3: near dupes (SequenceMatcher >= NEAR_DUPE_RATIO on the body,
    # word-token level — rationale in the module docstring).
    survivors = [r for r in records if r.status == "usable"]
    tokens = {id(r): r.body.split() for r in survivors}
    for i, a in enumerate(survivors):
        if a.status != "usable":
            continue
        for b in survivors[i + 1:]:
            if b.status != "usable":
                continue
            sm = SequenceMatcher(None, tokens[id(a)], tokens[id(b)],
                                 autojunk=False)
            # Upper bounds first — identical result, just faster
            # (ratio() on 50k-character pairs is the real cost driver).
            if sm.real_quick_ratio() < NEAR_DUPE_RATIO:
                continue
            if sm.quick_ratio() < NEAR_DUPE_RATIO:
                continue
            if sm.ratio() >= NEAR_DUPE_RATIO:
                _mark_dupes([a, b], "near")
                if a.status != "usable":
                    break
