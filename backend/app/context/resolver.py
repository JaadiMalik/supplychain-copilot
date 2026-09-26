import re

from app.context.entity_resolver import resolve_entities
from app.context.intent_resolver import resolve_intent
from app.context.period_resolver import resolve_period


RESOLVER_VERSION = "2.0.0-context-v1"


def normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", question.strip())


def _build_filters(entities: dict, period: dict) -> dict:
    filters = {}
    if entities.get("suppliers"):
        filters["suppliers"] = [
            item["canonical_name"] for item in entities["suppliers"] if item.get("canonical_name")
        ]
    for source, target in (
        ("purchase_orders", "purchase_orders"),
        ("shipments", "shipments"),
        ("skus", "skus"),
        ("statuses", "statuses"),
    ):
        if entities.get(source):
            filters[target] = entities[source]
    if period.get("matched"):
        filters["date_range"] = {
            "start_date": period.get("start_date"),
            "end_date": period.get("end_date"),
        }
    return filters


def _build_warnings(
    question: str,
    entities: dict,
) -> list[str]:
    """
    Build warnings only for concrete entity-resolution problems.

    Generic words such as "supplier" or "suppliers" should not
    generate warnings when the user has not named a supplier.
    """

    warnings = []

    unresolved = [
        item
        for item in entities.get(
            "suppliers",
            [],
        )
        if not item.get(
            "alias_resolved"
        )
    ]

    if unresolved:
        warnings.append(
            "A supplier name was found in operational data "
            "but does not have an explicit canonical alias mapping."
        )

    return warnings

def resolve_context(question: str) -> dict:
    normalized = normalize_question(question)
    if not normalized:
        raise ValueError("Question cannot be empty.")
    entities = resolve_entities(normalized)
    period = resolve_period(normalized)
    intent = resolve_intent(normalized)
    return {
        "resolver_version": RESOLVER_VERSION,
        "question": question,
        "normalized_question": normalized,
        "intent": intent,
        "entities": entities,
        "period": period,
        "filters": _build_filters(entities, period),
        "warnings": _build_warnings(normalized, entities),
    }
