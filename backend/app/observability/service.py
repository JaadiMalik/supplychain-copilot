from __future__ import annotations

import json
from datetime import datetime

from app.analytics.duckdb_service import get_connection


def ensure_observability_table() -> None:
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS copilot_observability (
                event_id VARCHAR,
                analysis_id VARCHAR,
                event_type VARCHAR,
                status VARCHAR,
                duration_ms DOUBLE,
                metadata_json VARCHAR,
                created_at TIMESTAMP
            )
            """
        )
    finally:
        connection.close()


def _insert_event(
    event_id: str,
    analysis_id: str,
    event_type: str,
    status: str,
    duration_ms: float | None,
    metadata: dict,
) -> None:
    ensure_observability_table()
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO copilot_observability
            (
                event_id,
                analysis_id,
                event_type,
                status,
                duration_ms,
                metadata_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                event_id,
                analysis_id,
                event_type,
                status,
                duration_ms,
                json.dumps(metadata, default=str),
                datetime.now(),
            ],
        )
    finally:
        connection.close()


def record_analysis_metrics(
    analysis_id: str,
    agent_result: dict,
) -> None:
    metrics = agent_result.get("metrics", {})

    _insert_event(
        event_id=f"{analysis_id}:analysis",
        analysis_id=analysis_id,
        event_type="analysis",
        status=agent_result.get("status", "unknown"),
        duration_ms=metrics.get("total_duration_ms"),
        metadata={
            "rounds_used": agent_result.get("rounds_used"),
            "stopped_reason": agent_result.get("stopped_reason"),
            "planner_duration_ms": metrics.get("planner_duration_ms"),
            "tool_duration_ms": metrics.get("tool_duration_ms"),
            "synthesis_duration_ms": metrics.get("synthesis_duration_ms"),
        },
    )

    for step in agent_result.get("trace", []):
        round_number = step.get("round")
        event_type = (
            "tool"
            if step.get("tool")
            else step.get("stage", "agent_step")
        )

        _insert_event(
            event_id=f"{analysis_id}:{event_type}:{round_number}",
            analysis_id=analysis_id,
            event_type=event_type,
            status=step.get("status", "unknown"),
            duration_ms=step.get("duration_ms"),
            metadata={
                "round": round_number,
                "tool": step.get("tool"),
                "planner_reason": step.get("planner_reason"),
                "error_type": step.get("error_type"),
                "error": step.get("error"),
                "planner_duration_ms": step.get("planner_duration_ms"),
            },
        )


def get_observability_summary(
    limit: int = 100,
) -> dict:
    ensure_observability_table()
    limit = max(1, min(int(limit), 1000))

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                status,
                COUNT(*) AS count,
                AVG(duration_ms) AS avg_duration_ms
            FROM (
                SELECT status, duration_ms
                FROM copilot_observability
                WHERE event_type = 'analysis'
                ORDER BY created_at DESC
                LIMIT ?
            )
            GROUP BY status
            ORDER BY status
            """,
            [limit],
        ).fetchall()

        recent = connection.execute(
            """
            SELECT
                analysis_id,
                status,
                duration_ms,
                metadata_json,
                created_at
            FROM copilot_observability
            WHERE event_type = 'analysis'
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [min(limit, 20)],
        ).fetchall()

    finally:
        connection.close()

    return {
        "by_status": [
            {
                "status": row[0],
                "count": int(row[1]),
                "avg_duration_ms": (
                    round(float(row[2]), 2)
                    if row[2] is not None
                    else None
                ),
            }
            for row in rows
        ],
        "recent": [
            {
                "analysis_id": row[0],
                "status": row[1],
                "duration_ms": row[2],
                "metadata": json.loads(row[3] or "{}"),
                "created_at": str(row[4]),
            }
            for row in recent
        ],
    }
