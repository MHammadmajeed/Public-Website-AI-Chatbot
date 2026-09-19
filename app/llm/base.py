"""LLM provider abstraction (task 4.1).

The chat orchestrator only ever talks to this interface, never to a
specific SDK. Switching providers is a one-line config change
(LLM_PROVIDER in .env) — no orchestration code changes needed.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMMessage:
    role: str  # "user" | "assistant"
    content: str


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        messages: list[LLMMessage],
        max_tokens: int = 600,
        temperature: float = 0.3,
    ) -> str:
        """Generate a single assistant reply given a system prompt and
        conversation history. Returns plain text."""
        raise NotImplementedError

class LLMUnavailableError(Exception):
    pass