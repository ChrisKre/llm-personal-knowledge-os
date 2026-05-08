"""Smoke-Test: pyyaml verfügbar (Pre-Req für jede Frontmatter-Migration)."""


def test_yaml_available():
    import yaml

    sample = yaml.safe_load("type: VocabEntry\nword: test\n")
    assert sample == {"type": "VocabEntry", "word": "test"}
