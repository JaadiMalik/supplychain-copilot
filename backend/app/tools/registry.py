from typing import Any

from app.tools.base import ToolSpec
from app.tools.supplychain_tools import (
    get_dataset_catalog,
    get_structured_schema,
    query_operational_data,
    resolve_supplier_identity,
    run_combined_analysis,
    search_contract_evidence,
    verify_supplier_late_penalty,
)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def names(self) -> list[str]:
        return sorted(self._tools)

    def schemas(self) -> list[dict]:
        return [self._tools[name].public_schema() for name in self.names()]

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict:
        tool = self.get(name)
        arguments = arguments or {}

        missing = [arg for arg in tool.required_args if arg not in arguments]
        if missing:
            raise ValueError(f"Missing arguments for {name}: {', '.join(missing)}")

        allowed = set(tool.required_args) | set(tool.optional_args)
        unexpected = sorted(set(arguments) - allowed)
        if unexpected:
            raise ValueError(f"Unexpected arguments for {name}: {', '.join(unexpected)}")

        return tool.handler(**arguments)


registry = ToolRegistry()

registry.register(
    ToolSpec(
        name="query_operational_data",
        description=(
            "Ask a read-only structured-data question across uploaded CSV/XLSX tables. "
            "Use for inventory, shipments, purchase orders, quantities, dates, status and joins."
        ),
        handler=query_operational_data,
        required_args=("question",),
    )
)
registry.register(
    ToolSpec(
        name="search_contract_evidence",
        description=(
            "Search indexed supplier contracts/documents and return an evidence-grounded answer with pages."
        ),
        handler=search_contract_evidence,
        required_args=("question",),
    )
)
registry.register(
    ToolSpec(
        name="resolve_supplier_identity",
        description=(
            "Resolve an operational supplier name using the explicit supplier alias registry. "
            "This tool does not use fuzzy legal-entity matching."
        ),
        handler=resolve_supplier_identity,
        required_args=("supplier_name",),
    )
)
registry.register(
    ToolSpec(
        name="verify_supplier_late_penalty",
        description=(
            "Deterministically verify whether a supplier has confirmed contract coverage "
            "and a late-delivery penalty/service-credit clause."
        ),
        handler=verify_supplier_late_penalty,
        required_args=("supplier_name",),
    )
)
registry.register(
    ToolSpec(
        name="run_combined_analysis",
        description=(
            "Run the existing deterministic combined workflow for questions that require BOTH "
            "operational data and contract evidence. Prefer this for multi-supplier combined questions."
        ),
        handler=run_combined_analysis,
        required_args=("question",),
    )
)
registry.register(
    ToolSpec(
        name="get_structured_schema",
        description="Return registered DuckDB tables and columns.",
        handler=get_structured_schema,
    )
)
registry.register(
    ToolSpec(
        name="get_dataset_catalog",
        description="Return uploaded structured dataset metadata.",
        handler=get_dataset_catalog,
    )
)
