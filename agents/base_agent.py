from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path


class BaseAgent(ABC):
    """Abstract base class for all Knowledge-OS agents.

    Contract: every agent receives a state dict and returns an updated state dict.
    Agents never write files directly — they return WikiWrite objects in state["wiki_writes"].
    """

    def __init__(self, wiki_root: Path, anthropic_client: Any):
        self.wiki_root = wiki_root
        self.client = anthropic_client

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
        """Call Claude Haiku — cheap classification and template tasks."""
        messages = [{"role": "user", "content": prompt}]
        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system or "You are a precise assistant. Answer exactly as instructed.",
            messages=messages,
        )
        return response.content[0].text

    def _sonnet(self, prompt: str, system: str = "") -> str:
        """Call Claude Sonnet — synthesis, creative writing, nuanced reasoning."""
        messages = [{"role": "user", "content": prompt}]
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system or "You are a precise assistant. Answer exactly as instructed.",
            messages=messages,
        )
        return response.content[0].text
