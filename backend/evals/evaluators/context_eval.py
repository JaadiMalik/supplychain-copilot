from evals.evaluators.common import normalize_text


def evaluate_context(response: dict, expected: dict) -> dict:
    context = response.get("context", response)
    checks = {}
    passed = True

    expected_statuses = expected.get("statuses")
    if expected_statuses is not None:
        observed = context.get("entities", {}).get("statuses", [])
        ok = {normalize_text(x) for x in observed} == {
            normalize_text(x) for x in expected_statuses
        }
        checks["statuses"] = {
            "passed": ok,
            "expected": expected_statuses,
            "observed": observed,
        }
        passed = passed and ok

    expected_suppliers = expected.get("suppliers")
    if expected_suppliers is not None:
        observed_items = context.get("entities", {}).get("suppliers", [])
        observed = [
            {
                "canonical_name": item.get("canonical_name"),
                "alias_resolved": bool(item.get("alias_resolved")),
            }
            for item in observed_items
        ]

        def key(item):
            return (
                normalize_text(item.get("canonical_name")),
                bool(item.get("alias_resolved")),
            )

        ok = {key(item) for item in observed} == {
            key(item) for item in expected_suppliers
        }

        checks["suppliers"] = {
            "passed": ok,
            "expected": expected_suppliers,
            "observed": observed,
        }
        passed = passed and ok

    expected_warning_count = expected.get("warning_count")
    if expected_warning_count is not None:
        observed_count = len(context.get("warnings", []))
        ok = observed_count == expected_warning_count
        checks["warning_count"] = {
            "passed": ok,
            "expected": expected_warning_count,
            "observed": observed_count,
        }
        passed = passed and ok

    if not checks:
        return {"applicable": False, "passed": True}

    return {
        "applicable": True,
        "passed": passed,
        "checks": checks,
    }
