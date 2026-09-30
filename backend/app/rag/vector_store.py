from __future__ import annotations

import chromadb

from app.config import CHROMA_DIR, COLLECTION_NAME


client = chromadb.PersistentClient(path=str(CHROMA_DIR))

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)


def _clean_metadata(metadata: dict) -> dict:
    return {
        key: value
        for key, value in metadata.items()
        if value not in (None, "")
        and isinstance(value, (str, int, float, bool))
    }


def save_chunk(
    chunk_id: str,
    text: str,
    embedding: list[float],
    document: str,
    page: int,
    metadata: dict | None = None,
):
    metadata = dict(metadata or {})
    metadata["document"] = document
    metadata["page"] = int(page)

    collection.upsert(
        ids=[chunk_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[_clean_metadata(metadata)],
    )


def search_chunks(
    query_embedding: list[float],
    limit: int = 3,
    where: dict | None = None,
):
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": max(1, int(limit)),
        "include": ["documents", "metadatas", "distances"],
    }

    if where:
        kwargs["where"] = where

    return collection.query(**kwargs)


def get_all_chunks(
    where: dict | None = None,
) -> dict:
    kwargs = {
        "include": ["documents", "metadatas"],
    }

    if where:
        kwargs["where"] = where

    return collection.get(**kwargs)


def get_document_records(document_name: str):
    return collection.get(
        where={"document": document_name},
        include=["metadatas"],
    )


def delete_document_chunks(document_name: str):
    collection.delete(
        where={"document": document_name}
    )
