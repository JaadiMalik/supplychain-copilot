from evals.evaluators.common import (
    contains_all,
    contains_none,
    normalize_text,
    recursive_find_values,
)


def _flatten_scalar_lists(values: list) -> list[str]:
    flattened = []
    for value in values:
        if isinstance(value, list):
            for item in value:
                if isinstance(item, (str, int, float)):
                    flattened.append(str(item))
    return flattened


def evaluate_answer(response: dict, expected: dict) -> dict:
    checks = {}
    passed = True

    answer = response.get("answer", "")
    if isinstance(answer, dict):
        answer = answer.get("answer", "")

    required = expected.get("answer_contains", [])
    forbidden = expected.get("answer_not_contains", [])

    if required:
        ok, missing = contains_all(answer, required)
        checks["answer_contains"] = {
            "passed": ok,
            "required": required,
            "missing": missing,
        }
        passed = passed and ok

    if forbidden:
        ok, found = contains_none(answer, forbidden)
        checks["answer_not_contains"] = {
            "passed": ok,
            "forbidden": forbidden,
            "found": found,
        }
        passed = passed and ok

    expected_status = expected.get("status")
    if expected_status:
        observed_status = response.get("status")
        ok = normalize_text(observed_status) == normalize_text(expected_status)
        checks["status"] = {
            "passed": ok,
            "expected": expected_status,
            "observed": observed_status,
        }
        passed = passed and ok

    expected_suppliers = expected.get("confirmed_suppliers")
    if expected_suppliers is not None:
        observed = _flatten_scalar_lists(
            recursive_find_values(response, "confirmed_suppliers")
        )
        ok = {normalize_text(x) for x in observed} == {
            normalize_text(x) for x in expected_suppliers
        }
        checks["confirmed_suppliers"] = {
            "passed": ok,
            "expected": expected_suppliers,
            "observed": observed,
        }
        passed = passed and ok

    expected_pos = expected.get("confirmed_purchase_orders")
    if expected_pos is not None:
        rows_values = recursive_find_values(response, "confirmed_rows")
        observed_pos = []
        for rows in rows_values:
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict) and row.get("po_number"):
                        observed_pos.append(str(row["po_number"]))

        ok = {normalize_text(x) for x in observed_pos} == {
            normalize_text(x) for x in expected_pos
        }
        checks["confirmed_purchase_orders"] = {
            "passed": ok,
            "expected": expected_pos,
            "observed": observed_pos,
        }
        passed = passed and ok

    expected_rounds = expected.get("rounds_used")
    if expected_rounds is not None:
        observed_rounds = response.get("rounds_used")
        ok = observed_rounds == expected_rounds
        checks["rounds_used"] = {
            "passed": ok,
            "expected": expected_rounds,
            "observed": observed_rounds,
        }
        passed = passed and ok

    if not checks:
        return {"applicable": False, "passed": True}

    return {
        "applicable": True,
        "passed": passed,
        "checks": checks,
    }
