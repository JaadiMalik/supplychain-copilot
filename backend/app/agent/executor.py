from __future__ import annotations

import time

from app.agent.planner import plan_next_step
from app.agent.synthesizer import synthesize_answer
from app.tools.registry import registry


MAX_TOOL_ROUNDS = 3


def _fallback_answer(trace: list[dict]) -> str:
    successful = [
        step
        for step in trace
        if step.get("status") == "success"
        and isinstance(step.get("result"), dict)
    ]

    for step in reversed(successful):
        answer = step["result"].get("answer")
        if answer:
            return str(answer)

    errors = [
        step.get("error")
        for step in trace
        if step.get("status") == "error"
        and step.get("error")
    ]

    if errors:
        return (
            "The analysis could not complete because an AI component "
            f"failed: {errors[-1]}"
        )

    return "The analysis could not collect enough evidence to answer."


def run_agent(
    question: str,
    context: dict,
    corrections: list[dict] | None = None,
) -> dict:
    corrections = corrections or []
    trace: list[dict] = []
    stopped_reason = "max_rounds_reached"

    total_started = time.perf_counter()

    planner_total_ms = 0.0
    tool_total_ms = 0.0

    for round_number in range(1, MAX_TOOL_ROUNDS + 1):
        planner_started = time.perf_counter()

        try:
            plan = plan_next_step(
                question=question,
                context=context,
                trace=trace,
                corrections=corrections,
                round_number=round_number,
                max_rounds=MAX_TOOL_ROUNDS,
            )
        except Exception as error:
            planner_ms = (
                time.perf_counter() - planner_started
            ) * 1000
            planner_total_ms += planner_ms

            trace.append(
                {
                    "round": round_number,
                    "stage": "planner",
                    "status": "error",
                    "duration_ms": round(planner_ms, 2),
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            )

            stopped_reason = "planner_error"
            break

        planner_ms = (
            time.perf_counter() - planner_started
        ) * 1000
        planner_total_ms += planner_ms

        if plan["action"] == "finish":
            stopped_reason = plan.get(
                "reason",
                "planner_finished",
            )
            break

        tool_name = plan["tool_name"]
        arguments = plan.get("arguments", {})

        step = {
            "round": round_number,
            "tool": tool_name,
            "arguments": arguments,
            "planner_reason": plan.get("reason", ""),
            "planner_duration_ms": round(planner_ms, 2),
        }

        tool_started = time.perf_counter()

        try:
            step["result"] = registry.execute(
                tool_name,
                arguments,
            )
            step["status"] = "success"
        except Exception as error:
            step["status"] = "error"
            step["error_type"] = type(error).__name__
            step["error"] = str(error)

        tool_ms = (
            time.perf_counter() - tool_started
        ) * 1000
        tool_total_ms += tool_ms
        step["duration_ms"] = round(tool_ms, 2)

        trace.append(step)

    successful_steps = [
        step
        for step in trace
        if step.get("status") == "success"
        and step.get("tool")
    ]

    failed_steps = [
        step
        for step in trace
        if step.get("status") == "error"
    ]

    synthesis_ms = 0.0

    if successful_steps:
        synthesis_started = time.perf_counter()

        try:
            answer = synthesize_answer(
                question=question,
                context=context,
                trace=trace,
            )
        except Exception:
            answer = _fallback_answer(trace)

        synthesis_ms = (
            time.perf_counter() - synthesis_started
        ) * 1000

    else:
        answer = _fallback_answer(trace)

    if trace and not successful_steps:
        overall_status = "error"
    elif successful_steps and failed_steps:
        overall_status = "partial"
    else:
        overall_status = "success"

    total_ms = (
        time.perf_counter() - total_started
    ) * 1000

    return {
        "status": overall_status,
        "answer": answer,
        "trace": trace,
        "rounds_used": len(
            [step for step in trace if step.get("tool")]
        ),
        "stopped_reason": stopped_reason,
        "metrics": {
            "total_duration_ms": round(total_ms, 2),
            "planner_duration_ms": round(planner_total_ms, 2),
            "tool_duration_ms": round(tool_total_ms, 2),
            "synthesis_duration_ms": round(synthesis_ms, 2),
        },
    }
