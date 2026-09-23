import requests

from app.config import LM_STUDIO_URL, LLM_MODEL
from app.rag.embeddings import embed_query
from app.rag.vector_store import search_chunks


# -----------------------------
# 1. Ask the user a question
# -----------------------------

question = input("\nAsk SupplyChain Copilot: ").strip()

if not question:
    print("Please enter a question.")
    raise SystemExit


# -----------------------------
# 2. Convert question to embedding
# -----------------------------

query_embedding = embed_query(question)


# -----------------------------
# 3. Retrieve relevant chunks
# -----------------------------

results = search_chunks(
    query_embedding,
    limit=5,
)

documents = results["documents"][0]
metadatas = results["metadatas"][0]
distances = results["distances"][0]


# -----------------------------
# 4. Debug retrieved chunks
# -----------------------------

print("\nDEBUG - RETRIEVED TEXT")
print("=" * 60)

for i, text in enumerate(documents):
    metadata = metadatas[i]
    distance = distances[i]

    print(
        f"\nResult {i + 1}"
        f" | Page {metadata['page']}"
        f" | Distance {distance:.4f}"
    )

    print(text[:600])


# -----------------------------
# 5. Build evidence for Qwen
# -----------------------------

evidence_parts = []

for i, text in enumerate(documents):
    metadata = metadatas[i]

    evidence_parts.append(
        f"""
SOURCE {i + 1}
Document: {metadata["document"]}
Page: {metadata["page"]}

{text}
"""
    )

evidence = "\n".join(evidence_parts)


# -----------------------------
# 6. Build prompt
# -----------------------------

prompt = f"""
You are SupplyChain Copilot.

Answer the user's question ONLY using the evidence provided below.

Rules:

1. Never invent information.
2. Do not use outside knowledge.
3. If the evidence does not contain the answer, say exactly:
   "I could not find enough evidence in the document."
4. Give a short direct answer.
5. Mention the document name and page number.
6. If more than one source supports the answer, mention all relevant pages.

QUESTION:
{question}

EVIDENCE:
{evidence}
"""


# -----------------------------
# 7. Send evidence to Qwen
# -----------------------------

response = requests.post(
    f"{LM_STUDIO_URL}/api/v1/chat",
    json={
        "model": LLM_MODEL,
        "input": prompt,
        "reasoning": "off",
        "max_output_tokens": 300,
        "temperature": 0.1,
        "store": False,
    },
    timeout=120,
)

response.raise_for_status()

data = response.json()


# -----------------------------
# 8. Extract answer
# -----------------------------

answer = ""

for item in data.get("output", []):
    if item.get("type") == "message":
        content = item.get("content", "")

        if isinstance(content, str):
            answer += content


# -----------------------------
# 9. Show final answer
# -----------------------------

print("\nANSWER")
print("=" * 60)

if answer.strip():
    print(answer.strip())
else:
    print("No answer returned by Qwen.")


# -----------------------------
# 10. Show retrieved sources
# -----------------------------

print("\nSOURCES")
print("=" * 60)

seen_sources = set()

for metadata in metadatas:
    source = (
        metadata["document"],
        metadata["page"],
    )

    # Avoid printing the same page repeatedly
    if source not in seen_sources:
        print(
            f"{metadata['document']} "
            f"- Page {metadata['page']}"
        )

        seen_sources.add(source)