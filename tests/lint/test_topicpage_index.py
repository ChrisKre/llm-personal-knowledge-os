"""BL-14/BL-15: index/reader support for TopicPage + the human-owned family.

R9 mandatory test (brief 031, QM workshop 02): after ``rebuild_index`` a
fixture TopicPage must be (a) visible in ``index.md`` and (b) findable via
``search_wiki(page_type="TopicPage")``. Index support is critical for batch
merges: without it, continuous operation would silently create duplicates.
The test runs against today's real search path (index.md, brief F4; the FTS5
test against a real ``wiki_index.db`` is BL-09 scope / QK-22).

Likewise for the human-owned type family (SCHEMA §3.10, ENT-062): the
``Human-Owned (health)`` section ends the health pages' invisibility in the index.

Fixtures are built per test in ``tmp_path`` (no live wiki access, pattern from
test_index_rebuild.py). Their page content is German, like real vault content.
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
    # Shares the slug token "sauna" with the TopicPage — needed for the
    # page_type filter test below.
    (wiki / "personal" / "health" / "02_protocol_sauna.md").write_text(
        HEALTH_MD, encoding="utf-8")
    return wiki


def test_topicpage_indexed_and_searchable(tmp_path: Path) -> None:
    """R9: fixture TopicPage → rebuild_index → index.md + search_wiki hit."""
    mod = _load_module()
    wiki = _build_wiki(tmp_path)
    result = mod.run(wiki_dir=wiki, index_path=tmp_path / "index.md")

    assert "## TopicPages (1)" in result["rendered"]
    # _summary() contract: "<topic> (<domain>, N Quellen)"
    assert "- [[tp_health_sauna]] — sauna (health, 2 Quellen)" \
        in result["rendered"]

    hits = search_wiki("sauna", page_type="TopicPage", wiki_root=tmp_path)
    assert len(hits) == 1
    assert hits[0].page_type == "TopicPage"
    assert hits[0].path == "wiki/topics/tp_health_sauna.md"
    assert (tmp_path / hits[0].path).exists()  # _ref_to_path points to a real file


def test_health_pages_indexed_and_searchable(tmp_path: Path) -> None:
    """ENT-062 point 3: the Human-Owned section makes health pages visible in the index."""
    mod = _load_module()
    wiki = _build_wiki(tmp_path)
    result = mod.run(wiki_dir=wiki, index_path=tmp_path / "index.md")

    assert "## Human-Owned (health) (1)" in result["rendered"]
    assert "- [[02_protocol_sauna]]" in result["rendered"]

    hits = search_wiki("protocol sauna", wiki_root=tmp_path)
    paths = {h.path for h in hits}
    assert "wiki/personal/health/02_protocol_sauna.md" in paths


def test_type_filter_separates_sections(tmp_path: Path) -> None:
    """The page_type filter separates TopicPage from human-owned hits."""
    mod = _load_module()
    wiki = _build_wiki(tmp_path)
    mod.run(wiki_dir=wiki, index_path=tmp_path / "index.md")

    # "sauna" is a slug token of both pages — the filter must separate them.
    tp_hits = search_wiki("sauna", page_type="TopicPage", wiki_root=tmp_path)
    assert {h.path for h in tp_hits} == {"wiki/topics/tp_health_sauna.md"}
    ho_hits = search_wiki("sauna", page_type="HumanOwned", wiki_root=tmp_path)
    assert {h.path for h in ho_hits} == {
        "wiki/personal/health/02_protocol_sauna.md"}
