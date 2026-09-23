import json
import requests

from app.config import (
    LM_STUDIO_URL,
    LLM_MODEL,
)

from app.rag.service import ask_rag


def call_qwen_json(
    prompt: str,
    max_tokens: int = 400,
) -> dict:
    response = requests.post(
        f"{LM_STUDIO_URL}/api/v1/chat",
        json={
            "model": LLM_MODEL,
            "input": prompt,
            "reasoning": "off",
            "temperature": 0.0,
            "max_output_tokens": max_tokens,
            "store": False,
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    output = ""

    for item in data.get(
        "output",
        [],
    ):
        if item.get("type") == "message":
            content = item.get(
                "content",
                "",
            )

            if isinstance(
                content,
                str,
            ):
                output += content

    output = (
        output
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    return json.loads(output)


def verify_supplier_penalty(
    operational_supplier: str,
    canonical_supplier: str,
    alias_resolved: bool,
) -> dict:
    """
    Verify supplier contract evidence.

    Important v1 safety rule:

    A supplier identity is considered contract-verified
    only when the explicit supplier alias registry confirms
    the relationship.

    The LLM may extract contract terms, but it does NOT
    decide whether an operational supplier is the same
    legal entity as the contract supplier.
    """

    # ==================================================
    # 1. Retrieve document evidence
    # ==================================================

    rag_question = f"""
Search the uploaded documents for a supplier agreement
containing a late-delivery penalty or service-credit clause.

Operational supplier:
{operational_supplier}

Canonical supplier:
{canonical_supplier}

Explicit alias registry match:
{alias_resolved}

Find evidence for:

1. named supplier / contract party
2. late-delivery penalty or service-credit clause
3. penalty type
4. rate
5. calculation period
6. maximum cap
7. exceptions

IMPORTANT:

Do not assume that a generic penalty clause proves that
the operational supplier is covered by the agreement.

Use only uploaded-document evidence.
"""

    rag_result = ask_rag(
        rag_question
    )

    answer = rag_result.get(
        "answer",
        "",
    )

    sources = rag_result.get(
        "sources",
        [],
    )

    # ==================================================
    # 2. Extract contract terms only
    # ==================================================

    extraction_prompt = f"""
You are extracting structured contract terms.

Do NOT decide whether the operational supplier identity
matches the legal supplier identity.

That identity decision is performed separately by Python.

CANONICAL SUPPLIER:

{canonical_supplier}


DOCUMENT ANSWER:

{answer}


DOCUMENT SOURCES:

{json.dumps(sources)}


Return JSON exactly:

{{
  "penalty_clause_confirmed": true,
  "penalty_type": "Service Credit",
  "rate": "0.5%",
  "calculation_period": "per completed calendar week",
  "maximum_cap": "5%",
  "exceptions": [
    "..."
  ]
}}


RULES:

1. penalty_clause_confirmed is true only when retrieved
   document evidence explicitly contains a late-delivery
   penalty or service-credit clause.

2. Do not infer missing terms.

3. Unknown text values must be null.

4. Unknown exceptions must be [].

5. Return valid JSON only.
"""

    extracted = call_qwen_json(
        extraction_prompt
    )

    penalty_clause_confirmed = bool(
        extracted.get(
            "penalty_clause_confirmed",
            False,
        )
    )

    # ==================================================
    # 3. Deterministic supplier identity decision
    # ==================================================
    #
    # IMPORTANT:
    #
    # Qwen cannot override this.
    #
    # For v1, supplier coverage is confirmed only when
    # the explicit supplier alias registry has verified
    # the operational → canonical relationship.
    # ==================================================

    supplier_coverage_confirmed = bool(
        alias_resolved
    )

    # ==================================================
    # 4. Final deterministic qualification
    # ==================================================

    confirmed = (
        supplier_coverage_confirmed
        and penalty_clause_confirmed
    )

    return {
        "operational_supplier":
            operational_supplier,

        "canonical_supplier":
            canonical_supplier,

        "alias_resolved":
            bool(alias_resolved),

        "supplier_coverage_confirmed":
            supplier_coverage_confirmed,

        "penalty_clause_confirmed":
            penalty_clause_confirmed,

        "penalty_type":
            extracted.get(
                "penalty_type"
            ),

        "rate":
            extracted.get(
                "rate"
            ),

        "calculation_period":
            extracted.get(
                "calculation_period"
            ),

        "maximum_cap":
            extracted.get(
                "maximum_cap"
            ),

        "exceptions":
            extracted.get(
                "exceptions",
                [],
            ),

        "sources":
            sources,

        "confirmed":
            confirmed,
    }