"""Central configuration: where the knowledge vault lives.

The vault holds all user data (``wiki/``, ``raw/``, ``index.md``, ``log.md``,
``user_profile.md``, ``wiki_index.db``). It is resolved once at import time from
``KOS_VAULT_ROOT``; without it, the fictional ``sample_vault/`` shipped with the
repo is used. Entry points (``bot.py``, ``main_workflow.py``, ``scripts/*.py``)
load ``.env`` before importing this module, so a value set there is honoured.
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_ROOT = Path(os.environ.get("KOS_VAULT_ROOT") or REPO_ROOT / "sample_vault").resolve()
