"""RAG knowledge base ingestion pipeline.

Reads the approved JSONL knowledge dataset, validates each record,
normalizes text, generates embeddings, and upserts into PostgreSQL
(knowledge_document + knowledge_chunk) using pgvector.

Re-running this against the same dataset version updates existing
records (matched by their stable external `id`) instead of creating
duplicates.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import KnowledgeChunk, KnowledgeDocument
from app.rag.embeddings import embed_texts

REQUIRED_FIELDS = ["id", "title", "category", "content", "text"]
EMBEDDING_BATCH_SIZE = 50


class ValidationError(Exception):
    pass


@dataclass
class IngestionReport:
    total_records_in_file: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    inserted: int = 0
    updated: int = 0
    invalid_details: list[str] | None = None

    def __post_init__(self):
        if self.invalid_details is None:
            self.invalid_details = []


def load_jsonl(path: str | Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValidationError(f"Line {line_num}: invalid JSON ({e})") from e
    return records


def validate_record(record: dict) -> list[str]:
    """Returns a list of problems with the record. Empty list = valid."""
    problems = []
    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            problems.append(f"missing or empty required field '{field}'")
    if not isinstance(record.get("tags", []), list):
        problems.append("'tags' must be a list")
    if not isinstance(record.get("intents", []), list):
        problems.append("'intents' must be a list")
    return problems


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(value.split())


def get_or_create_document(
    db: Session, source_name: str, version: str, source_uri: str | None = None
) -> KnowledgeDocument:
    existing = db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.source_name == source_name,
            KnowledgeDocument.version == version,
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    doc = KnowledgeDocument(source_name=source_name, version=version, source_uri=source_uri)
    db.add(doc)
    db.flush()
    return doc


def ingest(
    db: Session,
    jsonl_path: str | Path,
    source_name: str = "MoinSystems_AI_Public_Chatbot_RAG_Dataset",
    version: str = "v2",
) -> IngestionReport:
    report = IngestionReport()

    raw_records = load_jsonl(jsonl_path)
    report.total_records_in_file = len(raw_records)

    valid_records = []
    for i, record in enumerate(raw_records):
        problems = validate_record(record)
        if problems:
            report.invalid_records += 1
            report.invalid_details.append(f"record #{i} (id={record.get('id')}): {'; '.join(problems)}")
            continue
        valid_records.append(record)

    report.valid_records = len(valid_records)

    if not valid_records:
        return report

    document = get_or_create_document(db, source_name=source_name, version=version)

    texts_to_embed = [normalize_text(r["text"]) for r in valid_records]

    embeddings: list[list[float]] = []
    for start in range(0, len(texts_to_embed), EMBEDDING_BATCH_SIZE):
        batch = texts_to_embed[start : start + EMBEDDING_BATCH_SIZE]
        embeddings.extend(embed_texts(batch))

    for record, embedding in zip(valid_records, embeddings):
        external_id = str(record["id"])

        existing_chunk = db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.external_id == external_id)
        ).scalar_one_or_none()

        tags = ",".join(record.get("tags", []))
        intents = ",".join(record.get("intents", []))
        content = normalize_text(record["content"])
        title = normalize_text(record["title"])
        category = normalize_text(record["category"])

        if existing_chunk:
            existing_chunk.document_id = document.id
            existing_chunk.title = title
            existing_chunk.content = content
            existing_chunk.embedding = embedding
            existing_chunk.category = category
            existing_chunk.tags = tags
            existing_chunk.intents = intents
            report.updated += 1
        else:
            chunk = KnowledgeChunk(
                external_id=external_id,
                document_id=document.id,
                title=title,
                content=content,
                embedding=embedding,
                category=category,
                tags=tags,
                intents=intents,
            )
            db.add(chunk)
            report.inserted += 1

    db.commit()
    return report