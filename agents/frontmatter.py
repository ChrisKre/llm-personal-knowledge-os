"""Frontmatter helper — single-source read/write/patch for wiki Markdown.

Consolidates the three formerly separate frontmatter code paths (see backlog BL-03):
- ``scripts/export_anki.py:79-98`` (regex-based, robust against the legacy indent)
- ``agents/language_agent.py`` ``_build_frontmatter()`` (f-string dedent, source of the bug)
- ``scripts/rebuild_index.py`` (planned in BL-04)

Since BL-03, ``language_agent`` uses this helper directly; ``export_anki`` was
switched over in BL-04 (order as planned in the workshop).

Format convention (established in ENT-005, enforced by BL-03):
- ``yaml.safe_load`` must succeed without workarounds.
- When writing: ``sort_keys=False`` (property order is kept), ``allow_unicode=True``
  (Spanish and German without escapes), ``default_flow_style=False`` (block style
  throughout, diff-friendly; tags and bridges become multi-line).
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

_FM_DELIM_RE = re.compile(r"^\s*---\s*$")


def _split(text: str) -> tuple[str, str, str]:
    """Return (frontmatter_block, body, trailing_newline_marker).

    Splits at the first two ``---`` lines. Robust against the legacy indent bug
    (the FM block may be indented as a whole); the indentation is not removed
    here but in ``_normalize_legacy_fm`` during parsing.
    """
    lines = text.splitlines(keepends=False)
    start = end = -1
    for i, line in enumerate(lines):
        if _FM_DELIM_RE.match(line):
            if start == -1:
                start = i
            else:
                end = i
                break
    if start == -1 or end == -1:
        return "", text, ""
    fm = "\n".join(lines[start + 1:end])
    body = "\n".join(lines[end + 1:])
    trailing = "\n" if text.endswith("\n") else ""
    return fm, body, trailing


_BARE_QUESTIONMARK_RE = re.compile(r"^(\s*[A-Za-z_][\w]*:\s*)\?(\s*)$")


def _normalize_legacy_fm(fm_text: str) -> str:
    """Repair legacy FM blocks for ``yaml.safe_load``.

    Two defects are handled:

    1. *Indent bug*: ``_build_frontmatter`` interpolated multi-line substrings
       (``cross_language_bridges:\\n  - lang: de\\n    type: ?...``) into a
       ``textwrap.dedent`` f-string. The interpolated lines started at column 0,
       the rest was indented by 16. ``dedent`` computed the minimal common
       prefix (= 0) and removed nothing -> broken YAML.
       Repair: find the most common indentation and strip it.

    2. *Bare question mark bug*: ``type: ?`` as the bridge type default. ``?`` is the
       YAML key indicator -> ``ScannerError: mapping keys are not allowed here``.
       Repair: ``key: ?`` -> ``key: '?'`` line by line.
    """
    lines = fm_text.splitlines()
    indents: Counter[int] = Counter()
    for line in lines:
        if not line.strip():
            continue
        m = re.match(r"^( +)", line)
        if m:
            indents[len(m.group(1))] += 1
    base = max(indents, key=lambda k: (indents[k], k)) if indents else 0
    prefix = " " * base
    out: list[str] = []
    for line in lines:
        if base and line.startswith(prefix):
            line = line[base:]
        m = _BARE_QUESTIONMARK_RE.match(line)
        if m:
            line = f"{m.group(1)}'?'{m.group(2)}"
        out.append(line)
    return "\n".join(out)


def parse(text: str) -> tuple[dict[str, Any], str]:
    """Parse Markdown-with-frontmatter -> ``(frontmatter_dict, body)``.

    ``frontmatter_dict`` is empty if there is no FM block. The body is the
    rest of the file, without the leading ``---`` marker.

    Raises ``yaml.YAMLError`` if the YAML is still invalid after the legacy
    repair.
    """
    fm_raw, body, _ = _split(text)
    if not fm_raw:
        return {}, text
    try:
        data = yaml.safe_load(fm_raw)
    except yaml.YAMLError:
        data = yaml.safe_load(_normalize_legacy_fm(fm_raw))
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise yaml.YAMLError(f"Frontmatter must be a mapping, got {type(data).__name__}")
    return data, body


def render(frontmatter: dict[str, Any], body: str) -> str:
    """Render ``(frontmatter_dict, body)`` -> Markdown-with-frontmatter.

    Guarantees:
    - ``yaml.safe_load`` of the output returns the same dict.
    - Property order is preserved (``sort_keys=False``).
    - The body is appended unchanged; a single separating blank block
      between FM and body is normalized.
    """
    fm_yaml = yaml.dump(
        frontmatter,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    body_clean = body.lstrip("\n")
    if body_clean:
        return f"---\n{fm_yaml}---\n\n{body_clean}"
    return f"---\n{fm_yaml}---\n"


def read(path: Path) -> tuple[dict[str, Any], str]:
    """Read a Markdown file and parse its frontmatter."""
    return parse(path.read_text(encoding="utf-8"))


def write(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    """Write a Markdown file with rendered frontmatter."""
    path.write_text(render(frontmatter, body), encoding="utf-8")


def patch(path: Path, **updates: Any) -> dict[str, Any]:
    """Read, update top-level frontmatter keys, write back. Returns new dict."""
    data, body = read(path)
    data.update(updates)
    write(path, data, body)
    return data
