def evaluate_intent(response: dict, expected: dict) -> dict:
    expected_intent = expected.get("intent")
    if not expected_intent:
        return {"applicable": False, "passed": True}

    observed_intent = (
        response.get("context", response)
        .get("intent", {})
        .get("name")
    )

    return {
        "applicable": True,
        "passed": observed_intent == expected_intent,
        "expected": expected_intent,
        "observed": observed_intent,
    }
