from app.rag.embeddings import embed_query
from app.rag.retrieval import retrieve_chunks


QUESTION = "What is the late-delivery service credit rate and maximum cap?"


def main():
    embedding = embed_query(QUESTION)

    vector = retrieve_chunks(
        QUESTION,
        embedding,
        limit=5,
        mode="vector",
    )

    hybrid = retrieve_chunks(
        QUESTION,
        embedding,
        limit=5,
        mode="hybrid",
    )

    assert vector["documents"][0], "Vector retrieval returned nothing."
    assert hybrid["documents"][0], "Hybrid retrieval returned nothing."
    assert hybrid["debug"]["mode"] == "hybrid"

    print("✅ Day 9 hybrid retrieval smoke test passed.")
    print("Vector IDs:", vector["ids"][0])
    print("Hybrid IDs:", hybrid["ids"][0])


if __name__ == "__main__":
    main()
