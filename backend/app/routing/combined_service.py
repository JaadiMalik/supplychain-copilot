import json
import requests

from app.config import (
    LM_STUDIO_URL,
    LLM_MODEL,
)

from app.analytics.service import ask_data

from app.analytics.supplier_service import (
    resolve_supplier,
)

from app.routing.evidence_service import (
    verify_supplier_penalty,
)


# ==================================================
# LM Studio helper
# ==================================================

def call_qwen_text(
    prompt: str,
    max_tokens: int = 600,
) -> str:
    """
    Call Qwen through LM Studio.

    This function is used only for planning/explanation.
    Final supplier qualification is calculated by Python.
    """

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
        if item.get(
            "type"
        ) == "message":

            content = item.get(
                "content",
                "",
            )

            if isinstance(
                content,
                str,
            ):
                output += content

    return output.strip()


def call_qwen_json(
    prompt: str,
    max_tokens: int = 300,
) -> dict:
    """
    Call Qwen and require JSON output.
    """

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
        if item.get(
            "type"
        ) == "message":

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
        .replace(
            "```json",
            "",
        )
        .replace(
            "```",
            "",
        )
        .strip()
    )

    return json.loads(
        output
    )


# ==================================================
# Combined question planner
# ==================================================

def plan_combined_question(
    question: str,
) -> dict:
    """
    Split the original user question into:

    1. structured operational-data question
    2. document evidence requirement

    The planner must preserve the original intent
    and must not add unrelated conditions.
    """

    prompt = f"""
You are the planning component of SupplyChain Copilot.

The original question requires BOTH:

1. structured operational data from CSV/Excel
2. evidence from contracts, policies, or SOPs


Split the question into exactly:

- data_question
- document_requirement


CRITICAL RULES:

1. Preserve the user's meaning exactly.

2. NEVER introduce conditions that are not explicitly
   present in the original question.

3. Do NOT introduce:
   - reorder levels
   - low stock
   - inventory shortages
   - delayed shipments
   - open purchase orders
   - supplier performance
   unless the original question asks for them.

4. If the original question says "open purchase orders",
   the structured-data question must query open purchase
   orders only.

5. Include supplier in the structured-data result whenever
   supplier contract evidence must later be checked.

6. The document requirement should describe only the
   contract/document evidence that must be verified.


EXAMPLE:

Original:

Which open purchase orders belong to suppliers with
contractual late-delivery penalties?

Correct output:

{{
  "data_question":
  "Which purchase orders are open? Include po_number, supplier, sku, order_date, promised_date, status, ordered_qty, received_qty, and unit_cost.",

  "document_requirement":
  "Determine whether each supplier is covered by a contract containing a late-delivery penalty or service-credit clause."
}}


Return valid JSON only.


ORIGINAL QUESTION:

{question}
"""

    return call_qwen_json(
        prompt,
        max_tokens=300,
    )


# ==================================================
# Main combined service
# ==================================================

def ask_combined(
    question: str,
) -> dict:
    """
    Combined workflow:

    User question
        ↓
    planner
        ↓
    DuckDB structured-data query
        ↓
    supplier extraction
        ↓
    supplier alias resolution
        ↓
    RAG evidence retrieval
        ↓
    structured evidence extraction
        ↓
    Python deterministic qualification
        ↓
    Qwen explanation only
    """

    try:

        # ==================================================
        # 1. Plan the original question
        # ==================================================

        plan = (
            plan_combined_question(
                question
            )
        )

        data_question = (
            plan.get(
                "data_question",
                "",
            )
            .strip()
        )

        document_requirement = (
            plan.get(
                "document_requirement",
                "",
            )
            .strip()
        )

        if not data_question:
            return {
                "status": "error",
                "stage": "planning",
                "message":
                    "No structured-data question was generated.",
            }

        if not document_requirement:
            return {
                "status": "error",
                "stage": "planning",
                "message":
                    "No document requirement was generated.",
            }


        # ==================================================
        # 2. Query structured operational data
        # ==================================================

        data_result = ask_data(
            data_question
        )

        if (
            data_result.get(
                "status"
            )
            != "success"
        ):
            return {
                "status": "error",
                "stage":
                    "structured_data",

                "data_question":
                    data_question,

                "data_result":
                    data_result,
            }


        data_rows = (
            data_result.get(
                "results",
                [],
            )
        )


        # ==================================================
        # 3. Extract unique suppliers
        # ==================================================

        suppliers = []

        for row in data_rows:

            supplier = (
                row.get(
                    "supplier"
                )
            )

            if (
                supplier
                and supplier
                not in suppliers
            ):
                suppliers.append(
                    supplier
                )


        # ==================================================
        # 4. Resolve supplier identities
        #    and verify contract evidence
        # ==================================================

        supplier_evidence = []

        for supplier in suppliers:

            # ----------------------------------------------
            # Resolve operational name → legal name
            # ----------------------------------------------

            resolution = (
                resolve_supplier(
                    supplier
                )
            )

            canonical_supplier = (
                resolution.get(
                    "canonical_name",
                    supplier,
                )
            )

            alias_resolved = bool(
                resolution.get(
                    "alias_resolved",
                    False,
                )
            )


            # ----------------------------------------------
            # Retrieve + structure contract evidence
            # ----------------------------------------------

            verification = (
                verify_supplier_penalty(
                    operational_supplier=
                        supplier,

                    canonical_supplier=
                        canonical_supplier,

                    alias_resolved=
                        alias_resolved,
                )
            )


            # ----------------------------------------------
            # DETERMINISTIC Python decision
            # ----------------------------------------------

            confirmed = (
                verification.get(
                    "supplier_coverage_confirmed",
                    False,
                )
                and
                verification.get(
                    "penalty_clause_confirmed",
                    False,
                )
            )

            verification[
                "confirmed"
            ] = bool(
                confirmed
            )

            supplier_evidence.append(
                verification
            )


        # ==================================================
        # 5. Build confirmed supplier set in Python
        # ==================================================

        confirmed_suppliers = {
            item[
                "operational_supplier"
            ]
            for item
            in supplier_evidence
            if item.get(
                "confirmed"
            )
        }


        # ==================================================
        # 6. Match qualifying operational rows in Python
        # ==================================================

        confirmed_rows = [
            row
            for row
            in data_rows
            if row.get(
                "supplier"
            )
            in confirmed_suppliers
        ]


        # ==================================================
        # 7. Build unconfirmed supplier list
        # ==================================================

        unconfirmed_suppliers = [
            item[
                "operational_supplier"
            ]
            for item
            in supplier_evidence
            if not item.get(
                "confirmed"
            )
        ]


        # ==================================================
        # 8. Build compact confirmed evidence
        # ==================================================

        confirmed_evidence = [
            item
            for item
            in supplier_evidence
            if item.get(
                "confirmed"
            )
        ]


        # ==================================================
        # 9. Qwen EXPLAINS the Python result
        #
        # Qwen does NOT decide which supplier qualifies.
        # ==================================================

        synthesis_prompt = f"""
You are the explanation component of SupplyChain Copilot.

Python has already completed the final qualification logic.

You MUST NOT independently decide which suppliers or records qualify.

Use the confirmed results exactly as provided.


ORIGINAL USER QUESTION:

{question}


STRUCTURED DATA QUESTION:

{data_question}


DOCUMENT REQUIREMENT:

{document_requirement}


ALL STRUCTURED DATA ROWS:

{json.dumps(
    data_rows,
    default=str,
)}


PYTHON-CONFIRMED QUALIFYING ROWS:

{json.dumps(
    confirmed_rows,
    default=str,
)}


PYTHON-CONFIRMED SUPPLIER EVIDENCE:

{json.dumps(
    confirmed_evidence,
    default=str,
)}


UNCONFIRMED SUPPLIERS:

{json.dumps(
    unconfirmed_suppliers,
    default=str,
)}


STRICT RULES:

1. The Python-confirmed qualifying rows are the final result.

2. Do NOT add a supplier or purchase order that is not
   present in PYTHON-CONFIRMED QUALIFYING ROWS.

3. Do NOT remove a supplier or purchase order that is
   present in PYTHON-CONFIRMED QUALIFYING ROWS.

4. Do NOT independently reinterpret contract evidence.

5. If confirmed_rows is empty, clearly state that no
   qualifying operational records were confirmed.

6. If confirmed_rows contains records, state exactly
   which records qualify.

7. For confirmed suppliers, explain the contractual
   penalty using only the structured evidence supplied.

8. Mention:
   - penalty type
   - rate
   - calculation period
   - maximum cap
   - exceptions
   when available.

9. You may mention unconfirmed suppliers separately,
   but clearly state that they were not confirmed.

10. Never introduce:
    - low stock
    - reorder levels
    - unrelated inventory conditions
    unless the original question asks for them.

11. Be concise and operationally useful.
"""

        final_answer = (
            call_qwen_text(
                synthesis_prompt,
                max_tokens=600,
            )
        )


        # ==================================================
        # 10. Return transparent result
        # ==================================================

        return {
            "status": "success",

            "answer":
                final_answer,

            "data_question":
                data_question,

            "document_requirement":
                document_requirement,

            "sql":
                data_result.get(
                    "sql"
                ),

            "data_rows":
                data_rows,

            "suppliers_checked":
                suppliers,

            # ----------------------------------------------
            # Important deterministic outputs
            # ----------------------------------------------

            "confirmed_suppliers":
                sorted(
                    confirmed_suppliers
                ),

            "confirmed_rows":
                confirmed_rows,

            "unconfirmed_suppliers":
                unconfirmed_suppliers,

            # ----------------------------------------------
            # Full evidence for transparency / frontend
            # ----------------------------------------------

            "supplier_evidence":
                supplier_evidence,
        }


    except Exception as error:

        return {
            "status": "error",
            "stage": "combined",
            "error_type":
                type(
                    error
                ).__name__,

            "message":
                str(
                    error
                ),
        }