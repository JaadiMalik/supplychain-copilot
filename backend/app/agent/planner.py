import json

from app.agent.llm import call_qwen_structured
from app.agent.schemas import PlannerDecision
from app.tools.registry import registry


def plan_next_step(
    question: str,
    context: dict,
    trace: list[dict],
    corrections: list[dict],
    round_number: int,
    max_rounds: int,
) -> dict:
    tools = registry.schemas()

    prompt = f"""
You are the controlled tool planner for SupplyChain Copilot v2.

Choose exactly one action:
- tool
- finish

Round {round_number} of {max_rounds}.

Rules:
1. Use only registered tools.
2. Prefer run_combined_analysis when BOTH structured data and contract evidence are needed.
3. Use query_operational_data for structured CSV/XLSX questions.
4. Use search_contract_evidence for document-only questions.
5. Never infer supplier legal-entity equivalence.
6. Deterministic tool outputs are authoritative.
7. Do not repeat identical successful calls.

QUESTION:
{question}

CONTEXT:
{json.dumps(context, default=str)}

MEMORY:
{json.dumps(corrections, default=str)}

TOOLS:
{json.dumps(tools, default=str)}

TRACE:
{json.dumps(trace, default=str)}

Return JSON only.

Tool:
{{
  "action": "tool",
  "tool_name": "query_operational_data",
  "arguments": {{"question": "Which shipments are delayed?"}},
  "reason": "..."
}}

Finish:
{{
  "action": "finish",
  "tool_name": null,
  "arguments": {{}},
  "reason": "enough evidence"
}}
"""

    decision = call_qwen_structured(
        prompt,
        PlannerDecision,
        max_tokens=450,
        retries=1,
    )

    plan = decision.model_dump()
    raw_action = plan["action"]

    aliases = {
        "final": "finish",
        "final_answer": "finish",
        "done": "finish",
        "call_tool": "tool",
        "use_tool": "tool",
    }
    action = aliases.get(raw_action, raw_action)

    registered = set(registry.names())

    if raw_action in registered:
        plan["tool_name"] = raw_action
        action = "tool"

    plan["action"] = action

    if action not in {"tool", "finish"}:
        raise ValueError(
            f"Planner returned invalid action: {raw_action!r}"
        )

    if action == "finish":
        return plan

    tool_name = (plan.get("tool_name") or "").strip()
    if not tool_name:
        raise ValueError("Planner selected tool action without tool_name.")

    registry.get(tool_name)

    arguments = plan.get("arguments", {})
    if not isinstance(arguments, dict):
        raise ValueError("Planner arguments must be an object.")

    # Reuse registry validation without executing the tool.
    spec = registry.get(tool_name)
    missing = [
        arg for arg in spec.required_args
        if arg not in arguments
    ]
    if missing:
        raise ValueError(
            f"Planner omitted required arguments for {tool_name}: "
            f"{', '.join(missing)}"
        )

    allowed = set(spec.required_args) | set(spec.optional_args)
    unexpected = sorted(set(arguments) - allowed)
    if unexpected:
        raise ValueError(
            f"Planner invented arguments for {tool_name}: "
            f"{', '.join(unexpected)}"
        )

    return plan
