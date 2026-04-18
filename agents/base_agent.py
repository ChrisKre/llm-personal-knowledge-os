"""base_agent.py — Abstract base for all Knowledge-OS agents.

Provider selection (automatic, no code changes needed):
  ANTHROPIC_API_KEY set   →  Claude Haiku 4.5 / Sonnet 4.6  (Produktion)
  ANTHROPIC_API_KEY unset →  Ollama lokal (beide Rollen, für Tests)

Ollama-Konfiguration via Umgebungsvariablen:
  OLLAMA_HOST   (default: http://localhost:11434)
  OLLAMA_MODEL  (default: llama3.2)
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

_OLLAMA_BASE  = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

_CLAUDE_HAIKU  = "claude-haiku-4-5-20251001"
_CLAUDE_SONNET = "claude-sonnet-4-6"
_DEFAULT_SYSTEM = "You are a precise assistant. Answer exactly as instructed."


class BaseAgent(ABC):
    """Abstract base class for all Knowledge-OS agents.

    Contract: every agent receives a state dict and returns an updated state dict.
    Agents never write files directly — they return WikiWrite objects in state["wiki_writes"].
    """

    def __init__(self, wiki_root: Path, anthropic_client: Any = None):
        self.wiki_root = wiki_root
        self.client = anthropic_client
        self._provider = "claude" if anthropic_client is not None else "ollama"
        if self._provider == "ollama":
            logger.info(
                "%s: kein Anthropic-Client — Ollama-Fallback aktiv (Modell: %s)",
                self.__class__.__name__,
                _OLLAMA_MODEL,
            )

    @abstractmethod
    def process(self, state: dict) -> dict:
        """Main entry point called by LangGraph as a node.

        Args:
            state: SupervisorState or agent-specific state dict.

        Returns:
            Updated state dict. Must include "wiki_writes" key (may be empty list).
        """
        ...

    def _haiku(self, prompt: str, system: str = "") -> str:
        """Cheap classification and template tasks.
        Claude Haiku in production, Ollama fallback for testing.
        """
        if self._provider == "claude":
            return self._call_claude(_CLAUDE_HAIKU, prompt, system, max_tokens=1024)
        return self._call_ollama(prompt, system)

    def _sonnet(self, prompt: str, system: str = "") -> str:
        """Synthesis, creative writing, nuanced reasoning.
        Claude Sonnet in production, Ollama fallback for testing.
        """
        if self._provider == "claude":
            return self._call_claude(_CLAUDE_SONNET, prompt, system, max_tokens=4096)
        return self._call_ollama(prompt, system)

    # ------------------------------------------------------------------
    # Internal provider implementations
    # ------------------------------------------------------------------

    def _call_claude(self, model: str, prompt: str, system: str, max_tokens: int) -> str:
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system or _DEFAULT_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _call_ollama(self, prompt: str, system: str) -> str:
        """Call local Ollama via HTTP. Raises RuntimeError if Ollama is unreachable."""
        payload = {
            "model": _OLLAMA_MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": system or _DEFAULT_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
        }
        try:
            resp = requests.post(
                f"{_OLLAMA_BASE}/api/chat",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Ollama nicht erreichbar unter {_OLLAMA_BASE}. "
                "Starte Ollama mit: ollama serve"
            ) from None
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"Ollama HTTP-Fehler: {e}. "
                f"Modell '{_OLLAMA_MODEL}' vorhanden? Prüfe mit: ollama list"
            ) from e
