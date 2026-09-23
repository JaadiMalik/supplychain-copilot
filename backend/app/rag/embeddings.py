from openai import OpenAI

from app.config import EMBED_MODEL, LM_STUDIO_URL


client = OpenAI(
    base_url=f"{LM_STUDIO_URL}/v1",
    api_key="lm-studio",
)


def embed_document(text: str) -> list[float]:

    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=f"search_document: {text}",
    )

    return response.data[0].embedding


def embed_query(text: str) -> list[float]:

    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=f"search_query: {text}",
    )

    return response.data[0].embedding