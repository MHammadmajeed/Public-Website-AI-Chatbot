"""RAG retrieval service.

Given a user's question, finds the most relevant knowledge_chunk
records via pgvector cosine similarity, applies a confidence
threshold, optionally filters by category/intent, deduplicates
near-identical results, and assembles a deterministic context block
ready to hand to the LLM.

This is deliberately kept separate from the chat route (task 3.1) so
retrieval logic, tuning, and evaluation can evolve independently of
how the chat endpoint uses it.
"""

import re
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.rag.embeddings import embed_query

settings = get_settings()

DEFAULT_TOP_K = 5
DEFAULT_THRESHOLD = 0.55  # cosine similarity, 0-1; tune via evaluation


@dataclass
class RetrievedChunk:
    external_id: str
    title: str | None
    category: str | None
    content: str
    tags: str | None
    intents: str | None
    similarity: float


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk] = field(default_factory=list)
    query_used: str = ""
    has_context: bool = False

    def trace(self) -> list[dict]:
        """Retrieved IDs + scores, for debugging/logging (task 3.9)."""
        return [{"id": c.external_id, "similarity": round(c.similarity, 4)} for c in self.chunks]


def normalize_query(raw_query: str, recent_context: str | None = None) -> str:
    """Normalize the incoming query and fold in only the minimal recent
    conversation context useful for retrieval (task 3.2). We deliberately
    do NOT dump the whole conversation history in here — just enough to
    resolve references like 'that service'."""
    q = " ".join(raw_query.split()).strip()
    if recent_context:
        recent_context = " ".join(recent_context.split()).strip()
        if recent_context:
            q = f"{recent_context} {q}"
    return q


def _dedupe(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Drop near-identical content blocks so they don't waste prompt
    space (task 3.8). Uses a simple normalized-text signature."""
    seen = set()
    result = []
    for c in chunks:
        signature = re.sub(r"\W+", "", c.content.lower())[:200]
        if signature in seen:
            continue
        seen.add(signature)
        result.append(c)
    return result


def retrieve(
    db: Session,
    query: str,
    recent_context: str | None = None,
    top_k: int | None = None,
    threshold: float | None = None,
    category: str | None = None,
    intent: str | None = None,
) -> RetrievalResult:
    """Run similarity search and return a RetrievalResult.

    top_k and threshold default to the configurable settings in .env
    (RETRIEVAL_TOP_K, RETRIEVAL_THRESHOLD) but can be overridden per
    call — kept tunable through evaluation (task 3.4, 3.5).
    """
    top_k = top_k if top_k is not None else settings.retrieval_top_k
    threshold = threshold if threshold is not None else settings.retrieval_threshold

    normalized = normalize_query(query, recent_context)
    query_vector = embed_query(normalized)

    # pgvector's <=> operator returns cosine DISTANCE (0 = identical).
    # We convert to similarity (1 - distance) for readability/threshold.
    where_clauses = []
    pool_size = max(top_k * 2, 10)
    params: dict = {"qvec": str(query_vector), "limit": pool_size}

    if category is not None:
        where_clauses.append("category = :category")
        params["category"] = category
    if intent is not None:
        where_clauses.append("intents ILIKE '%' || :intent || '%'")
        params["intent"] = intent

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    sql = f"""
        SELECT
            external_id, title, category, content, tags, intents,
            1 - (embedding <=> CAST(:qvec AS vector)) AS similarity
        FROM knowledge_chunk
        {where_sql}
        ORDER BY embedding <=> CAST(:qvec AS vector)
        LIMIT :limit
    """

    rows = db.execute(text(sql), params).fetchall()

    candidates = [
        RetrievedChunk(
            external_id=row.external_id,
            title=row.title,
            category=row.category,
            content=row.content,
            tags=row.tags,
            intents=row.intents,
            similarity=float(row.similarity),
        )
        for row in rows
    ]

    above_threshold = [c for c in candidates if c.similarity >= threshold]
    deduped = _dedupe(above_threshold)[:top_k]

    return RetrievalResult(
        chunks=deduped,
        query_used=normalized,
        has_context=len(deduped) > 0,
    )


def build_context(result: RetrievalResult) -> str:
    """Deterministic context formatter (task 3.7). Includes title,
    category, content, and safe metadata — nothing the LLM shouldn't see.
    Returns an empty string when there's no context (low-confidence
    queries must be allowed to produce a no-context result — task 3.5)."""
    if not result.has_context:
        return ""

    blocks = []
    for c in result.chunks:
        tags = f" | tags: {c.tags}" if c.tags else ""
        blocks.append(
            f"[{c.title or 'Untitled'}] (category: {c.category or 'general'}{tags})\n{c.content}"
        )
    return "\n\n---\n\n".join(blocks)