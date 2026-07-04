"""BL-14/BL-15: Index-/Reader-Aufnahme von TopicPage + human-owned Familie.

R9-Pflichttest (Brief 031, QM Workshop-02): eine Fixture-TopicPage muss nach
``rebuild_index`` (a) in ``index.md`` sichtbar und (b) via
``search_wiki(page_type="TopicPage")`` auffindbar sein — die Index-Aufnahme
ist Batch-Merge-kritisch: ohne sie legt der laufende Betrieb stumm Duplikate
an. Der Test laeuft gegen den heutigen realen Such-Pfad (index.md, Brief F4;
der FTS5-Test gegen echte ``wiki_index.db`` ist BL-09-Scope/QK-22).

Analog fuer die human-owned Typen-Familie (SCHEMA §3.10, ENT-062): Sektion
``Human-Owned (health)`` beendet die Index-Blindheit der Health-Seiten.

Fixtures werden pro Test in ``tmp_path`` gebaut (kein Live-Wiki-Zugriff,
Muster aus test_index_rebuild.py).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from agents.graph_reader import search_wiki

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_FILE = REPO_ROOT / "scripts" / "rebuild_index.py"

TOPICPAGE_MD = """---
type: TopicPage
topic: sauna
domain: health
mode: claims
created: 2026-07-04
updated: 2026-07-04
status: raw
tags: []
sensitivity: sensitive
sources:
  - key: A
    id: "yt:exampleVid1"
    path: "raw/Wiki/Clippings/Example Source A.md"
    author: "Dr. Jane Doe"
    tier: 3
  - key: B
    id: "yt:abc123def45"
    path: "raw/Wiki/Clippings/Example Source B.md"
    author: "Dr. John Roe"
    tier: 2
related: []
---

# Sauna

> Aggregiertes Fremdwissen, keine medizinische Beratung. Quellen-Tier ≠ ärztliche Empfehlung.

## Konsens
- **Claim:** Sauna verbessert die Regeneration. | **Quellen:** [A 6:05], [B 3:06] | **Konfidenz:** hoch (2 Autoren, tier 2+3)
"""

HEALTH_MD = """---
type: HealthProtocol
created: 2026-06-01
updated: 2026-06-01
status: active
owner: human
tags: [recovery, protocol]
---

# Gesundheits-Protokoll
"""


def _load_module():
    spec = importlib.util.spec_from_file_location("rebuild_index", SCRIPT_FILE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _build_wiki(tmp_path: Path) -> Path:
    wiki = tmp_path / "wiki"
    (wiki / "topics").mkdir(parents=True)
    (wiki / "topics" / "tp_health_sauna.md").write_text(
        TOPICPAGE_MD, encoding="utf-8")
    (wiki / "personal" / "health").mkdir(parents=True)
    # Teilt das Slug-Token "sauna" mit der TopicPage — noetig fuer
    # den page_type-Filter-Test unten.
    (wiki / "personal" / "health" / "02_protocol_sauna.md").write_text(
        HEALTH_MD, encoding="utf-8")
    return wiki


def test_topicpage_indexed_and_searchable(tmp_path: Path) -> None:
    """R9: Fixture-TopicPage → rebuild_index → index.md + search_wiki-Treffer."""
    mod = _load_module()
    wiki = _build_wiki(tmp_path)
    result = mod.run(wiki_dir=wiki, index_path=tmp_path / "index.md")

    assert "## TopicPages (1)" in result["rendered"]
    # _summary()-Vertrag: "<topic> (<domain>, N Quellen)"
    assert "- [[tp_health_sauna]] — sauna (health, 2 Quellen)" \
        in result["rendered"]

    hits = search_wiki("sauna", page_type="TopicPage", wiki_root=tmp_path)
    assert len(hits) == 1
    assert hits[0].page_type == "TopicPage"
    assert hits[0].path == "wiki/topics/tp_health_sauna.md"
    assert (tmp_path / hits[0].path).exists()  # _ref_to_path zeigt auf echtes File


def test_health_pages_indexed_and_searchable(tmp_path: Path) -> None:
    """ENT-062 Punkt 3: Human-Owned-Sektion beendet die Index-Blindheit."""
    mod = _load_module()
    wiki = _build_wiki(tmp_path)
    result = mod.run(wiki_dir=wiki, index_path=tmp_path / "index.md")

    assert "## Human-Owned (health) (1)" in result["rendered"]
    assert "- [[02_protocol_sauna]]" in result["rendered"]

    hits = search_wiki("protocol sauna", wiki_root=tmp_path)
    paths = {h.path for h in hits}
    assert "wiki/personal/health/02_protocol_sauna.md" in paths


def test_type_filter_separates_sections(tmp_path: Path) -> None:
    """page_type-Filter trennt TopicPage von human-owned Treffern."""
    mod = _load_module()
    wiki = _build_wiki(tmp_path)
    mod.run(wiki_dir=wiki, index_path=tmp_path / "index.md")

    # "sauna" ist Slug-Token beider Seiten — der Filter muss trennen.
    tp_hits = search_wiki("sauna", page_type="TopicPage", wiki_root=tmp_path)
    assert {h.path for h in tp_hits} == {"wiki/topics/tp_health_sauna.md"}
    ho_hits = search_wiki("sauna", page_type="HumanOwned", wiki_root=tmp_path)
    assert {h.path for h in ho_hits} == {
        "wiki/personal/health/02_protocol_sauna.md"}
