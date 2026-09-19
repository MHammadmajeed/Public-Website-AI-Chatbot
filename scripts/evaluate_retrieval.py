"""Retrieval evaluation script (task 3.10).

Runs the supplied evaluation set (data/rag_evaluation_set.json) against
the retriever and reports top-3/top-5 hit rates: for each query, did
the expected record appear within the top 3 (or top 5) results?

Usage:
    python scripts/evaluate_retrieval.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal  # noqa: E402
from app.rag.retriever import retrieve  # noqa: E402

EVAL_FILE = "data/rag_evaluation_set.json"
# Evaluation uses a wider top_k and low threshold so we can see full
# ranking behavior, independent of the production defaults.
EVAL_TOP_K = 5
EVAL_THRESHOLD = 0.0


def main():
    with open(EVAL_FILE, encoding="utf-8") as f:
        eval_cases = json.load(f)

    db = SessionLocal()
    top3_hits = 0
    top5_hits = 0
    failures = []

    try:
        for case in eval_cases:
            result = retrieve(
                db,
                query=case["query"],
                top_k=EVAL_TOP_K,
                threshold=EVAL_THRESHOLD,
            )
            retrieved_ids = [c.external_id for c in result.chunks]
            expected = case["expected_record"]

            in_top3 = expected in retrieved_ids[:3]
            in_top5 = expected in retrieved_ids[:5]

            if in_top3:
                top3_hits += 1
            if in_top5:
                top5_hits += 1

            if not in_top5:
                failures.append(
                    {
                        "id": case["id"],
                        "query": case["query"],
                        "expected": expected,
                        "got": result.trace(),
                    }
                )

        total = len(eval_cases)
        print("--- Retrieval Evaluation Report ---")
        print(f"Total queries:        {total}")
        print(f"Top-3 accuracy:       {top3_hits}/{total} ({100 * top3_hits / total:.1f}%)")
        print(f"Top-5 accuracy:       {top5_hits}/{total} ({100 * top5_hits / total:.1f}%)")

        if failures:
            print(f"\nFailures (expected record not in top 5) — {len(failures)}:")
            for f in failures:
                print(f"\n  {f['id']}: \"{f['query']}\"")
                print(f"    expected: {f['expected']}")
                print(f"    got:      {f['got']}")
        else:
            print("\nNo failures — every expected record appeared in the top 5.")
    finally:
        db.close()


if __name__ == "__main__":
    main()