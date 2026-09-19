"""Generates vector embeddings for RAG ingestion and retrieval.

Uses Google's Gemini API (text-embedding-004), which has a genuinely
free tier with no billing/card required, unlike OpenAI's embeddings API.
This is used even though Claude is the chat LLM, since Anthropic does
not offer an embeddings API.

Get a free key at: https://aistudio.google.com/apikey
"""

import time

from google import genai
from google.genai import types

from app.core.config import get_settings

settings = get_settings()

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set in .env. Get a free key at "
                "https://aistudio.google.com/apikey"
            )
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns one vector per input text, in order.

    Gemini's free tier has a request-per-minute limit, so this embeds
    one at a time with a small delay to stay well under it.
    """
    if not texts:
        return []
    client = get_client()

    vectors = []
    for text in texts:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=768,
                task_type="RETRIEVAL_DOCUMENT",
            ),
        )
        vectors.append(response.embeddings[0].values)
        time.sleep(0.5)  # stay comfortably under free-tier rate limits
    return vectors


def embed_query(text: str) -> list[float]:
    """Embed a single search query. Uses RETRIEVAL_QUERY task type, which
    Gemini optimizes differently from RETRIEVAL_DOCUMENT (used for
    ingestion) — this asymmetry improves retrieval quality."""
    client = get_client()
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=768,
            task_type="RETRIEVAL_QUERY",
        ),
    )
    return response.embeddings[0].values


def embed_text(text: str) -> list[float]:
    """Embed a single text string."""
    return embed_texts([text])[0]