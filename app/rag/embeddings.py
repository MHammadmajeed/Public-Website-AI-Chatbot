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
        time.sleep(0.5)
    return vectors


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]