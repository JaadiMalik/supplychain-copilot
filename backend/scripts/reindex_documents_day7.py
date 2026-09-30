from pathlib import Path

from app.ingestion.indexer import index_pdf
from app.rag.vector_store import delete_document_chunks


DOCUMENT_DIR = Path("data/documents")


def main():
    pdfs = sorted(DOCUMENT_DIR.glob("*.pdf"))

    if not pdfs:
        raise SystemExit("No PDFs found in backend/data/documents.")

    for pdf_path in pdfs:
        print(f"Re-indexing {pdf_path.name} ...")
        delete_document_chunks(pdf_path.name)
        result = index_pdf(pdf_path)
        print(result)

    print(f"✅ Re-indexed {len(pdfs)} document(s) with metadata.")


if __name__ == "__main__":
    main()
