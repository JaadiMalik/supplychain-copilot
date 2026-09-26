import json

from app.agent.llm import call_qwen_text


def synthesize_answer(question: str, context: dict, trace: list[dict]) -> str:
    prompt = f"""
You are the final explanation layer of SupplyChain Copilot v2.

Answer the user's question using ONLY the tool trace below.

STRICT RULES:
1. Never invent facts not present in tool results.
2. Never independently change a deterministic confirmed/unconfirmed result.
3. If a tool says a supplier or record is unconfirmed, state that it is unconfirmed.
4. If the trace contains page/document evidence, use it in the explanation.
5. Be concise and operationally useful.
6. If the trace does not contain enough evidence, say that clearly.
7. Do not reveal hidden reasoning. Summarize actions and evidence only.

QUESTION:
{question}

CONTEXT:
{json.dumps(context, default=str)}

TOOL TRACE:
{json.dumps(trace, default=str)}
"""
    answer = call_qwen_text(prompt, max_tokens=700)
    return answer or "I could not produce a grounded answer from the available tool results."
