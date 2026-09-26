import json
import uuid
from datetime import datetime

from app.analytics.duckdb_service import get_connection
from app.analytics.supplier_service import add_supplier_alias


def ensure_memory_tables() -> None:
    connection = get_connection()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS copilot_corrections (
                correction_id VARCHAR PRIMARY KEY,
                correction_type VARCHAR,
                correction_key VARCHAR,
                correction_value VARCHAR,
                note VARCHAR,
                active BOOLEAN,
                created_at TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS copilot_analysis_history (
                analysis_id VARCHAR PRIMARY KEY,
                question VARCHAR,
                context_json VARCHAR,
                trace_json VARCHAR,
                answer_json VARCHAR,
                created_at TIMESTAMP
            )
            """
        )
    finally:
        connection.close()


def remember_correction(
    correction_type: str,
    key: str,
    value: str,
    note: str = "",
) -> dict:
    ensure_memory_tables()
    correction_id = str(uuid.uuid4())
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO copilot_corrections
            (correction_id, correction_type, correction_key, correction_value, note, active, created_at)
            VALUES (?, ?, ?, ?, ?, TRUE, ?)
            """,
            [
                correction_id,
                correction_type.strip(),
                key.strip(),
                value.strip(),
                note.strip(),
                datetime.now(),
            ],
        )
    finally:
        connection.close()
    return {
        "correction_id": correction_id,
        "correction_type": correction_type.strip(),
        "key": key.strip(),
        "value": value.strip(),
        "note": note.strip(),
        "active": True,
    }


def remember_supplier_alias(alias_name: str, canonical_name: str, note: str = "") -> dict:
    alias = add_supplier_alias(alias_name=alias_name, canonical_name=canonical_name)
    memory = remember_correction(
        correction_type="supplier_alias",
        key=alias_name,
        value=canonical_name,
        note=note or "Stored in explicit supplier alias registry.",
    )
    return {"supplier_alias": alias, "memory": memory}


def list_corrections(active_only: bool = True, limit: int = 100) -> list[dict]:
    ensure_memory_tables()
    limit = max(1, min(int(limit), 500))
    connection = get_connection()
    try:
        where = "WHERE active = TRUE" if active_only else ""
        rows = connection.execute(
            f"""
            SELECT correction_id, correction_type, correction_key,
                   correction_value, note, active, created_at
            FROM copilot_corrections
            {where}
            ORDER BY created_at DESC
            LIMIT {limit}
            """
        ).fetchall()
    finally:
        connection.close()
    return [
        {
            "correction_id": row[0],
            "correction_type": row[1],
            "key": row[2],
            "value": row[3],
            "note": row[4],
            "active": bool(row[5]),
            "created_at": str(row[6]),
        }
        for row in rows
    ]


def get_relevant_corrections(question: str, limit: int = 20) -> list[dict]:
    text = question.casefold()
    relevant = []
    for item in list_corrections(active_only=True, limit=200):
        key = (item.get("key") or "").casefold()
        correction_type = item.get("correction_type")
        if correction_type == "preference" or (key and key in text):
            relevant.append(item)
        if len(relevant) >= limit:
            break
    return relevant


def deactivate_correction(correction_id: str) -> dict:
    ensure_memory_tables()
    connection = get_connection()
    try:
        existing = connection.execute(
            "SELECT correction_id FROM copilot_corrections WHERE correction_id = ?",
            [correction_id],
        ).fetchone()
        if not existing:
            return {"updated": False, "correction_id": correction_id}
        connection.execute(
            "UPDATE copilot_corrections SET active = FALSE WHERE correction_id = ?",
            [correction_id],
        )
    finally:
        connection.close()
    return {"updated": True, "correction_id": correction_id, "active": False}


def save_analysis(question: str, context: dict, trace: list[dict], answer: dict) -> str:
    ensure_memory_tables()
    analysis_id = str(uuid.uuid4())
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO copilot_analysis_history
            (analysis_id, question, context_json, trace_json, answer_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                analysis_id,
                question,
                json.dumps(context, default=str),
                json.dumps(trace, default=str),
                json.dumps(answer, default=str),
                datetime.now(),
            ],
        )
    finally:
        connection.close()
    return analysis_id


def _decode_analysis(row) -> dict:
    return {
        "analysis_id": row[0],
        "question": row[1],
        "context": json.loads(row[2] or "{}"),
        "trace": json.loads(row[3] or "[]"),
        "answer": json.loads(row[4] or "{}"),
        "created_at": str(row[5]),
    }


def get_analysis(analysis_id: str) -> dict | None:
    ensure_memory_tables()
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT analysis_id, question, context_json, trace_json, answer_json, created_at
            FROM copilot_analysis_history
            WHERE analysis_id = ?
            """,
            [analysis_id],
        ).fetchone()
    finally:
        connection.close()
    return _decode_analysis(row) if row else None


def list_history(limit: int = 50) -> list[dict]:
    ensure_memory_tables()
    limit = max(1, min(int(limit), 200))
    connection = get_connection()
    try:
        rows = connection.execute(
            f"""
            SELECT analysis_id, question, context_json, trace_json, answer_json, created_at
            FROM copilot_analysis_history
            ORDER BY created_at DESC
            LIMIT {limit}
            """
        ).fetchall()
    finally:
        connection.close()
    return [_decode_analysis(row) for row in rows]
