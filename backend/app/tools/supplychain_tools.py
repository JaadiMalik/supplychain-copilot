from app.analytics.dataset_service import get_database_schema, list_datasets
from app.analytics.service import ask_data
from app.analytics.supplier_service import resolve_supplier
from app.rag.service import ask_rag
from app.routing.combined_service import ask_combined
from app.routing.evidence_service import verify_supplier_penalty


def query_operational_data(question: str) -> dict:
    return ask_data(question)


def search_contract_evidence(question: str) -> dict:
    return ask_rag(question)


def resolve_supplier_identity(supplier_name: str) -> dict:
    return resolve_supplier(supplier_name)


def verify_supplier_late_penalty(supplier_name: str) -> dict:
    resolution = resolve_supplier(supplier_name)
    canonical = resolution.get("canonical_name", supplier_name)
    alias_resolved = bool(resolution.get("alias_resolved"))
    verification = verify_supplier_penalty(
        operational_supplier=supplier_name,
        canonical_supplier=canonical,
        alias_resolved=alias_resolved,
    )
    verification["confirmed"] = bool(
        verification.get("supplier_coverage_confirmed")
        and verification.get("penalty_clause_confirmed")
    )
    return verification


def run_combined_analysis(question: str) -> dict:
    return ask_combined(question)


def get_structured_schema() -> dict:
    return {"tables": get_database_schema()}


def get_dataset_catalog() -> dict:
    return {"datasets": list_datasets()}
