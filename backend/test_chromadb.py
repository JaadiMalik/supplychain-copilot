from pathlib import Path

import chromadb
import pymupdf
from openai import OpenAI


PDF_PATH = Path("data/documents/sample.pdf")

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0"


# -----------------------------
# Connect to LM Studio
# -----------------------------

lm_client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)


# -----------------------------
# Connect to local ChromaDB
# -----------------------------

chroma_client = chromadb.PersistentClient(
    path="data/chroma"
)

collection = chroma_client.get_or_create_collection(
    name="supplychain_documents"
)


# -----------------------------
# Extract PDF pages
# -----------------------------

def extract_pages(pdf_path):
    document = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text()
        text = " ".join(text.split())

        if text:
            pages.append({
                "page": page_number,
                "text": text
            })

    return pages


# -----------------------------
# Split text into chunks
# -----------------------------

def split_into_chunks(text):
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


# -----------------------------
# Create Nomic embedding
# -----------------------------

def create_embedding(text, prefix):
    response = lm_client.embeddings.create(
        model=EMBED_MODEL,
        input=f"{prefix}: {text}"
    )

    return response.data[0].embedding


# -----------------------------
# Build chunks
# -----------------------------

pages = extract_pages(PDF_PATH)

chunks = []

chunk_number = 1

for page in pages:

    page_chunks = split_into_chunks(page["text"])

    for text in page_chunks:

        chunks.append({
            "id": f"chunk-{chunk_number}",
            "document": PDF_PATH.name,
            "page": page["page"],
            "text": text
        })

        chunk_number += 1


print(f"Created {len(chunks)} chunks.")


# -----------------------------
# Store chunks in ChromaDB
# -----------------------------

for index, chunk in enumerate(chunks, start=1):

    print(f"Embedding chunk {index}/{len(chunks)}...")

    embedding = create_embedding(
        chunk["text"],
        "search_document"
    )

    collection.upsert(
        ids=[chunk["id"]],
        embeddings=[embedding],
        documents=[chunk["text"]],
        metadatas=[
            {
                "document": chunk["document"],
                "page": chunk["page"]
            }
        ]
    )


print("\nAll chunks stored!")
print("Chroma records:", collection.count())


# -----------------------------
# Ask a test question
# -----------------------------

question = "What are the payment terms?"

query_embedding = create_embedding(
    question,
    "search_query"
)


results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3,
    include=["documents", "metadatas", "distances"]
)


print("\nQUESTION:")
print(question)

print("\nTOP RESULTS:")
print("=" * 60)


for i in range(len(results["documents"][0])):

    text = results["documents"][0][i]
    metadata = results["metadatas"][0][i]
    distance = results["distances"][0][i]

    print(f"\nResult {i + 1}")
    print("Document:", metadata["document"])
    print("Page:", metadata["page"])
    print("Distance:", distance)

    print("\nText:")
    print(text[:500])

    print("-" * 60)