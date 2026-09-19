"""OpenAI provider (alternate to Claude — switch via LLM_PROVIDER in .env).

Not the active provider for this project (Claude is), but implemented so
the provider abstraction is genuinely swappable, not just theoretical.
"""

from openai import OpenAI

from app.core.config import get_settings
from app.llm.base import LLMMessage, LLMProvider

settings = get_settings()

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str = DEFAULT_MODEL):
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in .env")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model

    def generate(
        self,
        system_prompt: str,
        messages: list[LLMMessage],
        max_tokens: int = 600,
        temperature: float = 0.3,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "system", "content": system_prompt}]
            + [{"role": m.role, "content": m.content} for m in messages],
        )
        return (response.choices[0].message.content or "").strip()
