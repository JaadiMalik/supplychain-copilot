import chromadb

from app.config import CHROMA_DIR, COLLECTION_NAME


client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)


collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)


def save_chunk(
    chunk_id: str,
    text: str,
    embedding: list[float],
    document: str,
    page: int,
):

    collection.upsert(
        ids=[chunk_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[
            {
                "document": document,
                "page": page,
            }
        ],
    )


def search_chunks(
    query_embedding: list[float],
    limit: int = 3,
):

    return collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )
def get_document_records(document_name: str):
    return collection.get(
        where={
            "document": document_name
        },
        include=["metadatas"],
    )


def delete_document_chunks(document_name: str):
    collection.delete(
        where={
            "document": document_name
        }
    )