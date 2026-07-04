"""Stufe 0 — deterministischer Inventory-/Dedup-Pass ueber die Source-Mounts.

Quelle: ENT-058 Extractor-Vertrag (a)–(f) woertlich, 02 §B2 (Stufen-Skizze),
QM R12 (Ist-Clip-Check), Brief 032 Schritt 2. $0 — kein LLM-Call an keiner
Stelle dieses Moduls (Scope-Schutz: enthaelt das Skript auch nur einen
LLM-Call, ist der Scope verfehlt).

Extractor-Vertrag (ENT-058)
===========================
(a) ``source``-URL → kanonische ID: YouTube → ``yt:<video_id>`` (Query-
    Fragmente wie ``&t=…``/``&list=…`` strippen), sonst ``url:<normalisiert>``.
(b) No-Frontmatter-Fallback: Titel aus Dateiname, ``id: sha1:<content-hash>``
    (Langbericht ist der bekannte Fall, 01 §A2). Gilt auch fuer ``.html``.
(c) Format-Weiche ``.md``/``.html`` (html → BeautifulSoup-Textextraktion;
    ``bs4`` liegt bereits in der venv, Brief-032 F4).
(d) Leer-Clip-Filter: Body < ``EMPTY_CLIP_MIN_WORDS`` Woerter →
    ``skipped: empty_clip``.
(e) ``tags: [clippings]`` wird ignoriert (konstant, kein Informationswert).
(f) Ist-Clip-Check (QM R12): siehe unten.

Lesart des Ist-Clip-Checks (f) — dokumentierte Architektur-Entscheidung
=======================================================================
R12 woertlich: „Frontmatter hat ``source:``-URL **oder** kanonische ID
ableitbar; sonst → ``skipped: not_a_clipping``." Damit (b) und (f) beide
einen nicht-leeren Anwendungsbereich haben, gilt:

- Frontmatter vorhanden **mit** ``source``-URL → Clipping (ID aus (a)).
- **Kein** Frontmatter (oder Parse-Fehler, s.u.) → Clipping via (b)-Fallback
  (``sha1:``-ID ist die ableitbare ID — der Langbericht muss verarbeitbar
  bleiben, er ist die wertvollste Health-Quelle).
- Frontmatter vorhanden, aber **ohne** verwertbare ``source``-URL →
  ``not_a_clipping`` (der Web Clipper schreibt immer ``source``; FM ohne
  Quelle = manuelle Notiz/kaputter Export — genau die R12-Kante).

Abweichung zum Brief 032 (im Sessionbericht eskaliert): Die dort genannten
Kandidaten (``Candy.md``, ``Preply*.md``, ``massive-…``) tragen alle echte
``source``-URLs und sind nach ENT-058 woertlich **Clippings** — sie
deterministisch zu skippen verlangte inhaltliche Bewertung (verboten,
Stufe 1/S033) oder eine Domain-Blocklist (traefe auch die Karpathy-
GitHub-Clips). Vertrag schlaegt Brief-Erwartung.

Frontmatter: NUR clean parse (Brief-032 F3)
===========================================
``yaml.safe_load`` auf den unveraenderten FM-Block. Der Legacy-Repair in
``agents.frontmatter.parse`` ist fuer Wiki-Seiten kalibriert, nicht fuer
Obsidian-Clipper-Output — er wird hier bewusst NICHT benutzt (S029-Lehre).
Scheitert der Parse, greift der (b)-Fallback; das File bleibt verarbeitbar.

Dedup dreistufig (deterministisch, kein Embedding — ENT-002)
============================================================
1. ``byte``  — byte-identischer Datei-Inhalt.
2. ``id``    — gleiche kanonische ID (faengt das Dupe-Clip-Paar
   ``&t=50s``/``&t=55s`` und das NEARDUPE-Paar, selbes Video).
3. ``near``  — ``SequenceMatcher.ratio() >= NEAR_DUPE_RATIO`` auf dem Body,
   verglichen auf **Wort-Token-Ebene** (``body.split()``).
   ``real_quick_ratio``/``quick_ratio`` als obere Schranken vorab — reine
   Laufzeit-Optimierung, identisches Ergebnis (Brief-032 F5).
   Warum Tokens statt Roh-Zeichen (F5-Fall, Laufzeit stoerte real): auf
   Zeichen-Ebene ist ``quick_ratio`` (Zeichen-Haeufigkeiten) fuer
   gleichsprachige Transkripte fast immer > 0,9 — das teure ``ratio()``
   lief damit auf dutzenden 20–50-KB-Paaren (>7 min CPU auf dem
   49-File-Korpus). Token-Ebene: Schwelle unveraendert 0,9 (Vertragswert),
   deterministisch, robuster gegen Whitespace-/Punktuations-Rauschen;
   Korpus-Lauf < 10 s.

Keeper-Regel pro Dupe-Gruppe (deterministisch): fruehestes ``created``,
dann kuerzester Dateiname, dann lexikographisch — die Erst-Clip-Fassung
ohne `` 1``-Suffix gewinnt.
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

# YouTube-Hosts fuer die kanonische ``yt:``-ID (ENT-058 (a)).
_YT_HOSTS = ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be")
_YT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,}$")

# Tracking-Parameter, die bei ``url:``-Normalisierung gestrippt werden.
_TRACKING_PARAMS = ("utm_", "fbclid", "gclid", "ref")


@dataclass
class ClipRecord:
    """Inventory-Eintrag eines Files aus den Source-Mounts (Stufe 0)."""

    path: str                    # repo-relativ, POSIX
    title: str
    fmt: str                     # "md" | "html"
    canonical_id: str | None     # yt:/url:/sha1: — None nur bei not_a_clipping
    words: int
    created: str                 # ISO-Datum aus FM, "" wenn unbekannt
    status: str = "usable"       # usable|dupe|empty_clip|not_a_clipping|ledgered
    reason: str = ""
    dupe_of: str | None = None   # Keeper-Pfad bei status=dupe
    dedup_tier: str | None = None  # byte|id|near
    body: str = field(default="", repr=False)
    raw_sha1: str = field(default="", repr=False)


# ---------------------------------------------------------------------------
# Extraktion
# ---------------------------------------------------------------------------

def _fm_bounds(lines: list[str]) -> tuple[int, int]:
    """Indices der beiden ``---``-Delimiter, (-1, -1) wenn kein FM-Block.

    Lokale Kopie der Delimiter-Logik (Muster ``2026-07-04_owner_flag``) —
    bewusst keine ``agents.frontmatter``-Nutzung, s. Modul-Docstring (F3).
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
    """Clean parse: ``(frontmatter | None, body)``. None = (b)-Fallback.

    Kein Legacy-Repair (F3): unparsbares/fehlendes FM → ``None`` und der
    komplette Text als Body (bzw. Rest nach dem kaputten Block — wir nehmen
    konservativ den ganzen Text, damit der ``sha1:``-Hash stabil ist).
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
    """(title, text) aus einem HTML-File (Format-Weiche (c))."""
    from bs4 import BeautifulSoup  # in der venv vorhanden (Brief-032 F4)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = (soup.title.get_text(strip=True) if soup.title else "")
    return title, soup.get_text(" ", strip=True)


def canonical_id_from_source(source: str) -> str | None:
    """ENT-058 (a): ``source``-URL → ``yt:<video_id>`` | ``url:<normalisiert>``.

    None wenn ``source`` keine http(s)-URL ist.
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
        # YouTube-URL ohne extrahierbare Video-ID → generische url:-Form.

    # url:<normalisiert>: https-Schema-agnostisch, Host lowercase ohne www.,
    # Fragment weg, Tracking-Parameter weg, Trailing-Slash weg.
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
    """(b)-Fallback-ID: Content-Hash. ``\\r\\n`` normalisiert, damit die ID
    unabhaengig von autocrlf-Checkout-Varianten stabil ist."""
    normalized = body.replace("\r\n", "\n").encode("utf-8")
    return f"sha1:{hashlib.sha1(normalized).hexdigest()}"


def extract_clip(path: Path, repo_root: Path) -> ClipRecord:
    """Ein File aus einem Source-Mount → ``ClipRecord`` (Status noch ohne
    Ledger-/Dedup-Wissen: ``usable``, ``empty_clip`` oder ``not_a_clipping``).
    """
    rel = path.relative_to(repo_root).as_posix()
    raw_bytes = path.read_bytes()
    # errors="replace": Rohdaten duerfen den Lauf nie crashen (Mojibake-
    # Bestand ist bekannt); die Bytes selbst werden nie angefasst.
    # BOM strippen, sonst verfehlt der FM-Delimiter-Match Zeile 0.
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

    # Ist-Clip-Check (f) — Lesart siehe Modul-Docstring.
    if fm is None:
        canonical_id = _sha1_id(body)          # (b)-Fallback, LONGDOC-/HTML-Fall
    else:
        canonical_id = canonical_id_from_source(fm.get("source"))
        if canonical_id is None:
            return ClipRecord(
                path=rel, title=title, fmt=fmt, canonical_id=None,
                words=words, created=created, status="not_a_clipping",
                reason="Frontmatter ohne source:-URL (QM R12)",
                body=body, raw_sha1=raw_sha1,
            )

    record = ClipRecord(
        path=rel, title=title, fmt=fmt, canonical_id=canonical_id,
        words=words, created=created, body=body, raw_sha1=raw_sha1,
    )
    if words < EMPTY_CLIP_MIN_WORDS:
        record.status = "empty_clip"
        record.reason = f"{words} Woerter < {EMPTY_CLIP_MIN_WORDS}"
    return record


def walk_sources(repo_root: Path,
                 source_dirs: tuple[str, ...] = SOURCE_DIRS) -> list[Path]:
    """Alle ``.md``/``.html``-Files der Mounts, deterministisch sortiert."""
    files: list[Path] = []
    for mount in source_dirs:
        base = repo_root / Path(mount)
        if not base.exists():
            continue
        files.extend(p for p in base.rglob("*")
                     if p.is_file() and p.suffix.lower() in (".md", ".html"))
    return sorted(files, key=lambda p: p.relative_to(repo_root).as_posix())


# ---------------------------------------------------------------------------
# Dedup (dreistufig)
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
        rec.reason = f"{tier}-Dupe von {keeper.path}"


def dedup(records: list[ClipRecord]) -> None:
    """Dreistufiger Dedup in-place ueber alle ``status == "usable"``-Records.

    Reihenfolge byte → id → near; ein bereits markierter Dupe nimmt an
    spaeteren Stufen nicht mehr teil.
    """
    # Stufe 1: byte-identisch.
    by_hash: dict[str, list[ClipRecord]] = {}
    for rec in records:
        if rec.status == "usable":
            by_hash.setdefault(rec.raw_sha1, []).append(rec)
    for group in by_hash.values():
        if len(group) > 1:
            _mark_dupes(group, "byte")

    # Stufe 2: gleiche kanonische ID.
    by_id: dict[str, list[ClipRecord]] = {}
    for rec in records:
        if rec.status == "usable" and rec.canonical_id:
            by_id.setdefault(rec.canonical_id, []).append(rec)
    for group in by_id.values():
        if len(group) > 1:
            _mark_dupes(group, "id")

    # Stufe 3: Near-Dupes (SequenceMatcher >= NEAR_DUPE_RATIO auf Body,
    # Wort-Token-Ebene — Begruendung im Modul-Docstring).
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
            # Obere Schranken zuerst — identisches Ergebnis, nur schneller
            # (ratio() auf 50k-Zeichen-Paaren ist der reale Kostentreiber).
            if sm.real_quick_ratio() < NEAR_DUPE_RATIO:
                continue
            if sm.quick_ratio() < NEAR_DUPE_RATIO:
                continue
            if sm.ratio() >= NEAR_DUPE_RATIO:
                _mark_dupes([a, b], "near")
                if a.status != "usable":
                    break
