from pathlib import Path
import pymupdf


PDF_PATH = Path("data/documents/sample.pdf")

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


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


pages = extract_pages(PDF_PATH)

all_chunks = []

chunk_id = 1

for page in pages:
    chunks = split_into_chunks(page["text"])

    for chunk in chunks:
        all_chunks.append({
            "chunk_id": chunk_id,
            "document": PDF_PATH.name,
            "page": page["page"],
            "text": chunk
        })

        chunk_id += 1


print(f"Document: {PDF_PATH.name}")
print(f"Pages: {len(pages)}")
print(f"Total chunks: {len(all_chunks)}")
print("=" * 60)

for chunk in all_chunks:
    print(f"\nChunk ID: {chunk['chunk_id']}")
    print(f"Page: {chunk['page']}")
    print(chunk["text"][:300])