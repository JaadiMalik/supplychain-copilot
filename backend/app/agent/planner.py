import json

from app.agent.llm import call_qwen_json
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

You may choose exactly ONE action for this round:
- tool
- finish

You have at most {max_rounds} rounds total. This is round {round_number}.

IMPORTANT RULES:
1. Use only tools listed below.
2. Never invent tool names or arguments.
3. Prefer run_combined_analysis when one question requires BOTH operational data and contract evidence across multiple suppliers.
4. Use query_operational_data for CSV/XLSX-only questions.
5. Use search_contract_evidence for document-only questions.
6. Supplier identity must be resolved explicitly; never infer legal-entity equivalence.
7. Deterministic tool outputs are authoritative. Do not override them.
8. If the available trace already contains enough evidence to answer, choose finish.
9. Do not repeat a tool call with identical arguments unless the previous call failed.

USER QUESTION:
{question}

PRE-RESOLVED CONTEXT:
{json.dumps(context, default=str)}

RELEVANT CORRECTIONS/MEMORY:
{json.dumps(corrections, default=str)}

AVAILABLE TOOLS:
{json.dumps(tools, default=str)}

TRACE SO FAR:
{json.dumps(trace, default=str)}

Return JSON only.

For a tool call:
{{
  "action": "tool",
  "tool_name": "query_operational_data",
  "arguments": {{"question": "Which shipments are delayed?"}},
  "reason": "short reason"
}}

To finish:
{{
  "action": "finish",
  "reason": "enough evidence has been collected"
}}
"""
    plan = call_qwen_json(prompt, max_tokens=450)

    raw_action = str(plan.get("action", "")).strip().lower()

    action_aliases = {
        "final": "finish",
        "final_answer": "finish",
        "done": "finish",
        "call_tool": "tool",
        "use_tool": "tool",
    }

    action = action_aliases.get(raw_action, raw_action)

    # Qwen may put the registered tool name directly
    # into "action", e.g.:
    # {"action": "run_combined_analysis", ...}
    #
    # Treat that as a normal tool call.
    registered_tool_names = set(
        registry.names()
    )

    if raw_action in registered_tool_names:
        plan["tool_name"] = raw_action
        action = "tool"

    if not action:
        if plan.get("tool_name") or plan.get("tool"):
            action = "tool"
        elif plan.get("answer"):
            action = "finish"

    plan["action"] = action

    if action not in {"tool", "finish"}:
        raise ValueError(
            f"Planner returned invalid action: {raw_action!r}. Plan: {plan}"
        )

    if action == "tool":
        tool_name = plan.get("tool_name") or plan.get("tool", "")
        plan["tool_name"] = tool_name

        arguments = plan.get("arguments", plan.get("args", {}))
        plan["arguments"] = arguments

        registry.get(tool_name)

        if not isinstance(arguments, dict):
            raise ValueError("Planner arguments must be a JSON object.")

    return plan
