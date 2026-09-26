from typing import Any, TypedDict


class PeriodContext(TypedDict, total=False):
    matched: bool
    label: str | None
    source_text: str | None
    start_date: str | None
    end_date: str | None


class IntentContext(TypedDict, total=False):
    name: str
    confidence: float
    signals: list[str]


class EntityContext(TypedDict, total=False):
    suppliers: list[dict[str, Any]]
    purchase_orders: list[str]
    shipments: list[str]
    skus: list[str]
    statuses: list[str]


class ResolvedContext(TypedDict, total=False):
    resolver_version: str
    question: str
    normalized_question: str
    intent: IntentContext
    entities: EntityContext
    period: PeriodContext
    filters: dict[str, Any]
    warnings: list[str]
