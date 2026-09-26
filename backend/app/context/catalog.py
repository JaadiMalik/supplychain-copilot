from app.analytics.dataset_service import get_database_schema
from app.analytics.duckdb_service import get_connection
from app.analytics.supplier_service import (
    list_supplier_aliases,
    resolve_supplier,
)


SUPPLIER_COLUMN_NAMES = {
    "supplier",
    "supplier_name",
    "suppliername",
    "vendor",
    "vendor_name",
    "vendorname",
    "supplier_company",
    "vendor_company",
}


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def get_known_suppliers(max_values_per_column: int = 500) -> list[dict]:
    """Build a supplier catalog from explicit aliases and DuckDB values."""
    by_key: dict[str, dict] = {}

    for item in list_supplier_aliases():
        alias = (item.get("alias_name") or "").strip()
        canonical = (item.get("canonical_name") or "").strip()

        if alias:
            by_key[alias.casefold()] = {
                "name": alias,
                "canonical_name": canonical or alias,
                "source": "alias_registry",
                "alias_resolved": bool(canonical),
            }

        if canonical:
            by_key.setdefault(
                canonical.casefold(),
                {
                    "name": canonical,
                    "canonical_name": canonical,
                    "source": "alias_registry",
                    "alias_resolved": True,
                },
            )

    connection = get_connection()
    try:
        for table in get_database_schema():
            table_name = table.get("table_name")
            if not table_name:
                continue

            for column in table.get("columns", []):
                column_name = str(column.get("name", "")).strip()
                if column_name.casefold() not in SUPPLIER_COLUMN_NAMES:
                    continue

                query = f"""
                    SELECT DISTINCT CAST({_quote_identifier(column_name)} AS VARCHAR)
                    FROM {_quote_identifier(table_name)}
                    WHERE {_quote_identifier(column_name)} IS NOT NULL
                      AND TRIM(CAST({_quote_identifier(column_name)} AS VARCHAR)) <> ''
                    LIMIT {int(max_values_per_column)}
                """

                try:
                    rows = connection.execute(query).fetchall()
                except Exception:
                    continue

                for row in rows:
                    raw_name = str(row[0]).strip()
                    if not raw_name:
                        continue
                    resolved = resolve_supplier(raw_name)
                    by_key.setdefault(
                        raw_name.casefold(),
                        {
                            "name": raw_name,
                            "canonical_name": resolved.get("canonical_name", raw_name),
                            "source": f"dataset:{table_name}.{column_name}",
                            "alias_resolved": bool(resolved.get("alias_resolved")),
                        },
                    )
    finally:
        connection.close()

    return sorted(by_key.values(), key=lambda item: len(item["name"]), reverse=True)
