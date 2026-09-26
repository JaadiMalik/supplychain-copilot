from app.context.resolver import resolve_context
from app.routing.query_router import route_question
from app.rag.service import ask_rag
from app.analytics.service import ask_data
from app.routing.combined_service import ask_combined


def ask_supplychain_copilot(
    question: str,
) -> dict:
    try:

        # ==================================================
        # 1. Resolve deterministic business context FIRST
        # ==================================================

        context = resolve_context(
            question
        )

        normalized_question = (
            context[
                "normalized_question"
            ]
        )

        # ==================================================
        # 2. Existing local-Qwen query router
        # ==================================================

        routing = route_question(
            normalized_question
        )

        route = routing.get(
            "route",
            "unsupported",
        )

        reason = routing.get(
            "reason",
            "",
        )

        # ==================================================
        # 3. Document RAG
        # ==================================================

        if route == "document":

            result = ask_rag(
                normalized_question
            )

            return {
                "route": "document",
                "router_reason": reason,
                "context": context,
                "result": result,
            }

        # ==================================================
        # 4. Structured data
        # ==================================================

        if route == "data":

            result = ask_data(
                normalized_question
            )

            return {
                "route": "data",
                "router_reason": reason,
                "context": context,
                "result": result,
            }

        # ==================================================
        # 5. Combined data + RAG
        # ==================================================

        if route == "combined":

            result = ask_combined(
                normalized_question
            )

            return {
                "route": "combined",
                "router_reason": reason,
                "context": context,
                "result": result,
            }

        # ==================================================
        # 6. Unsupported
        # ==================================================

        return {
            "route": "unsupported",
            "router_reason": reason,
            "context": context,
            "message": (
                "This question cannot currently be answered "
                "from the uploaded documents or structured data."
            ),
        }

    except Exception as error:

        return {
            "route": "error",
            "error_type":
                type(
                    error
                ).__name__,
            "message":
                str(
                    error
                ),
        }
