"""Anthropic Claude provider."""

from anthropic import Anthropic

from app.core.config import get_settings
from app.llm.base import LLMMessage, LLMProvider

settings = get_settings()

# Claude Haiku 4.5: fastest and most cost-effective current model, a good
# fit for a website support chatbot's short grounded answers.
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str = DEFAULT_MODEL):
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set in .env")
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = model

    def generate(
        self,
        system_prompt: str,
        messages: list[LLMMessage],
        max_tokens: int = 600,
        temperature: float = 0.3,
    ) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        # Concatenate all text blocks (there is normally exactly one).
        return "".join(block.text for block in response.content if block.type == "text").strip()
