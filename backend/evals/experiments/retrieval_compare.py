from __future__ import annotations

import json
import time
from pathlib import Path

from app.rag.embeddings import embed_query
from app.rag.retrieval import retrieve_chunks
from evals.io import load_cases


REPORT_PATH = (
    Path(__file__).resolve().parent.parent
    / "reports"
    / "retrieval_comparison.json"
)


def source_hit(result: dict, expected_sources: list[dict]) -> bool:
    metadatas = result.get("metadatas", [[]])[0]
    observed = {
        (item.get("document"), item.get("page"))
        for item in metadatas
        if item
    }

    return all(
        (source.get("document"), source.get("page")) in observed
        for source in expected_sources
    )


def evaluate_mode(mode: str, cases: list) -> dict:
    hits = 0
    latencies = []

    for case in cases:
        embedding = embed_query(case.question)

        started = time.perf_counter()
        result = retrieve_chunks(
            question=case.question,
            query_embedding=embedding,
            limit=5,
            mode=mode,
        )
        latencies.append((time.perf_counter() - started) * 1000)

        if source_hit(result, case.expected.get("sources", [])):
            hits += 1

    return {
        "mode": mode,
        "cases": len(cases),
        "source_hit_rate_at_5": hits / len(cases) if cases else 0.0,
        "mean_retrieval_latency_ms": (
            sum(latencies) / len(latencies)
            if latencies
            else 0.0
        ),
    }


def main():
    cases = [
        case
        for case in load_cases()
        if case.mode == "rag"
        and case.expected.get("sources")
    ]

    if not cases:
        raise SystemExit("No RAG source-evaluation cases found.")

    results = [
        evaluate_mode("vector", cases),
        evaluate_mode("hybrid", cases),
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    for result in results:
        print(
            f"{result['mode']}: "
            f"hit@5={result['source_hit_rate_at_5'] * 100:.1f}% "
            f"mean={result['mean_retrieval_latency_ms']:.2f} ms"
        )

    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
