"""Provider factory — reads LLM_PROVIDER from .env and returns the
matching implementation. This is the one place that knows which
concrete providers exist; orchestration code only imports get_provider().
"""

from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LLMProvider

settings = get_settings()


@lru_cache
def get_provider() -> LLMProvider:
    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider()
    elif provider == "openai":
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider()
    elif provider == "gemini":
        from app.llm.gemini_provider import GeminiProvider

        return GeminiProvider()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r} (expected 'anthropic', 'openai', or 'gemini')")
