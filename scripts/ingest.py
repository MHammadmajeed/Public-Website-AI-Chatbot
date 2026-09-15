"""Command-line entrypoint for running RAG knowledge base ingestion.

Usage:
    python scripts/ingest.py
    python scripts/ingest.py --file data/MoinSystems_AI_Public_Chatbot_RAG_Dataset_v2.jsonl
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal  # noqa: E402
from app.rag.ingestion import ingest  # noqa: E402

DEFAULT_FILE = "data/MoinSystems_AI_Public_Chatbot_RAG_Dataset_v2.jsonl"


def main():
    parser = argparse.ArgumentParser(description="Ingest the RAG knowledge base JSONL into PostgreSQL.")
    parser.add_argument("--file", default=DEFAULT_FILE, help="Path to the JSONL dataset file")
    parser.add_argument("--version", default="v2", help="Dataset version label")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print(f"Loading: {args.file}")
        report = ingest(db, jsonl_path=args.file, version=args.version)

        print("\n--- Ingestion Report ---")
        print(f"Records in file:   {report.total_records_in_file}")
        print(f"Valid records:     {report.valid_records}")
        print(f"Invalid records:   {report.invalid_records}")
        print(f"Inserted (new):    {report.inserted}")
        print(f"Updated (existing):{report.updated}")

        if report.invalid_details:
            print("\nInvalid record details:")
            for detail in report.invalid_details:
                print(f"  - {detail}")

        if report.invalid_records > 0:
            sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()