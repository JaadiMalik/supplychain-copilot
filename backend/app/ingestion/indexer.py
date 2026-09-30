from pathlib import Path

from app.ingestion.chunker import split_text
from app.ingestion.metadata import (
    build_chunk_metadata,
    infer_document_metadata,
)
from app.ingestion.pdf_parser import extract_pdf_pages
from app.rag.embeddings import embed_document
from app.rag.vector_store import save_chunk


def index_pdf(pdf_path: Path) -> dict:
    pages = extract_pdf_pages(pdf_path)
    base_metadata = infer_document_metadata(pdf_path, pages)

    chunk_number = 1

    for page in pages:
        chunks = split_text(page["text"])

        for chunk in chunks:
            embedding = embed_document(chunk)

            chunk_id = (
                f"{pdf_path.stem}"
                f"-p{page['page']}"
                f"-c{chunk_number}"
            )

            metadata = build_chunk_metadata(
                base_metadata=base_metadata,
                page=page["page"],
                chunk_text=chunk,
            )

            save_chunk(
                chunk_id=chunk_id,
                text=chunk,
                embedding=embedding,
                document=pdf_path.name,
                page=page["page"],
                metadata=metadata,
            )

            chunk_number += 1

    return {
        "document": pdf_path.name,
        "pages": len(pages),
        "chunks": chunk_number - 1,
        "metadata": base_metadata,
    }
