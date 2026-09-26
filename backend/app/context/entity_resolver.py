import re

from app.context.catalog import get_known_suppliers


STATUS_PATTERNS = {
    "delivered_late": [r"\bdelivered\s+late\b", r"\blate\s+delivery\b"],
    "delayed": [r"\bdelayed\b", r"\bdelay(?:ed|s)?\b", r"\blate\s+shipment(?:s)?\b"],
    "in_transit": [r"\bin[\s-]+transit\b"],
    "open": [r"\bopen\b", r"\boutstanding\b"],
    "closed": [r"\bclosed\b"],
    "delivered": [r"\bdelivered\b"],
    "low_stock": [r"\blow[\s-]+stock\b", r"\bbelow\s+reorder\b", r"\breorder\s+level\b"],
}


def _normalize_for_match(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^\w]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = f" {_normalize_for_match(text)} "
    normalized_phrase = _normalize_for_match(phrase)
    return bool(normalized_phrase and f" {normalized_phrase} " in normalized_text)


def _extract_ids(question: str, prefix: str) -> list[str]:
    pattern = rf"\b{prefix}[\s_-]*[A-Z]*\d+[A-Z0-9_-]*\b"
    matches = re.findall(pattern, question.upper(), flags=re.IGNORECASE)
    result = []
    for value in matches:
        compact = re.sub(r"[\s_-]+", "", value.upper())
        if compact not in result:
            result.append(compact)
    return result


def resolve_suppliers(question: str) -> list[dict]:
    matches = []
    for supplier in get_known_suppliers():
        name = supplier.get("name", "")
        if not name or not _contains_phrase(question, name):
            continue
        item = {
            "matched_text": name,
            "supplier_name": name,
            "canonical_name": supplier.get("canonical_name", name),
            "alias_resolved": bool(supplier.get("alias_resolved")),
            "source": supplier.get("source"),
        }
        if item not in matches:
            matches.append(item)
    return matches


def resolve_statuses(question: str) -> list[str]:
    text = question.casefold()
    resolved = []
    for status, patterns in STATUS_PATTERNS.items():
        if any(re.search(pattern, text) for pattern in patterns):
            resolved.append(status)
    if "delivered_late" in resolved and "delivered" in resolved:
        resolved.remove("delivered")
    # Final status normalization:
    # "delivered late" is more specific than
    # generic "delayed" or "delivered".
    if "delivered_late" in resolved:
        resolved = [
            status
            for status in resolved
            if status not in {
                "delayed",
                "delivered",
            }
        ]

    return resolved


def resolve_entities(question: str) -> dict:
    return {
        "suppliers": resolve_suppliers(question),
        "purchase_orders": _extract_ids(question, "PO"),
        "shipments": _extract_ids(question, "SHP"),
        "skus": _extract_ids(question, "SKU"),
        "statuses": resolve_statuses(question),
    }
