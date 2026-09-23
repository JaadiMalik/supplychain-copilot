import json
import requests

from app.config import LM_STUDIO_URL, LLM_MODEL
from app.rag.embeddings import embed_query
from app.rag.vector_store import search_chunks


def call_qwen(prompt: str, max_tokens: int = 300) -> str:
    response = requests.post(
        f"{LM_STUDIO_URL}/api/v1/chat",
        json={
            "model": LLM_MODEL,
            "input": prompt,
            "reasoning": "off",
            "temperature": 0.0,
            "max_output_tokens": max_tokens,
            "store": False,
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    output = ""

    for item in data.get("output", []):
        if item.get("type") == "message":
            content = item.get("content", "")

            if isinstance(content, str):
                output += content

    return output.strip()


def select_best_sources(
    question: str,
    documents: list,
    metadatas: list,
) -> list[int]:

    evidence_parts = []

    for i, text in enumerate(documents, start=1):
        metadata = metadatas[i - 1]

        evidence_parts.append(
            f"""
SOURCE {i}
Document: {metadata.get("document")}
Page: {metadata.get("page")}

{text}
"""
        )

    evidence = "\n".join(evidence_parts)

    prompt = f"""
You are selecting evidence for a supply-chain RAG system.

QUESTION:
{question}

EVIDENCE:
{evidence}

Select ONLY the strongest source or sources that directly
answer the question.

Rules:

1. Prefer the original contract clause or primary section.
2. Do not select summary tables or quick-reference sections
   when the original clause is available.
3. Do not select placeholders or blank template fields.
4. Do not select sources that merely mention the topic.
5. If one primary source completely answers the question,
   select ONLY that source.
6. Select multiple sources only when the question genuinely
   requires information from multiple places.
7. If no source contains sufficient evidence, return an empty list.

Return JSON only:

{{
    "source_numbers": [1]
}}
"""

    output = call_qwen(
        prompt,
        max_tokens=100,
    )

    output = output.replace("```json", "")
    output = output.replace("```", "")
    output = output.strip()

    try:
        result = json.loads(output)

        numbers = result.get(
            "source_numbers",
            [],
        )

        valid_numbers = []

        for number in numbers:
            if (
                isinstance(number, int)
                and 1 <= number <= len(documents)
            ):
                valid_numbers.append(number)

        return valid_numbers

    except json.JSONDecodeError:
        return []


def ask_rag(question: str) -> dict:

    # -----------------------------------------
    # 1. Embed question
    # -----------------------------------------

    query_embedding = embed_query(question)

    # -----------------------------------------
    # 2. Retrieve candidate chunks
    # -----------------------------------------

    results = search_chunks(
        query_embedding,
        limit=5,
    )

    documents = results.get(
        "documents",
        [[]],
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]],
    )[0]

    if not documents:
        return {
            "answer": (
                "I could not find enough evidence "
                "in the document."
            ),
            "sources": [],
        }

    # -----------------------------------------
    # 3. Select strongest evidence
    # -----------------------------------------

    selected_numbers = select_best_sources(
        question,
        documents,
        metadatas,
    )

    if not selected_numbers:
        return {
            "answer": (
                "I could not find enough evidence "
                "in the document."
            ),
            "sources": [],
        }

    # -----------------------------------------
    # 4. Build selected evidence only
    # -----------------------------------------

    selected_evidence = []
    selected_sources = []

    seen_sources = set()

    for source_number in selected_numbers:

        index = source_number - 1

        text = documents[index]
        metadata = metadatas[index]

        selected_evidence.append(
            f"""
Document: {metadata.get("document")}
Page: {metadata.get("page")}

{text}
"""
        )

        source_key = (
            metadata.get("document"),
            metadata.get("page"),
        )

        if source_key not in seen_sources:

            selected_sources.append(
                {
                    "document": metadata.get(
                        "document"
                    ),
                    "page": metadata.get(
                        "page"
                    ),
                }
            )

            seen_sources.add(source_key)

    evidence = "\n".join(
        selected_evidence
    )

    # -----------------------------------------
    # 5. Generate final answer
    # -----------------------------------------

    prompt = f"""
You are SupplyChain Copilot.

Answer the question ONLY using the selected evidence.

QUESTION:
{question}

SELECTED EVIDENCE:
{evidence}

Rules:

1. Never use outside knowledge.
2. Never invent information.
3. Give a concise business answer.
4. Do not mention information that is not needed
   to answer the user's question.
5. If the evidence is insufficient, say exactly:

I could not find enough evidence in the document.

Do not add a separate source list.
The application will display citations separately.
"""

    answer = call_qwen(
        prompt,
        max_tokens=300,
    )

    if not answer:
        return {
            "answer": (
                "I could not find enough evidence "
                "in the document."
            ),
            "sources": [],
        }

    return {
        "answer": answer,
        "sources": selected_sources,
    }