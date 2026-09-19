"""Quick diagnostic: shows company_001's exact similarity score and rank
for the EVAL-001 query, even when it falls outside the top 5.

Usage:
    python scripts/diagnose_retrieval.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal  # noqa: E402
from app.rag.retriever import retrieve  # noqa: E402


def main():
    db = SessionLocal()
    try:
        result = retrieve(
            db,
            query="What does MoinSystems AI do?",
            top_k=20,  # wide enough to definitely include company_001
            threshold=0.0,
        )
        print("Full ranked list for: 'What does MoinSystems AI do?'\n")
        for i, c in enumerate(result.chunks, start=1):
            marker = "  <-- expected answer" if c.external_id == "company_001" else ""
            print(f"{i:2d}. {c.external_id:25s} similarity={c.similarity:.4f}{marker}")
    finally:
        db.close()


if __name__ == "__main__":
    main()