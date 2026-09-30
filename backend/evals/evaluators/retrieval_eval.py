from evals.evaluators.common import recursive_collect_sources


def evaluate_retrieval(response: dict, expected: dict) -> dict:
    expected_sources = expected.get("sources")
    if not expected_sources:
        return {"applicable": False, "passed": True}

    observed_sources = recursive_collect_sources(response)
    observed_keys = {
        (item.get("document"), item.get("page"))
        for item in observed_sources
    }

    missing = [
        source
        for source in expected_sources
        if (source.get("document"), source.get("page")) not in observed_keys
    ]

    return {
        "applicable": True,
        "passed": not missing,
        "expected": expected_sources,
        "observed": observed_sources,
        "missing": missing,
    }
