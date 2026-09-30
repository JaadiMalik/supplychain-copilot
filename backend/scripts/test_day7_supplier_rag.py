from app.analytics.supplier_service import resolve_supplier
from app.routing.evidence_service import verify_supplier_penalty


def verify(name: str) -> dict:
    resolution = resolve_supplier(name)
    return verify_supplier_penalty(
        operational_supplier=name,
        canonical_supplier=resolution.get("canonical_name", name),
        alias_resolved=bool(resolution.get("alias_resolved")),
    )


def main():
    atlas = verify("Atlas Industrial")

    assert atlas["alias_resolved"] is True
    assert atlas["supplier_coverage_confirmed"] is True
    assert atlas["confirmed"] is True
    assert atlas["sources"], "Atlas should have supplier-filtered evidence."
    assert all(
        source.get("supplier") == "Atlas Industrial Supplies Ltd."
        for source in atlas["sources"]
    )

    prime = verify("Prime Tools")

    assert prime["alias_resolved"] is False
    assert prime["supplier_coverage_confirmed"] is False
    assert prime["penalty_clause_confirmed"] is False
    assert prime["confirmed"] is False
    assert prime["sources"] == []

    print("✅ Day 7 supplier-aware RAG test passed.")
    print("Atlas confirmed:", atlas["confirmed"])
    print("Prime Tools confirmed:", prime["confirmed"])


if __name__ == "__main__":
    main()
