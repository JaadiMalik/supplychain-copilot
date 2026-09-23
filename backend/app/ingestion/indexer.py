from pathlib import Path

from app.ingestion.pdf_parser import extract_pdf_pages
from app.ingestion.chunker import split_text
from app.rag.embeddings import embed_document
from app.rag.vector_store import save_chunk


def index_pdf(pdf_path: Path) -> dict:
    pages = extract_pdf_pages(pdf_path)

    chunk_number = 1

    for page in pages:
        chunks = split_text(page["text"])

        for chunk in chunks:
            embedding = embed_document(chunk)

            # Deterministic ID:
            # re-uploading the same filename updates the chunks
            chunk_id = (
                f"{pdf_path.stem}"
                f"-p{page['page']}"
                f"-c{chunk_number}"
            )

            save_chunk(
                chunk_id=chunk_id,
                text=chunk,
                embedding=embedding,
                document=pdf_path.name,
                page=page["page"],
            )

            chunk_number += 1

    return {
        "document": pdf_path.name,
        "pages": len(pages),
        "chunks": chunk_number - 1,
    }