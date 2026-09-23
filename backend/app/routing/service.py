from app.routing.query_router import route_question
from app.rag.service import ask_rag
from app.analytics.service import ask_data
from app.routing.combined_service import ask_combined


def ask_supplychain_copilot(question: str) -> dict:
    try:
        routing = route_question(question)

        route = routing.get(
            "route",
            "unsupported"
        )

        reason = routing.get(
            "reason",
            ""
        )

        # Document RAG
        if route == "document":
            result = ask_rag(question)

            return {
                "route": "document",
                "router_reason": reason,
                "result": result,
            }

        # Structured data
        elif route == "data":
            result = ask_data(question)

            return {
                "route": "data",
                "router_reason": reason,
                "result": result,
            }

        # Combined RAG + DuckDB
        elif route == "combined":
            result = ask_combined(question)

            return {
                "route": "combined",
                "router_reason": reason,
                "result": result,
            }

        # Unsupported
        return {
            "route": "unsupported",
            "router_reason": reason,
            "message": (
                "This question cannot currently be answered "
                "from the uploaded documents or structured data."
            ),
        }

    except Exception as error:
        return {
            "route": "error",
            "error_type": type(error).__name__,
            "message": str(error),
        }