import app.agent.executor as executor


def test_planner_failure():
    original_planner = executor.plan_next_step

    def fail_planner(**kwargs):
        raise RuntimeError("simulated planner outage")

    executor.plan_next_step = fail_planner

    try:
        result = executor.run_agent(
            question="Which purchase orders are open?",
            context={
                "intent": {
                    "name": "purchase_order_analysis"
                }
            },
        )
    finally:
        executor.plan_next_step = original_planner

    assert result["status"] == "error"
    assert result["stopped_reason"] == "planner_error"
    assert result["trace"][0]["stage"] == "planner"
    assert result["trace"][0]["error_type"] == "RuntimeError"


def test_tool_failure():
    original_planner = executor.plan_next_step
    original_execute = executor.registry.execute

    call_count = {"value": 0}

    def fake_planner(**kwargs):
        call_count["value"] += 1

        if call_count["value"] == 1:
            return {
                "action": "tool",
                "tool_name": "query_operational_data",
                "arguments": {
                    "question": "Which POs are open?"
                },
                "reason": "test",
            }

        return {
            "action": "finish",
            "reason": "done",
        }

    def fail_execute(name, arguments):
        raise RuntimeError("simulated tool failure")

    executor.plan_next_step = fake_planner
    executor.registry.execute = fail_execute

    try:
        result = executor.run_agent(
            question="Which POs are open?",
            context={
                "intent": {
                    "name": "purchase_order_analysis"
                }
            },
        )
    finally:
        executor.plan_next_step = original_planner
        executor.registry.execute = original_execute

    assert result["status"] == "error"
    assert result["trace"][0]["status"] == "error"
    assert "simulated tool failure" in result["answer"]


def main():
    test_planner_failure()
    test_tool_failure()
    print("✅ Day 10 failure-mode tests passed.")


if __name__ == "__main__":
    main()
