import chromadb
import requests
from openai import OpenAI


EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0"
LLM_MODEL = "qwen/qwen3.5-9b"


# LM Studio OpenAI client - used for embeddings
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)


# ChromaDB
chroma_client = chromadb.PersistentClient(
    path="data/chroma"
)

collection = chroma_client.get_collection(
    name="supplychain_documents"
)


def create_query_embedding(question: str):
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=f"search_query: {question}"
    )

    return response.data[0].embedding


# Ask question
question = input("\nAsk a question: ")


# Retrieve chunks
query_embedding = create_query_embedding(question)

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3,
    include=["documents", "metadatas", "distances"]
)

documents = results["documents"][0]
metadatas = results["metadatas"][0]


# Build evidence
evidence_parts = []

for i, document in enumerate(documents):

    metadata = metadatas[i]

    evidence_parts.append(
        f"""
SOURCE {i + 1}
Document: {metadata['document']}
Page: {metadata['page']}

{document}
"""
    )

evidence = "\n".join(evidence_parts)


# Prompt
prompt = f"""
You are a supply-chain document assistant.

Answer the question ONLY from the supplied evidence.

Rules:
- Never invent information.
- If the answer is not present, say:
  "I could not find enough evidence in the document."
- Give a short direct answer.
- Mention the document name and page number.

QUESTION:
{question}

EVIDENCE:
{evidence}
"""


# Qwen through LM Studio native API
payload = {
    "model": LLM_MODEL,
    "input": prompt,
    "reasoning": "off",
    "max_output_tokens": 300,
    "temperature": 0.1,
    "store": False
}

response = requests.post(
    "http://127.0.0.1:1234/api/v1/chat",
    json=payload,
    timeout=120
)

response.raise_for_status()

data = response.json()


# Extract Qwen answer
answer = ""

for item in data["output"]:
    if item["type"] == "message":
        answer += item["content"]


print("\nANSWER")
print("=" * 60)

if answer:
    print(answer)
else:
    print("No answer returned by Qwen.")


print("\nRETRIEVED SOURCES")
print("=" * 60)

for i, document in enumerate(documents):
    metadata = metadatas[i]

    print(
        f"{i + 1}. {metadata['document']} "
        f"- Page {metadata['page']}"
    )