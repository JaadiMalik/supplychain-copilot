from app.agent.executor import run_agent
from app.context.resolver import resolve_context
from app.memory.service import get_relevant_corrections, save_analysis


def ask_v2(question: str) -> dict:
    question = question.strip()
    if not question:
        raise ValueError("Question cannot be empty.")

    context = resolve_context(question)
    corrections = get_relevant_corrections(question)
    agent_result = run_agent(
        question=question,
        context=context,
        corrections=corrections,
    )

    analysis_id = save_analysis(
        question=question,
        context=context,
        trace=agent_result.get("trace", []),
        answer=agent_result,
    )

    return {
        "analysis_id": analysis_id,
        "question": question,
        "context": context,
        "memory_used": corrections,
        **agent_result,
    }
