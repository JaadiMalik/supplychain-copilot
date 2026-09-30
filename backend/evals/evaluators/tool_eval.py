def evaluate_tools(response: dict, expected: dict) -> dict:
    expected_tools = expected.get("tools")
    if not expected_tools:
        return {"applicable": False, "passed": True}

    observed_tools = [
        step.get("tool")
        for step in response.get("trace", [])
        if step.get("tool")
    ]

    exact = expected.get("tools_exact", True)
    passed = (
        observed_tools == expected_tools
        if exact
        else all(tool in observed_tools for tool in expected_tools)
    )

    return {
        "applicable": True,
        "passed": passed,
        "expected": expected_tools,
        "observed": observed_tools,
        "exact": exact,
    }
