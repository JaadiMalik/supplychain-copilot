import requests
import chromadb

from app.config import (
    LM_STUDIO_URL,
    LLM_MODEL,
    EMBED_MODEL,
    CHROMA_DIR,
)

from app.analytics.duckdb_service import (
    get_connection,
)


def check_lm_studio():
    try:
        response = requests.get(
            f"{LM_STUDIO_URL}/v1/models",
            timeout=5,
        )

        response.raise_for_status()

        data = response.json()

        loaded_models = [
            item.get("id")
            for item in data.get(
                "data",
                [],
            )
        ]

        return {
            "status": "healthy",
            "url": LM_STUDIO_URL,
            "llm_model": LLM_MODEL,
            "embedding_model": EMBED_MODEL,
            "loaded_models": loaded_models,
        }

    except Exception as error:
        return {
            "status": "unhealthy",
            "error": str(error),
        }


def check_duckdb():
    try:
        connection = get_connection()

        result = connection.execute(
            "SELECT 1"
        ).fetchone()

        connection.close()

        if result and result[0] == 1:
            return {
                "status": "healthy"
            }

        return {
            "status": "unhealthy"
        }

    except Exception as error:
        return {
            "status": "unhealthy",
            "error": str(error),
        }


def check_chromadb():
    try:
        client = (
            chromadb.PersistentClient(
                path=str(CHROMA_DIR)
            )
        )

        heartbeat = client.heartbeat()

        collections = (
            client.list_collections()
        )

        return {
            "status": "healthy",
            "heartbeat": heartbeat,
            "collections": len(
                collections
            ),
        }

    except Exception as error:
        return {
            "status": "unhealthy",
            "error": str(error),
        }


def get_system_health():
    lm_studio = (
        check_lm_studio()
    )

    duckdb = (
        check_duckdb()
    )

    chromadb_status = (
        check_chromadb()
    )

    components = {
        "lm_studio": lm_studio,
        "duckdb": duckdb,
        "chromadb": chromadb_status,
    }

    all_healthy = all(
        component.get("status")
        == "healthy"
        for component
        in components.values()
    )

    return {
        "status":
            "healthy"
            if all_healthy
            else "degraded",

        "components":
            components,
    }