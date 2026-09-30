from __future__ import annotations

import re
from pathlib import Path

from app.analytics.supplier_service import list_supplier_aliases

CONTRACT_ID_PATTERNS = [
    r"(?im)^\s*contract\s+id\s*[:\-]\s*([A-Z0-9][A-Z0-9._/-]+)\s*$",
    r"(?im)^\s*contract\s+(?:no|number)\s*[:\-]\s*([A-Z0-9][A-Z0-9._/-]+)\s*$",
    r"(?im)^\s*agreement\s+id\s*[:\-]\s*([A-Z0-9][A-Z0-9._/-]+)\s*$",
]

SUPPLIER_LINE_PATTERNS = [
    r"(?im)^\s*supplier(?:\s+name)?\s*[:\-]\s*([^\n\r]+)\s*$",
    r"(?im)^\s*vendor(?:\s+name)?\s*[:\-]\s*([^\n\r]+)\s*$",
]

PLACEHOLDER_SIGNALS = (
    "[supplier",
    "[vendor",
    "supplier's company name",
    "supplier’s company name",
    "specify supplier",
    "insert supplier",
    "company name]",
)

def _clean_value(value: str) -> str:
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t:;,-")

def _looks_like_placeholder(value: str) -> bool:
    lowered = value.casefold()
    if any(signal in lowered for signal in PLACEHOLDER_SIGNALS):
        return True
    if "[" in value or "]" in value:
        return True
    return False

def _first_match(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        value = _clean_value(match.group(1))
        if value:
            return value
    return ""

def _supplier_from_registry(text: str) -> str:
    aliases = list_supplier_aliases()
    candidates = []

    for item in aliases:
        alias_name = (item.get("alias_name") or "").strip()
        canonical_name = (item.get("canonical_name") or "").strip()

        if canonical_name:
            candidates.append((canonical_name, canonical_name))
        if alias_name:
            candidates.append((alias_name, canonical_name or alias_name))

    candidates.sort(key=lambda item: len(item[0]), reverse=True)

    for search_name, canonical_name in candidates:
        pattern = r"(?<!\w)" + re.escape(search_name) + r"(?!\w)"
        if re.search(pattern, text, flags=re.IGNORECASE):
            return canonical_name

    return ""

def _supplier_from_explicit_line(text: str) -> str:
    supplier = _first_match(SUPPLIER_LINE_PATTERNS, text)
    if not supplier:
        return ""
    if _looks_like_placeholder(supplier):
        return ""
    if len(supplier) > 120:
        return ""
    return supplier

def infer_document_metadata(pdf_path: Path, pages: list[dict]) -> dict:
    text = "\n".join(page.get("text", "") for page in pages)
    lowered = text.casefold()

    supplier = _supplier_from_registry(text) or _supplier_from_explicit_line(text)
    contract_id = _first_match(CONTRACT_ID_PATTERNS, text)

    if "supplier agreement" in lowered or "supplier contract" in lowered:
        document_type = "supplier_contract"
    elif "agreement" in lowered or "contract" in lowered:
        document_type = "contract"
    elif "standard operating procedure" in lowered or re.search(r"\bsop\b", lowered):
        document_type = "sop"
    else:
        document_type = "document"

    metadata = {
        "document": pdf_path.name,
        "document_type": document_type,
    }

    if supplier:
        metadata["supplier"] = supplier
    if contract_id:
        metadata["contract_id"] = contract_id

    return metadata

def infer_clause_type(text: str) -> str:
    lowered = text.casefold()

    if (
        "late-delivery" in lowered
        or "late delivery" in lowered
        or "service credit" in lowered
        or "delay penalty" in lowered
    ):
        return "late_delivery_penalty"

    if "payment term" in lowered or "net 30" in lowered or "net 45" in lowered:
        return "payment_terms"

    if "termination" in lowered:
        return "termination"
    if "warranty" in lowered:
        return "warranty"
    if "delivery" in lowered or "lead time" in lowered:
        return "delivery_terms"

    return "general"

def build_chunk_metadata(
    base_metadata: dict,
    page: int,
    chunk_text: str,
) -> dict:
    metadata = dict(base_metadata)
    metadata["page"] = int(page)
    metadata["clause_type"] = infer_clause_type(chunk_text)

    return {
        key: value
        for key, value in metadata.items()
        if value not in (None, "")
    }
