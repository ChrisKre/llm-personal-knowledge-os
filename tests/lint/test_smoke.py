"""Smoke test: lint_agent is importable."""


def test_lint_agent_imports():
    from agents import lint_agent  # noqa: F401
