import json
from pathlib import Path

from app.config import DATA_DIR


REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in value)


def answer_text(analysis: dict) -> str:
    answer = analysis.get("answer", {})
    if isinstance(answer, dict):
        return str(answer.get("answer", ""))
    return str(answer or "")


def trace_rows(analysis: dict) -> list[dict]:
    rows = []
    for step in analysis.get("trace", []):
        rows.append(
            {
                "round": step.get("round"),
                "tool": step.get("tool"),
                "status": step.get("status"),
                "arguments": json.dumps(step.get("arguments", {}), default=str),
                "planner_reason": step.get("planner_reason", ""),
            }
        )
    return rows


def report_path(analysis_id: str, extension: str) -> Path:
    return REPORTS_DIR / f"analysis_{safe_filename(analysis_id)}.{extension}"
