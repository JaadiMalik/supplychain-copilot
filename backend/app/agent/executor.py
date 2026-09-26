from app.agent.planner import plan_next_step
from app.agent.synthesizer import synthesize_answer
from app.tools.registry import registry


MAX_TOOL_ROUNDS = 3


def run_agent(
    question: str,
    context: dict,
    corrections: list[dict] | None = None,
) -> dict:
    corrections = corrections or []
    trace: list[dict] = []
    stopped_reason = "max_rounds_reached"

    for round_number in range(1, MAX_TOOL_ROUNDS + 1):
        plan = plan_next_step(
            question=question,
            context=context,
            trace=trace,
            corrections=corrections,
            round_number=round_number,
            max_rounds=MAX_TOOL_ROUNDS,
        )

        if plan["action"] == "finish":
            stopped_reason = plan.get("reason", "planner_finished")
            break

        tool_name = plan["tool_name"]
        arguments = plan.get("arguments", {})
        step = {
            "round": round_number,
            "tool": tool_name,
            "arguments": arguments,
            "planner_reason": plan.get("reason", ""),
        }

        try:
            step["result"] = registry.execute(tool_name, arguments)
            step["status"] = "success"
        except Exception as error:
            step["status"] = "error"
            step["error_type"] = type(error).__name__
            step["error"] = str(error)

        trace.append(step)

    answer = synthesize_answer(question=question, context=context, trace=trace)
    return {
        "status": "success",
        "answer": answer,
        "trace": trace,
        "rounds_used": len(trace),
        "stopped_reason": stopped_reason,
    }
