from __future__ import annotations

import json
import statistics
from datetime import datetime
from pathlib import Path

from evals.models import CaseResult


def build_summary(results: list[CaseResult]) -> dict:
    total = len(results)
    passed = sum(1 for item in results if item.passed)
    latencies = [item.latency_ms for item in results]

    applicable_by_check = {}
    passed_by_check = {}

    for result in results:
        for name, check in result.checks.items():
            if not check.get("applicable"):
                continue
            applicable_by_check[name] = applicable_by_check.get(name, 0) + 1
            if check.get("passed"):
                passed_by_check[name] = passed_by_check.get(name, 0) + 1

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_cases": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": passed / total if total else 0.0,
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 2) if latencies else 0.0,
            "median": round(statistics.median(latencies), 2) if latencies else 0.0,
            "max": round(max(latencies), 2) if latencies else 0.0,
        },
        "check_accuracy": {
            name: passed_by_check.get(name, 0) / count
            for name, count in applicable_by_check.items()
        },
    }


def write_reports(results: list[CaseResult], report_dir: str | Path) -> dict:
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = build_summary(results)

    payload = {
        "summary": summary,
        "results": [
            {
                "id": item.id,
                "question": item.question,
                "mode": item.mode,
                "passed": item.passed,
                "latency_ms": round(item.latency_ms, 2),
                "checks": item.checks,
                "observed": item.observed,
                "error": item.error,
            }
            for item in results
        ],
    }

    (report_dir / "latest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )

    lines = [
        "# SupplyChain Copilot AI Evaluation Report",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Total cases: **{summary['total_cases']}**",
        f"- Passed: **{summary['passed']}**",
        f"- Failed: **{summary['failed']}**",
        f"- Pass rate: **{summary['pass_rate'] * 100:.1f}%**",
        f"- Mean latency: **{summary['latency_ms']['mean']} ms**",
        f"- Median latency: **{summary['latency_ms']['median']} ms**",
        "",
        "## Component Accuracy",
        "",
    ]

    for name, accuracy in sorted(summary["check_accuracy"].items()):
        lines.append(f"- {name}: **{accuracy * 100:.1f}%**")

    lines += [
        "",
        "## Cases",
        "",
        "| Case | Mode | Result | Latency |",
        "|---|---|---:|---:|",
    ]

    for item in results:
        lines.append(
            f"| {item.id} | {item.mode} | "
            f"{'PASS' if item.passed else 'FAIL'} | {item.latency_ms:.1f} ms |"
        )

    (report_dir / "latest.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return summary
