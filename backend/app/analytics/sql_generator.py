import json
import requests

from app.config import LM_STUDIO_URL, LLM_MODEL
from app.analytics.dataset_service import get_database_schema


def generate_sql(question: str) -> dict:

    schema = get_database_schema()

    if not schema:
        return {
            "sql": "",
            "explanation": "No structured datasets are loaded.",
        }

    schema_text_parts = []

    for table in schema:

        columns = []

        for column in table["columns"]:
            columns.append(
                f'{column["name"]} ({column["dtype"]})'
            )

        schema_text_parts.append(
            f"""
TABLE: {table["table_name"]}
Source file: {table["source_file"]}
Sheet: {table["sheet_name"] or "N/A"}

Columns:
{", ".join(columns)}
"""
        )

    schema_text = "\n".join(schema_text_parts)

    prompt = f"""
You are a supply-chain data analyst.

Convert the user's question into ONE safe,
read-only DuckDB SELECT query.

AVAILABLE DATA:

{schema_text}

RULES:

1. SELECT queries only.
2. Never use:
   INSERT
   UPDATE
   DELETE
   DROP
   ALTER
   CREATE
   COPY
   ATTACH
   DETACH
   INSTALL
   LOAD

3. Use ONLY the tables listed above.
4. Use ONLY columns that actually exist.
5. Do not invent tables.
6. Do not invent columns.
7. Use DuckDB SQL syntax.
8. Add LIMIT 100 unless aggregation naturally
   returns a small result.
9. Return valid JSON only.
10. Do not use markdown.
11. When a table contains an explicit status column,
    use that status field when the user's question refers
    to states such as delayed, open, closed, cancelled,
    delivered, or in transit.

12. Date comparisons may be used in addition to status,
    but should not replace an explicit status value when
    relevant.
    13. Text comparisons must be case-insensitive when matching
    categorical values such as status, supplier, product, or location.

14. Prefer LOWER(column) = 'value' or
    LOWER(column) IN (...) for categorical text comparisons.

15. When the user asks for "delayed shipments", include both:
    - status = Delayed
    - status = Delivered Late
    when those values are relevant.

Return exactly:

{{
    "sql": "SELECT ...",
    "explanation": "Short explanation"
}}

USER QUESTION:

{question}
"""

    response = requests.post(
        f"{LM_STUDIO_URL}/api/v1/chat",
        json={
            "model": LLM_MODEL,
            "input": prompt,
            "reasoning": "off",
            "temperature": 0.0,
            "max_output_tokens": 300,
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

    output = output.replace(
        "```json",
        ""
    )

    output = output.replace(
        "```",
        ""
    )

    output = output.strip()

    return json.loads(output)