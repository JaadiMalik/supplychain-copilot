import json

from app.agent.llm import call_qwen_structured, call_qwen_text
from app.analytics.service import ask_data
from app.analytics.supplier_service import resolve_supplier
from app.routing.evidence_service import verify_supplier_penalty
from app.routing.schemas import CombinedPlan


def plan_combined_question(question: str) -> dict:
    prompt = f"""
You are the planning component of SupplyChain Copilot.

Split the question into:
- data_question
- document_requirement

Rules:
1. Preserve the original meaning.
2. Never introduce a condition the user did not request.
3. If supplier contract evidence is needed, include supplier
   in the structured-data output.
4. Return JSON only.

QUESTION:
{question}

Example:
{{
  "data_question":
    "Which purchase orders are open? Include po_number, supplier, sku, order_date, promised_date, status, ordered_qty, received_qty, and unit_cost.",
  "document_requirement":
    "Determine whether each supplier is covered by a contract containing a late-delivery penalty or service-credit clause."
}}
"""

    plan = call_qwen_structured(
        prompt,
        CombinedPlan,
        max_tokens=300,
        retries=1,
    )

    return plan.model_dump()


def ask_combined(question: str) -> dict:
    try:
        plan = plan_combined_question(question)

        data_question = plan["data_question"].strip()
        document_requirement = plan["document_requirement"].strip()

        if not data_question or not document_requirement:
            return {
                "status": "error",
                "stage": "planning",
                "message": "Combined planner returned empty requirements.",
            }

        data_result = ask_data(data_question)

        if data_result.get("status") != "success":
            return {
                "status": "error",
                "stage": "structured_data",
                "data_question": data_question,
                "data_result": data_result,
            }

        data_rows = data_result.get("results", [])

        suppliers = []
        for row in data_rows:
            supplier = row.get("supplier")
            if supplier and supplier not in suppliers:
                suppliers.append(supplier)

        supplier_evidence = []

        for supplier in suppliers:
            resolution = resolve_supplier(supplier)
            canonical = resolution.get("canonical_name", supplier)
            alias_resolved = bool(resolution.get("alias_resolved"))

            verification = verify_supplier_penalty(
                operational_supplier=supplier,
                canonical_supplier=canonical,
                alias_resolved=alias_resolved,
            )

            verification["confirmed"] = bool(
                verification.get("supplier_coverage_confirmed")
                and verification.get("penalty_clause_confirmed")
            )

            supplier_evidence.append(verification)

        confirmed_suppliers = {
            item["operational_supplier"]
            for item in supplier_evidence
            if item.get("confirmed")
        }

        confirmed_rows = [
            row
            for row in data_rows
            if row.get("supplier") in confirmed_suppliers
        ]

        unconfirmed_suppliers = [
            item["operational_supplier"]
            for item in supplier_evidence
            if not item.get("confirmed")
        ]

        confirmed_evidence = [
            item
            for item in supplier_evidence
            if item.get("confirmed")
        ]

        synthesis_prompt = f"""
You are the explanation component of SupplyChain Copilot.

Python already performed final qualification.
Do not independently add or remove suppliers or records.

QUESTION:
{question}

DATA QUESTION:
{data_question}

DOCUMENT REQUIREMENT:
{document_requirement}

CONFIRMED ROWS:
{json.dumps(confirmed_rows, default=str)}

CONFIRMED EVIDENCE:
{json.dumps(confirmed_evidence, default=str)}

UNCONFIRMED SUPPLIERS:
{json.dumps(unconfirmed_suppliers, default=str)}

Rules:
- confirmed_rows is authoritative
- only explain evidence from confirmed_evidence
- do not say penalty evidence was found for unconfirmed suppliers
- if a supplier is unconfirmed, say only that supplier-specific
  contract coverage was not confirmed
- be concise
"""

        final_answer = call_qwen_text(
            synthesis_prompt,
            max_tokens=600,
        )

        return {
            "status": "success",
            "answer": final_answer,
            "data_question": data_question,
            "document_requirement": document_requirement,
            "sql": data_result.get("sql"),
            "data_rows": data_rows,
            "suppliers_checked": suppliers,
            "confirmed_suppliers": sorted(confirmed_suppliers),
            "confirmed_rows": confirmed_rows,
            "unconfirmed_suppliers": unconfirmed_suppliers,
            "supplier_evidence": supplier_evidence,
        }

    except Exception as error:
        return {
            "status": "error",
            "stage": "combined",
            "error_type": type(error).__name__,
            "message": str(error),
        }
