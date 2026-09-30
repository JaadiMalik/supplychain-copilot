from __future__ import annotations

import math
import os
import re
from collections import Counter

from app.rag.vector_store import (
    get_all_chunks,
    search_chunks,
)


TOKEN_RE = re.compile(r"[a-zA-Z0-9_%.-]+")


def tokenize(text: str) -> list[str]:
    return [
        token.casefold()
        for token in TOKEN_RE.findall(text or "")
        if len(token) > 1
    ]


def _bm25_scores(
    query: str,
    ids: list[str],
    documents: list[str],
) -> dict[str, float]:
    query_terms = tokenize(query)
    tokenized_docs = [tokenize(doc) for doc in documents]

    if not query_terms or not tokenized_docs:
        return {doc_id: 0.0 for doc_id in ids}

    n_docs = len(tokenized_docs)
    avgdl = (
        sum(len(tokens) for tokens in tokenized_docs) / n_docs
        if n_docs
        else 1.0
    )

    doc_frequency = Counter()
    for tokens in tokenized_docs:
        for term in set(tokens):
            doc_frequency[term] += 1

    k1 = 1.5
    b = 0.75
    scores = {}

    for doc_id, tokens in zip(ids, tokenized_docs):
        counts = Counter(tokens)
        dl = len(tokens) or 1
        score = 0.0

        for term in query_terms:
            tf = counts.get(term, 0)
            if tf == 0:
                continue

            df = doc_frequency.get(term, 0)
            idf = math.log(
                1.0
                + (n_docs - df + 0.5) / (df + 0.5)
            )

            numerator = tf * (k1 + 1.0)
            denominator = tf + k1 * (
                1.0 - b + b * dl / max(avgdl, 1.0)
            )

            score += idf * numerator / denominator

        scores[doc_id] = score

    return scores


def _normalize_vector_result(result: dict) -> list[dict]:
    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    rows = []

    for index, chunk_id in enumerate(ids):
        rows.append(
            {
                "id": chunk_id,
                "document": documents[index],
                "metadata": metadatas[index] or {},
                "distance": (
                    distances[index]
                    if index < len(distances)
                    else None
                ),
            }
        )

    return rows


def retrieve_chunks(
    question: str,
    query_embedding: list[float],
    limit: int = 5,
    metadata_filter: dict | None = None,
    mode: str | None = None,
) -> dict:
    mode = (
        mode
        or os.getenv("RAG_RETRIEVAL_MODE", "hybrid")
    ).strip().casefold()

    if mode not in {"vector", "hybrid"}:
        raise ValueError(
            "RAG_RETRIEVAL_MODE must be 'vector' or 'hybrid'."
        )

    vector_result = search_chunks(
        query_embedding,
        limit=max(limit * 3, 10),
        where=metadata_filter,
    )
    vector_rows = _normalize_vector_result(vector_result)

    if mode == "vector":
        selected = vector_rows[:limit]
        return {
            "ids": [[row["id"] for row in selected]],
            "documents": [[row["document"] for row in selected]],
            "metadatas": [[row["metadata"] for row in selected]],
            "distances": [[row["distance"] for row in selected]],
            "scores": [[
                {
                    "vector_rank": index + 1,
                    "lexical_score": None,
                    "rrf_score": None,
                }
                for index, _ in enumerate(selected)
            ]],
            "debug": {
                "mode": "vector",
                "filter": metadata_filter or {},
                "candidate_count": len(vector_rows),
            },
        }

    all_records = get_all_chunks(where=metadata_filter)
    all_ids = all_records.get("ids", [])
    all_documents = all_records.get("documents", [])
    all_metadatas = all_records.get("metadatas", [])

    lexical_scores = _bm25_scores(
        question,
        all_ids,
        all_documents,
    )

    lexical_ranked = sorted(
        all_ids,
        key=lambda chunk_id: lexical_scores.get(chunk_id, 0.0),
        reverse=True,
    )

    vector_rank = {
        row["id"]: index + 1
        for index, row in enumerate(vector_rows)
    }
    lexical_rank = {
        chunk_id: index + 1
        for index, chunk_id in enumerate(lexical_ranked)
    }

    doc_map = {
        chunk_id: {
            "id": chunk_id,
            "document": document,
            "metadata": metadata or {},
            "distance": None,
        }
        for chunk_id, document, metadata
        in zip(all_ids, all_documents, all_metadatas)
    }

    for row in vector_rows:
        doc_map.setdefault(row["id"], row)
        doc_map[row["id"]]["distance"] = row["distance"]

    k = 60.0
    combined = []

    for chunk_id, row in doc_map.items():
        vrank = vector_rank.get(chunk_id)
        lrank = lexical_rank.get(chunk_id)

        score = 0.0

        if vrank is not None:
            score += 1.0 / (k + vrank)

        if lrank is not None and lexical_scores.get(chunk_id, 0.0) > 0:
            score += 1.0 / (k + lrank)

        if score <= 0:
            continue

        combined.append(
            {
                **row,
                "vector_rank": vrank,
                "lexical_rank": lrank,
                "lexical_score": lexical_scores.get(chunk_id, 0.0),
                "rrf_score": score,
            }
        )

    combined.sort(
        key=lambda row: row["rrf_score"],
        reverse=True,
    )
    selected = combined[:limit]

    return {
        "ids": [[row["id"] for row in selected]],
        "documents": [[row["document"] for row in selected]],
        "metadatas": [[row["metadata"] for row in selected]],
        "distances": [[row["distance"] for row in selected]],
        "scores": [[
            {
                "vector_rank": row["vector_rank"],
                "lexical_rank": row["lexical_rank"],
                "lexical_score": round(row["lexical_score"], 6),
                "rrf_score": round(row["rrf_score"], 8),
            }
            for row in selected
        ]],
        "debug": {
            "mode": "hybrid",
            "filter": metadata_filter or {},
            "candidate_count": len(combined),
        },
    }
