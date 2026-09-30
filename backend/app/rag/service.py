import json

from app.agent.llm import call_qwen_text
from app.rag.embeddings import embed_query
from app.rag.retrieval import retrieve_chunks


def select_best_sources(
    question: str,
    documents: list,
    metadatas: list,
) -> list[int]:
    evidence_parts = []

    for i, text in enumerate(documents, start=1):
        metadata = metadatas[i - 1] or {}
        evidence_parts.append(
            f"""
SOURCE {i}
Document: {metadata.get("document")}
Page: {metadata.get("page")}
Supplier: {metadata.get("supplier")}
Contract ID: {metadata.get("contract_id")}
Clause type: {metadata.get("clause_type")}

{text}
"""
        )

    prompt = f"""
You are selecting evidence for a supply-chain RAG system.

QUESTION:
{question}

EVIDENCE:
{"".join(evidence_parts)}

Rules:
1. Select only direct evidence.
2. Prefer original contract clauses.
3. Supplier-specific questions require matching supplier metadata.
4. Never transfer evidence between suppliers.
5. Return JSON only:
{{"source_numbers": [1]}}
"""

    output = call_qwen_text(prompt, max_tokens=100)
    output = output.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(output)
    except json.JSONDecodeError:
        return []

    return [
        number
        for number in result.get("source_numbers", [])
        if isinstance(number, int) and 1 <= number <= len(documents)
    ]


def ask_rag(
    question: str,
    metadata_filter: dict | None = None,
    retrieval_mode: str | None = None,
) -> dict:
    query_embedding = embed_query(question)

    results = retrieve_chunks(
        question=question,
        query_embedding=query_embedding,
        limit=5,
        metadata_filter=metadata_filter,
        mode=retrieval_mode,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    scores = results.get("scores", [[]])[0]

    if not documents:
        return {
            "answer": "I could not find enough evidence in the document.",
            "sources": [],
            "retrieval": results.get("debug", {}),
        }

    selected_numbers = select_best_sources(
        question,
        documents,
        metadatas,
    )

    if not selected_numbers:
        return {
            "answer": "I could not find enough evidence in the document.",
            "sources": [],
            "retrieval": results.get("debug", {}),
        }

    evidence = []
    sources = []
    seen = set()

    for source_number in selected_numbers:
        index = source_number - 1
        metadata = metadatas[index] or {}

        evidence.append(
            f"""
Document: {metadata.get("document")}
Page: {metadata.get("page")}
Supplier: {metadata.get("supplier")}
Contract ID: {metadata.get("contract_id")}
Clause type: {metadata.get("clause_type")}

{documents[index]}
"""
        )

        key = (
            metadata.get("document"),
            metadata.get("page"),
        )

        if key not in seen:
            seen.add(key)
            sources.append(
                {
                    "document": metadata.get("document"),
                    "page": metadata.get("page"),
                    "supplier": metadata.get("supplier"),
                    "contract_id": metadata.get("contract_id"),
                    "clause_type": metadata.get("clause_type"),
                    "distance": (
                        distances[index]
                        if index < len(distances)
                        else None
                    ),
                    "retrieval_score": (
                        scores[index]
                        if index < len(scores)
                        else {}
                    ),
                }
            )

    prompt = f"""
You are SupplyChain Copilot.

Answer only from the selected evidence.

QUESTION:
{question}

EVIDENCE:
{"".join(evidence)}

Never invent facts.
Never transfer a clause between suppliers.
Be concise.
"""

    answer = call_qwen_text(prompt, max_tokens=300)

    return {
        "answer": (
            answer
            or "I could not find enough evidence in the document."
        ),
        "sources": sources if answer else [],
        "retrieval": results.get("debug", {}),
    }
