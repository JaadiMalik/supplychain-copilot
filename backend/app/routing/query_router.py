import json
import requests

from app.config import LM_STUDIO_URL, LLM_MODEL


def route_question(question: str) -> dict:
    """
    Decide whether a question should use:

    - document: RAG only
    - data: DuckDB only, including joins across multiple tables
    - combined: DuckDB + document RAG
    - unsupported
    """

    prompt = f"""
You are the query router for SupplyChain Copilot.

Choose exactly ONE route:

document
data
combined
unsupported


ROUTING RULES

DOCUMENT:
Use when the answer must come from uploaded text documents.

Examples:
- supplier contracts
- SOPs
- policies
- clauses
- payment terms
- warranties
- contractual penalties
- termination terms

Example:
"What is the late-delivery penalty in the Atlas contract?"
=> document


DATA:
Use when the answer can be obtained entirely from structured
CSV or Excel data stored in DuckDB.

IMPORTANT:
Questions can use ONE OR MULTIPLE structured tables and still
belong to the data route.

SQL joins between:
- inventory
- shipments
- purchase orders
- suppliers
or other uploaded structured tables

are still DATA questions.

Examples:

"Which products are below reorder level?"
=> data

"Which shipments are delayed?"
=> data

"Which purchase orders are open?"
=> data

"Which open purchase orders also have delayed shipments?"
=> data

"Compare purchase orders with shipment records."
=> data

"What is the total open PO value by supplier?"
=> data


COMBINED:
Use ONLY when answering requires BOTH:

1. structured CSV/Excel operational data
AND
2. information from a document such as a contract, SOP, or policy.

Examples:

"Which delayed shipments belong to suppliers with contractual
late-delivery penalties?"
=> combined

"Which low-stock suppliers have payment terms over 30 days?"
=> combined

"Which open purchase orders belong to suppliers whose contracts
contain late-delivery penalties?"
=> combined


UNSUPPORTED:
Use when the question cannot be answered from uploaded
supply-chain documents or structured operational data.

Example:

"What is the weather today?"
=> unsupported


IMPORTANT DISTINCTION:

Multiple DuckDB tables = DATA

DuckDB data + contract/SOP/policy evidence = COMBINED


Return JSON only:

{{
    "route": "data",
    "reason": "short explanation"
}}


QUESTION:
{question}
"""

    response = requests.post(
        f"{LM_STUDIO_URL}/api/v1/chat",
        json={
            "model": LLM_MODEL,
            "input": prompt,
            "reasoning": "off",
            "temperature": 0.0,
            "max_output_tokens": 120,
            "store": False,
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    output = ""

    for item in data.get("output", []):
        if item.get("type") == "message":
            content = item.get("content", "")

            if isinstance(content, str):
                output += content

    output = output.strip()

    # Remove accidental Markdown fences
    output = output.replace("```json", "")
    output = output.replace("```", "")
    output = output.strip()

    try:
        result = json.loads(output)

    except json.JSONDecodeError:
        return {
            "route": "unsupported",
            "reason": "Router returned invalid JSON.",
        }

    allowed_routes = {
        "document",
        "data",
        "combined",
        "unsupported",
    }

    route = result.get("route")

    if route not in allowed_routes:
        return {
            "route": "unsupported",
            "reason": "Router returned an unknown route.",
        }

    return {
        "route": route,
        "reason": result.get(
            "reason",
            "",
        ),
    }