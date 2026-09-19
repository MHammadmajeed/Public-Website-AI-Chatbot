"""Gemini chat provider (free tier, no card required).

Uses the same GEMINI_API_KEY already set up for embeddings - no new
account or payment needed.
"""
import time

from google import genai
from google.genai import errors as genai_errors

from app.core.config import get_settings
from app.llm.base import LLMMessage, LLMProvider, LLMUnavailableError

settings = get_settings()

DEFAULT_MODEL = "gemini-3.8-flash"
RETRY_DELAYS = [2, 5, 10]  # seconds to wait before retry 1, 2, 3


class GeminiProvider(LLMProvider):
    def __init__(self, model: str = DEFAULT_MODEL):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in .env")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = model

    def generate(
        self,
        system_prompt: str,
        messages: list[LLMMessage],
        max_tokens: int = 600,
        temperature: float = 0.3,
    ) -> str:
        """Call Gemini. Retry on 5xx (busy). Fail fast on 429 (quota)."""
        last_error = None
        for attempt in range(len(RETRY_DELAYS) + 1):
            try:
                return self._call(system_prompt, messages, max_tokens, temperature)
            except genai_errors.ServerError as e:
                last_error = e
                if attempt < len(RETRY_DELAYS):
                    delay = RETRY_DELAYS[attempt]
                    print(f"Gemini busy, retrying in {delay}s...")
                    time.sleep(delay)
            except genai_errors.ClientError as e:
                if getattr(e, "code", None) == 429:
                    raise LLMUnavailableError("Gemini quota exhausted (429)") from e
                raise
        raise LLMUnavailableError(str(last_error))

    def _call(
        self,
        system_prompt: str,
        messages: list[LLMMessage],
        max_tokens: int = 600,
        temperature: float = 0.3,
    ) -> str:
        # Map roles directly: user -> user, assistant -> model.
        contents = [
            {"role": "user" if m.role == "user" else "model", "parts": [{"text": m.content}]}
            for m in messages
        ]

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config={
                "system_instruction": system_prompt,
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        return (response.text or "").strip()