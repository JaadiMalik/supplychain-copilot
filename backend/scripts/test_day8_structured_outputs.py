from pydantic import ValidationError

from app.agent.schemas import PlannerDecision
from app.routing.schemas import CombinedPlan, PenaltyTerms


def main():
    decision = PlannerDecision.model_validate(
        {
            "action": "TOOL",
            "tool_name": "query_operational_data",
            "arguments": {"question": "Which POs are open?"},
            "reason": "structured data",
        }
    )
    assert decision.action == "tool"

    plan = CombinedPlan.model_validate(
        {
            "data_question": "Which POs are open?",
            "document_requirement": "Check contract penalties.",
        }
    )
    assert plan.data_question

    terms = PenaltyTerms.model_validate(
        {
            "penalty_clause_confirmed": True,
            "penalty_type": "Service Credit",
            "rate": "0.5%",
            "calculation_period": "per completed calendar week",
            "maximum_cap": "5%",
            "exceptions": [],
        }
    )
    assert terms.penalty_clause_confirmed is True

    try:
        CombinedPlan.model_validate({"data_question": "missing other field"})
    except ValidationError:
        pass
    else:
        raise AssertionError("Invalid CombinedPlan should fail validation.")

    print("✅ Day 8 structured schema tests passed.")


if __name__ == "__main__":
    main()
