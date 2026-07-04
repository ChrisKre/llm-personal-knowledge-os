"""BL-16 / QK-21a: Stufe-0-Pfade der Clippings-Ingestion, deterministisch.

Mini-Korpus aus **synthetischen** Fixtures (Brief 032 Schritt 4 — nicht die
echten Clippings kopieren), gebaut pro Test in ``tmp_path`` (Muster
``test_topicpage_index.py``). Abgedeckt:

- Dupe-Clip-Muster: gleiche Video-ID, verschiedene ``&t=`` → ID-Dupe.
- NEARDUPE-Muster: Near-Dupe via ``SequenceMatcher >= 0,9``.
- Byte-identisches Paar (Preply-Muster).
- No-Frontmatter-File → Titel aus Dateiname, ``sha1:``-ID (LONGDOC-Muster).
- ``.html``-File → Format-Weiche, bs4-Textextraktion.
- Leer-Clip (< 150 Woerter) → ``empty_clip``.
- Frontmatter ohne ``source``-URL → ``not_a_clipping`` (QM R12).
- Idempotenz: zweiter Lauf gegen volles Ledger filtert alles → nothing to do.
- Ledger-Rekonstruktion aus Fixture-TopicPage (Selbstheilung 02 §B2).
- Dry-run schreibt nichts (kein Ledger-Eintrag, Quell-Bytes unveraendert).
- Live-Lauf ohne Backup-Branch → Abbruch (RuntimeError).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ingest import EMPTY_CLIP_MIN_WORDS, LEDGER_PATH, SOURCE_DIRS
from scripts.ingest.ledger import load_ledger, reconstruct_ledger, save_ledger
from scripts.ingest.stage0 import canonical_id_from_source, extract_clip
from scripts.ingest_clippings import run

MOUNT = "raw/Wiki/Clippings/"

LONG_BODY = " ".join(f"wort{i} inhalt claim beleg satzbau" for i in range(60))
NEAR_BODY_A = " ".join(f"zeile{i} sauna erholung protokoll evidenz"
                       for i in range(80))
NEAR_BODY_B = NEAR_BODY_A + " nachtrag am ende mit wenigen extra worten"


def _clip(source: str, body: str, created: str = "2026-06-02",
          title: str = "Fixture") -> str:
    return (f'---\ntitle: "{title}"\nsource: "{source}"\n'
            f'created: {created}\ntags:\n  - "clippings"\n---\n{body}\n')


def _write(root: Path, name: str, text: str) -> Path:
    target = root / MOUNT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def _run(root: Path, **kwargs) -> dict:
    kwargs.setdefault("dry_run", True)
    kwargs.setdefault("ledger_path", root / "ledger.json")
    kwargs.setdefault("out_dir", root / "out")
    kwargs.setdefault("source_dirs", SOURCE_DIRS)
    return run(repo_root=root, **kwargs)


def _by_name(result: dict) -> dict[str, object]:
    return {Path(r.path).name: r for r in result["records"]}


# ---------------------------------------------------------------------------
# Extractor-Vertrag (a)–(f)
# ---------------------------------------------------------------------------

def test_canonical_id_youtube_strips_fragments() -> None:
    """(a): Dupe-Clip-Falle — ``&t=…``/``&list=…`` duerfen die ID nicht
    aufspalten."""
    variants = [
        "https://www.youtube.com/watch?v=dupeVideo01&t=50s",
        "https://www.youtube.com/watch?v=dupeVideo01&t=55s",
        "https://www.youtube.com/watch?v=dupeVideo01&list=RDx&start_radio=1",
        "https://youtu.be/dupeVideo01",
        "https://m.youtube.com/watch?v=dupeVideo01",
    ]
    ids = {canonical_id_from_source(s) for s in variants}
    assert ids == {"yt:dupeVideo01"}


def test_canonical_id_url_normalized() -> None:
    assert canonical_id_from_source(
        "https://Example.com/pfad/?utm_source=x#frag"
    ) == "url:example.com/pfad"
    # Nicht-URL / leer → keine ID (R12-Input).
    assert canonical_id_from_source("") is None
    assert canonical_id_from_source("kein link") is None


def test_no_frontmatter_fallback_sha1(tmp_path: Path) -> None:
    """(b): LONGDOC-Muster — kein FM, aber substantieller Body → sha1:-ID,
    Titel aus Dateiname, bleibt nutzbar."""
    p = _write(tmp_path, "Langbericht_Fixture.md",
               "# Fachbericht\n\n" + LONG_BODY)
    rec = extract_clip(p, tmp_path)
    assert rec.status == "usable"
    assert rec.canonical_id.startswith("sha1:")
    assert rec.title == "Langbericht_Fixture"


def test_html_format_weiche(tmp_path: Path) -> None:
    """(c): .html wird geparst (bs4), Script/Style fliegen raus."""
    html = ("<!DOCTYPE html><html><head><title>Long Report</title>"
            "<script>ignorier();</script></head><body><h1>Therapie</h1><p>"
            + LONG_BODY + "</p></body></html>")
    p = _write(tmp_path, "report.html", html)
    rec = extract_clip(p, tmp_path)
    assert rec.fmt == "html"
    assert rec.status == "usable"
    assert rec.title == "Long Report"
    assert rec.canonical_id.startswith("sha1:")
    assert "ignorier" not in rec.body


def test_empty_clip_filter(tmp_path: Path) -> None:
    """(d): Body < 150 Woerter → empty_clip (Fehl-Clip-Muster)."""
    p = _write(tmp_path, "fehlclip.md",
               _clip("https://www.youtube.com/watch?v=EpgY5iE4rhX",
                     "nur ein paar worte"))
    rec = extract_clip(p, tmp_path)
    assert rec.status == "empty_clip"
    assert rec.canonical_id == "yt:EpgY5iE4rhX"
    assert rec.words < EMPTY_CLIP_MIN_WORDS


def test_not_a_clipping_fm_without_source(tmp_path: Path) -> None:
    """(f)/R12: FM vorhanden, aber ohne source-URL → not_a_clipping —
    die manuelle Notiz im Mount, die der Scan nie in die Pipeline geben darf."""
    p = _write(tmp_path, "notiz.md",
               "---\ntitle: Manuelle Notiz\ncreated: 2026-07-01\n---\n"
               + LONG_BODY)
    rec = extract_clip(p, tmp_path)
    assert rec.status == "not_a_clipping"
    assert rec.canonical_id is None


# ---------------------------------------------------------------------------
# Dedup dreistufig
# ---------------------------------------------------------------------------

def test_dedup_same_video_id(tmp_path: Path) -> None:
    """Dupe-Clip-Paar: gleiche Video-ID, verschiedene ``&t=`` →
    ID-Dupe; Keeper = fruehestes ``created``."""
    _write(tmp_path, "DupeClip.md",
           _clip("https://www.youtube.com/watch?v=dupeVideo01&t=50s",
                 LONG_BODY, created="2026-06-02"))
    _write(tmp_path, "DupeClip 1.md",
           _clip("https://www.youtube.com/watch?v=dupeVideo01&t=55s",
                 LONG_BODY + " minimal anders", created="2026-06-05"))
    result = _run(tmp_path)
    recs = _by_name(result)
    assert recs["DupeClip.md"].status == "usable"
    assert recs["DupeClip 1.md"].status == "dupe"
    assert recs["DupeClip 1.md"].dedup_tier == "id"
    assert recs["DupeClip 1.md"].dupe_of.endswith("DupeClip.md")


def test_dedup_byte_identical(tmp_path: Path) -> None:
    """Preply-Muster: byte-identische Files → byte-Dupe."""
    text = _clip("https://example.com/lesson/1", LONG_BODY)
    _write(tmp_path, "Preply.md", text)
    _write(tmp_path, "Preply 1.md", text)
    result = _run(tmp_path)
    recs = _by_name(result)
    assert recs["Preply.md"].status == "usable"
    assert recs["Preply 1.md"].status == "dupe"
    assert recs["Preply 1.md"].dedup_tier == "byte"


def test_dedup_near_dupe_sequencematcher(tmp_path: Path) -> None:
    """NEARDUPE-Muster: verschiedene URLs, Body-Aehnlichkeit >= 0,9 →
    near-Dupe."""
    _write(tmp_path, "Tips.md",
           _clip("https://www.youtube.com/watch?v=aaaaaaaaaaa",
                 NEAR_BODY_A, created="2026-04-18"))
    _write(tmp_path, "Tips 1.md",
           _clip("https://www.youtube.com/watch?v=bbbbbbbbbbb",
                 NEAR_BODY_B, created="2026-06-02"))
    result = _run(tmp_path)
    recs = _by_name(result)
    assert recs["Tips.md"].status == "usable"
    assert recs["Tips 1.md"].status == "dupe"
    assert recs["Tips 1.md"].dedup_tier == "near"


def test_distinct_clips_stay_usable(tmp_path: Path) -> None:
    """Gegenprobe: zwei verschiedene Clips bleiben beide nutzbar."""
    _write(tmp_path, "A.md",
           _clip("https://www.youtube.com/watch?v=aaaaaaaaaaa", LONG_BODY))
    _write(tmp_path, "B.md",
           _clip("https://www.youtube.com/watch?v=bbbbbbbbbbb",
                 " ".join(f"anderes{i} thema vokabel spanisch beispiel"
                          for i in range(70))))
    result = _run(tmp_path)
    assert result["counts"]["usable"] == 2
    assert result["counts"]["dupe"] == 0


# ---------------------------------------------------------------------------
# Ledger: Idempotenz, Selbstheilung, Dry-run-Guard, Backup-Branch
# ---------------------------------------------------------------------------

def test_idempotenz_second_run_filters_all(tmp_path: Path) -> None:
    """02 §B2: alle IDs geledgert → zweiter Lauf filtert alles,
    „nothing to do"."""
    _write(tmp_path, "A.md",
           _clip("https://www.youtube.com/watch?v=aaaaaaaaaaa", LONG_BODY))
    _write(tmp_path, "B.md",
           _clip("https://www.youtube.com/watch?v=bbbbbbbbbbb",
                 "zu kurz fuer echten inhalt"))
    ledger_path = tmp_path / "ledger.json"

    first = _run(tmp_path, ledger_path=ledger_path)
    assert first["counts"]["usable"] == 1
    assert not first["nothing_to_do"]

    # Simulierter Abschluss: alle kanonischen IDs geledgert (merged/skipped).
    save_ledger({
        "yt:aaaaaaaaaaa": {"status": "merged", "reason": "",
                           "topic_pages": ["tp_x"], "ts": "t"},
        "yt:bbbbbbbbbbb": {"status": "skipped", "reason": "empty_clip",
                           "topic_pages": [], "ts": "t"},
    }, ledger_path)

    second = _run(tmp_path, ledger_path=ledger_path)
    assert second["counts"]["ledgered"] == 2
    assert second["counts"]["usable"] == 0
    assert second["nothing_to_do"]


def test_ledger_reconstruction_from_topicpage(tmp_path: Path) -> None:
    """Selbstheilung: ``sources[].id`` einer Fixture-TopicPage (R9-Muster
    aus S031) → rekonstruiertes Ledger; leeres ``wiki/topics/`` → leer."""
    assert reconstruct_ledger(tmp_path) == {}

    topics = tmp_path / "wiki" / "topics"
    topics.mkdir(parents=True)
    (topics / "tp_health_sauna.md").write_text(
        "---\n"
        "type: TopicPage\n"
        "topic: sauna\n"
        "domain: health\n"
        "mode: claims\n"
        "created: 2026-07-04\n"
        "status: raw\n"
        "sources:\n"
        "  - key: A\n"
        "    id: \"yt:exampleVid1\"\n"
        "    path: \"raw/Wiki/Clippings/Example Source A.md\"\n"
        "  - key: B\n"
        "    id: \"sha1:abc123\"\n"
        "    path: \"raw/Wiki/Clippings/Langbericht.md\"\n"
        "---\n\n# Sauna\n",
        encoding="utf-8")

    entries = reconstruct_ledger(tmp_path)
    assert set(entries) == {"yt:exampleVid1", "sha1:abc123"}
    assert entries["yt:exampleVid1"]["status"] == "merged"
    assert entries["yt:exampleVid1"]["topic_pages"] == [
        "tp_health_sauna"]


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    """DoD 2: Dry-run — kein Ledger-Eintrag, Quell-File byte-identisch."""
    src = _write(tmp_path, "A.md",
                 _clip("https://www.youtube.com/watch?v=aaaaaaaaaaa",
                       "kurz"))
    before = src.read_bytes()
    ledger_path = tmp_path / "ledger.json"

    result = _run(tmp_path, ledger_path=ledger_path)
    assert result["ledger_written"] == []
    assert not ledger_path.exists()
    assert src.read_bytes() == before
    # Plan + Report sind trotzdem da (Build-Artefakte, ENT-054-Pattern).
    assert result["plan_path"].exists()
    assert result["report_path"].exists()


def test_live_requires_backup_branch(tmp_path: Path) -> None:
    """Schritt 3.3: Live ohne ``backup/pre-clippings-batch`` → Abbruch.
    (tmp_path ist kein git-Repo → Branch existiert sicher nicht.)"""
    _write(tmp_path, "A.md",
           _clip("https://www.youtube.com/watch?v=aaaaaaaaaaa", LONG_BODY))
    with pytest.raises(RuntimeError, match="backup/pre-clippings-batch"):
        _run(tmp_path, dry_run=False)


def test_live_ledgers_definitive_skips_only(tmp_path: Path) -> None:
    """Live: empty_clip/near-Dupe werden geledgert; eine Dupe-ID, die der
    Keeper teilt (DupeClip-Fall), wird NIE geledgert — sonst filtert der
    naechste Lauf den Keeper mit."""
    _write(tmp_path, "DupeClip.md",
           _clip("https://www.youtube.com/watch?v=dupeVideo01&t=50s",
                 LONG_BODY, created="2026-06-02"))
    _write(tmp_path, "DupeClip 1.md",
           _clip("https://www.youtube.com/watch?v=dupeVideo01&t=55s",
                 LONG_BODY + " anders", created="2026-06-05"))
    _write(tmp_path, "leer.md",
           _clip("https://www.youtube.com/watch?v=ccccccccccc", "kurz"))
    ledger_path = tmp_path / "ledger.json"

    result = _run(tmp_path, dry_run=False, require_backup_branch=False,
                  ledger_path=ledger_path)
    assert result["ledger_written"] == ["yt:ccccccccccc"]
    ledger = load_ledger(ledger_path)
    assert "yt:dupeVideo01" not in ledger  # Keeper-Schutz

    again = _run(tmp_path, ledger_path=ledger_path)
    recs = _by_name(again)
    assert recs["leer.md"].status == "ledgered"
    assert recs["DupeClip.md"].status == "usable"


def test_plan_json_roundtrip(tmp_path: Path) -> None:
    """Inventory-Plan ist valides JSON mit Zaehlung + Clip-Eintraegen."""
    _write(tmp_path, "A.md",
           _clip("https://www.youtube.com/watch?v=aaaaaaaaaaa", LONG_BODY))
    result = _run(tmp_path)
    plan = json.loads(result["plan_path"].read_text(encoding="utf-8"))
    assert plan["stage"] == 0
    assert plan["counts"]["usable"] == 1
    assert plan["clips"][0]["id"] == "yt:aaaaaaaaaaa"
    assert plan["source_dirs"] == list(SOURCE_DIRS)


def test_ledger_repo_default_is_empty_object() -> None:
    """Liefer-Artefakt 1: das versionierte Ledger existiert ab S032 als
    leeres ``{}`` (Initial-Schnitt, dokumentiert in scripts/ingest/ledger.py)."""
    assert LEDGER_PATH.exists()
    assert load_ledger(LEDGER_PATH) == {}
