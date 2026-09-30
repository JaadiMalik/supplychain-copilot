from __future__ import annotations

import argparse
import time
from pathlib import Path

from app.agent.service import ask_v2
from app.context.resolver import resolve_context
from app.rag.service import ask_rag
from evals.evaluators.answer_eval import evaluate_answer
from evals.evaluators.context_eval import evaluate_context
from evals.evaluators.intent_eval import evaluate_intent
from evals.evaluators.retrieval_eval import evaluate_retrieval
from evals.evaluators.tool_eval import evaluate_tools
from evals.io import DEFAULT_DATASET, load_cases
from evals.models import CaseResult, EvalCase
from evals.report import write_reports


EVALS_DIR = Path(__file__).resolve().parent
REPORT_DIR = EVALS_DIR / "reports"


def run_case(case: EvalCase) -> CaseResult:
    started = time.perf_counter()

    try:
        if case.mode == "context":
            response = resolve_context(case.question)
        elif case.mode == "agent":
            response = ask_v2(case.question)
        elif case.mode == "rag":
            response = ask_rag(case.question)
        else:
            raise ValueError(f"Unknown evaluation mode: {case.mode}")

        checks = {
            "intent": evaluate_intent(response, case.expected),
            "context": evaluate_context(response, case.expected),
            "tools": evaluate_tools(response, case.expected),
            "retrieval": evaluate_retrieval(response, case.expected),
            "answer": evaluate_answer(response, case.expected),
        }

        applicable = [
            check for check in checks.values()
            if check.get("applicable")
        ]
        passed = all(check.get("passed", False) for check in applicable)

        observed = {
            "status": response.get("status"),
            "intent": (
                response.get("context", response)
                .get("intent", {})
                .get("name")
            ),
            "tools": [
                step.get("tool")
                for step in response.get("trace", [])
                if step.get("tool")
            ],
            "rounds_used": response.get("rounds_used"),
        }

        return CaseResult(
            id=case.id,
            question=case.question,
            mode=case.mode,
            passed=passed,
            latency_ms=(time.perf_counter() - started) * 1000,
            checks=checks,
            observed=observed,
        )

    except Exception as error:
        return CaseResult(
            id=case.id,
            question=case.question,
            mode=case.mode,
            passed=False,
            latency_ms=(time.perf_counter() - started) * 1000,
            error=f"{type(error).__name__}: {error}",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument(
        "--mode",
        choices=["all", "context", "agent", "rag"],
        default="all",
    )
    parser.add_argument("--tag")
    parser.add_argument("--case")
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()

    cases = load_cases(args.dataset)
    selected = [
        case for case in cases
        if (args.mode == "all" or case.mode == args.mode)
        and (not args.tag or args.tag in case.tags)
        and (not args.case or case.id == args.case)
    ]

    if not selected:
        print("No evaluation cases matched.")
        return 2

    results = []
    for i, case in enumerate(selected, start=1):
        print(f"[{i}/{len(selected)}] {case.id} ({case.mode}) ... ", end="")
        result = run_case(case)
        results.append(result)
        print("PASS" if result.passed else "FAIL")
        if result.error:
            print(f"  {result.error}")

    summary = write_reports(results, REPORT_DIR)

    print()
    print(f"Passed: {summary['passed']}/{summary['total_cases']}")
    print(f"Pass rate: {summary['pass_rate'] * 100:.1f}%")
    print(f"Median latency: {summary['latency_ms']['median']} ms")
    print(f"Report: {REPORT_DIR / 'latest.md'}")

    if args.fail_on_error and summary["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
