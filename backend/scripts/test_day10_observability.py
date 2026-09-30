import uuid

from app.observability.service import (
    get_observability_summary,
    record_analysis_metrics,
)


def main():
    analysis_id = f"test-{uuid.uuid4()}"

    record_analysis_metrics(
        analysis_id=analysis_id,
        agent_result={
            "status": "success",
            "rounds_used": 1,
            "stopped_reason": "test_complete",
            "metrics": {
                "total_duration_ms": 123.4,
                "planner_duration_ms": 20.0,
                "tool_duration_ms": 80.0,
                "synthesis_duration_ms": 23.4,
            },
            "trace": [
                {
                    "round": 1,
                    "tool": "query_operational_data",
                    "status": "success",
                    "duration_ms": 80.0,
                    "planner_duration_ms": 20.0,
                }
            ],
        },
    )

    summary = get_observability_summary(limit=20)

    assert any(
        item["analysis_id"] == analysis_id
        for item in summary["recent"]
    )

    print("✅ Day 10 observability persistence test passed.")


if __name__ == "__main__":
    main()
