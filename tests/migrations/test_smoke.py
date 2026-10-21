"""Smoke test: pyyaml is available (prerequisite for every frontmatter migration)."""


def test_yaml_available():
    import yaml

    sample = yaml.safe_load("type: VocabEntry\nword: test\n")
    assert sample == {"type": "VocabEntry", "word": "test"}
