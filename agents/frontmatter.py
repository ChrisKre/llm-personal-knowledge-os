"""Frontmatter helper — single-source read/write/patch fuer Wiki-Markdown.

Konsolidiert die drei verteilten Frontmatter-Pfade (siehe BL-03 Backlog):
- ``scripts/export_anki.py:79-98`` (regex-basiert, robust gegen Legacy-Indent)
- ``agents/language_agent.py`` ``_build_frontmatter()`` (f-string-dedent, Quelle des Bugs)
- ``scripts/rebuild_index.py`` (geplant in BL-04)

Nach BL-03 nutzt ``language_agent`` diesen Helper direkt; ``export_anki`` wird in
BL-04 umgestellt (Reihenfolge laut Workshop).

Format-Konvention (etabliert ENT-005, durchgesetzt durch BL-03):
- ``yaml.safe_load`` muss ohne Workaround durchlaufen.
- Beim Schreiben: ``sort_keys=False`` (Property-Reihenfolge bleibt), ``allow_unicode=True``
  (Spanisch + Deutsch ohne Escape), ``default_flow_style=False`` (alles Block-Style,
  diff-freundlich; Tags + Bridges werden multi-line).
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

    Splits at the first two ``---`` lines. Robust gegen den Legacy-Indent-Bug
    (FM-Block kann komplett einrueckt sein); die Indentation wird nicht hier
    entfernt, sondern in ``_normalize_legacy_fm`` waehrend des Parses.
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
    """Repariere Legacy-FM-Bloecke fuer ``yaml.safe_load``.

    Zwei Defekte adressiert:

    1. *Indent-Bug*: ``_build_frontmatter`` interpolierte mehrzeilige Substrings
       (``cross_language_bridges:\\n  - lang: de\\n    type: ?...``) in einen
       ``textwrap.dedent``-f-string. Die interpolierten Zeilen begannen bei Spalte 0,
       der Rest war 16-fach eingerueckt. ``dedent`` errechnete den minimalen
       gemeinsamen Prefix (= 0) und entfernte nichts -> kaputtes YAML.
       Reparatur: haeufigste Einrueckung ermitteln, abziehen.

    2. *Bare-Questionmark-Bug*: ``type: ?`` als Bridge-Type-Default. ``?`` ist YAML-
       Key-Indicator -> ``ScannerError: mapping keys are not allowed here``.
       Reparatur: ``key: ?`` -> ``key: '?'`` zeilenweise.
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

    ``frontmatter_dict`` ist leer wenn kein FM-Block existiert. Body ist der
    Rest des Files, ohne fuehrenden ``---``-Marker.

    Raises ``yaml.YAMLError`` wenn auch nach Legacy-Repair kein gueltiges YAML
    entsteht.
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

    Garantien:
    - ``yaml.safe_load`` der Ausgabe ergibt das gleiche Dict zurueck.
    - Property-Reihenfolge bleibt erhalten (``sort_keys=False``).
    - Body wird unveraendert eingehaengt; ein einzelner Leerzeichen-trennender
      Block zwischen FM und Body wird normalisiert.
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
