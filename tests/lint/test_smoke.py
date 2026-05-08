"""Smoke-Test: lint_agent ist importierbar."""


def test_lint_agent_imports():
    from agents import lint_agent  # noqa: F401
