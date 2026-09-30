from evals.io import load_cases
from evals.runner import run_case


def main():
    cases = [
        case
        for case in load_cases()
        if case.mode == "context" and "smoke" in case.tags
    ]
    assert cases, "No context smoke cases found."

    for case in cases:
        result = run_case(case)
        assert result.passed, (
            f"{case.id} failed: "
            f"error={result.error}, checks={result.checks}"
        )

    print(f"✅ Day 6 smoke evaluation passed ({len(cases)} cases).")


if __name__ == "__main__":
    main()
