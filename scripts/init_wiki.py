"""scripts/init_wiki.py — first-run setup for the LLM-Personal-Knowledge-OS.

Creates all directories and files in the vault that bot.py and main_workflow.py
need to start without errors. The generated templates are German (vault content).

Usage: python scripts/init_wiki.py
       python scripts/init_wiki.py --force   # overwrites existing files
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / ".env")  # before agents.config (KOS_VAULT_ROOT)

from agents.config import VAULT_ROOT  # noqa: E402

TODAY = date.today().isoformat()

# Directories that must exist
REQUIRED_DIRS = [
    "wiki/personal/facts",
    "wiki/personal/stories",
    "wiki/personal/style_refs",
    "wiki/language/vocab",
    "wiki/language/grammar",
    "wiki/language/culture",
    "wiki/language/bridges",
    "wiki/concepts",
    "raw/events",
    "raw/sources",
    "raw/assets",
    "raw/style_refs",
    "scripts",
]

INDEX_MD_TEMPLATE = f"""\
# Index — LLM-Personal-Knowledge-OS
> Aktualisiert: {TODAY} | Automatisch gepflegt vom System

---

## PersonalFacts (0)

## VocabEntries — ES (0)

## VocabEntries — EN (0)

## CulturalEntries (0)

## LanguageBridges (0)

## Concepts (0)

## StyleProfiles (0)
"""

LOG_MD_TEMPLATE = f"""\
# Operationslog — LLM-Personal-Knowledge-OS
> Append-only. Format: ## [TIMESTAMP] operation | Beschreibung

---

## [{TODAY}T00:00:00] init | Erstes Setup via scripts/init_wiki.py
"""

USER_PROFILE_TEMPLATE = f"""\
---
created: {TODAY}
updated: {TODAY}
---

# Nutzer-Profil

## Sprachprofil
- Primärsprache: de
- Aktive Zielsprachen: [es, en]
- Input-Verteilung (30 Tage): de: 100%, es: 0%, en: 0%
- Input-Verteilung (90 Tage): de: 100%, es: 0%, en: 0%

## Interessen-Cluster
- KI/Tech (hoch) — [Basis: 0 Seiten]
- Gesundheit (mittel) — [Basis: 0 Seiten]
- Musik (mittel) — [Basis: 0 Seiten]
- Fotografie (mittel) — [Basis: 0 Seiten]
- Esport/CS2 (mittel) — [Basis: 0 Seiten]
- Krypto (mittel) — [Basis: 0 Seiten]

## Personal-Facts-Profil
- Gesamt: 0 PersonalFacts
- story_score Durchschnitt: 0.0
- High-Score Facts (≥7) ungeübt: 0
- Zuletzt elaboriert: —

## Bootstrap
bootstrap_progress: 0/10
bootstrap_complete: false
bootstrap_started: {TODAY}

## Style
active_style_profile: null

## Schwellwerte (System-Defaults, überschreibbar)
concept_threshold: 3
story_score_elaborate_threshold: 6
story_score_review_required: 7
stale_raw_days: 7
"""

USER_LANGUAGE_PROFILE_TEMPLATE = f"""\
---
created: {TODAY}
updated: {TODAY}
---

# Sprachprofil

## Aktive Sprachen
| Sprache | Code | Status | Einträge | Letzte Aktivität |
|---------|------|--------|----------|-----------------|
| Deutsch | de | Muttersprache | — | — |
| Spanisch | es | aktiv lernend | 0 | — |
| Englisch | en | aktiv lernend | 0 | — |

## Input-Verteilung (letzte 30 Tage)
- de: 100%
- es: 0%
- en: 0%

## Input-Verteilung (letzte 90 Tage)
- de: 100%
- es: 0%
- en: 0%

## Ziel-Konfiguration
primary_learning_language: es
secondary_learning_language: en
anki_deck_es: "Personal :: Spanisch :: Vokabeln"
anki_deck_en: "Personal :: Englisch :: Vokabeln"
daily_push_language: es

## Schwellwerte
vocab_recommend_min_score: elaborated
bridge_auto_create: true
cultural_entry_auto: true

## Anki-Status
anki_last_sync: —
anki_entries_es: 0
anki_entries_en: 0
anki_streak_current: 0
anki_streak_best: 0

## Statistik
total_vocab_entries: 0
bridges_created: 0
cultural_entries: 0
concept_entries: 0
"""


def create_dirs(repo_root: Path) -> None:
    for rel in REQUIRED_DIRS:
        d = repo_root / rel
        d.mkdir(parents=True, exist_ok=True)
        # .gitkeep so Git tracks empty dirs
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()


def create_file(path: Path, content: str, force: bool, root: Path = VAULT_ROOT) -> bool:
    """Create file if it doesn't exist (or force=True). Returns True if written."""
    if path.exists() and not force:
        print(f"  SKIP  {path.relative_to(root)}  (already exists, use --force to overwrite)")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  OK    {path.relative_to(root)}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="First-run setup for the LLM-Personal-Knowledge-OS")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--root", type=Path, default=VAULT_ROOT, help="Vault root (default: KOS_VAULT_ROOT, else sample_vault/)")
    args = parser.parse_args()

    root: Path = args.root.resolve()
    force: bool = args.force

    print(f"\nLLM-Personal-Knowledge-OS — First-Run-Setup")
    print(f"Vault root: {root}\n")

    print("1. Creating directories...")
    create_dirs(root)
    print(f"   {len(REQUIRED_DIRS)} directories ready.\n")

    print("2. Creating system files...")
    create_file(root / "index.md",                                 INDEX_MD_TEMPLATE,                 force, root)
    create_file(root / "log.md",                                   LOG_MD_TEMPLATE,                   force, root)
    create_file(root / "user_profile.md",                          USER_PROFILE_TEMPLATE,             force, root)
    create_file(root / "wiki/language/user_language_profile.md",   USER_LANGUAGE_PROFILE_TEMPLATE,    force, root)

    print("\nSetup complete.")
    print("\nNext steps:")
    print("  1. Create .env from .env.example (TELEGRAM_BOT_TOKEN, optionally ANTHROPIC_API_KEY)")
    print("  2. Ingest test: python scripts/test_ingest.py \"...\"")
    print("  3. Start the bot: python bot.py\n")


if __name__ == "__main__":
    main()
