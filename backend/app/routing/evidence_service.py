from app.agent.llm import call_qwen_structured
from app.rag.service import ask_rag
from app.routing.schemas import PenaltyTerms


def _unconfirmed_result(
    operational_supplier: str,
    canonical_supplier: str,
    alias_resolved: bool,
    reason: str,
) -> dict:
    return {
        "operational_supplier": operational_supplier,
        "canonical_supplier": canonical_supplier,
        "alias_resolved": bool(alias_resolved),
        "supplier_coverage_confirmed": False,
        "penalty_clause_confirmed": False,
        "penalty_type": None,
        "rate": None,
        "calculation_period": None,
        "maximum_cap": None,
        "exceptions": [],
        "sources": [],
        "confirmed": False,
        "reason": reason,
    }


def verify_supplier_penalty(
    operational_supplier: str,
    canonical_supplier: str,
    alias_resolved: bool,
) -> dict:
    if not alias_resolved:
        return _unconfirmed_result(
            operational_supplier,
            canonical_supplier,
            False,
            (
                "Supplier identity is not confirmed by the explicit "
                "alias registry; contract evidence was not attributed."
            ),
        )

    rag_result = ask_rag(
        f"""
Find the late-delivery penalty or service-credit clause for
supplier {canonical_supplier}. Return only evidence belonging
to this supplier's contract.
""",
        metadata_filter={"supplier": canonical_supplier},
    )

    sources = rag_result.get("sources", [])
    if not sources:
        return _unconfirmed_result(
            operational_supplier,
            canonical_supplier,
            True,
            "No supplier-filtered contract evidence was retrieved.",
        )

    prompt = f"""
Extract the late-delivery contract terms.

Supplier:
{canonical_supplier}

Evidence answer:
{rag_result.get("answer", "")}

Return JSON matching:
{{
  "penalty_clause_confirmed": true,
  "penalty_type": "Service Credit",
  "rate": "0.5%",
  "calculation_period": "per completed calendar week",
  "maximum_cap": "5%",
  "exceptions": ["..."]
}}

Unknown strings must be null.
Unknown exceptions must be [].
Do not infer missing terms.
"""

    extracted = call_qwen_structured(
        prompt,
        PenaltyTerms,
        max_tokens=400,
        retries=1,
    )

    terms = extracted.model_dump()
    supplier_coverage_confirmed = bool(sources)
    confirmed = (
        supplier_coverage_confirmed
        and terms["penalty_clause_confirmed"]
    )

    return {
        "operational_supplier": operational_supplier,
        "canonical_supplier": canonical_supplier,
        "alias_resolved": True,
        "supplier_coverage_confirmed": supplier_coverage_confirmed,
        **terms,
        "sources": sources,
        "confirmed": confirmed,
    }
