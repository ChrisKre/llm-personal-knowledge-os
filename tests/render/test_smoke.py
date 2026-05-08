"""Smoke-Test: Anki-Export-Modul ist importierbar."""


def test_export_anki_imports():
    import importlib.util
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "export_anki", repo_root / "scripts" / "export_anki.py"
    )
    assert spec is not None
