from pathlib import Path

from app.ingestion.pdf_parser import extract_pdf_pages
from app.ingestion.chunker import split_text
from app.rag.embeddings import embed_document
from app.rag.vector_store import save_chunk


PDF_PATH = Path("data/documents/sample.pdf")


print(f"\nIndexing: {PDF_PATH.name}")


pages = extract_pdf_pages(PDF_PATH)

chunk_number = 1


for page in pages:

    chunks = split_text(page["text"])

    for chunk in chunks:

        print(
            f"Embedding chunk {chunk_number} "
            f"(page {page['page']})..."
        )

        embedding = embed_document(chunk)

        chunk_id = (
            f"{PDF_PATH.stem}"
            f"-p{page['page']}"
            f"-c{chunk_number}"
        )

        save_chunk(
            chunk_id=chunk_id,
            text=chunk,
            embedding=embedding,
            document=PDF_PATH.name,
            page=page["page"],
        )

        chunk_number += 1


print("\nDocument indexed successfully.")