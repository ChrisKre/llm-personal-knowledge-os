"""Pin the test suite to the bundled sample vault.

Runs before any test module imports ``agents.config``. The value is forced (not
a default) so that a ``KOS_VAULT_ROOT`` from the shell or ``.env`` can never
point tests at a private vault; ``load_dotenv`` does not override it.
"""
import os
from pathlib import Path

os.environ["KOS_VAULT_ROOT"] = str(Path(__file__).resolve().parent.parent / "sample_vault")
