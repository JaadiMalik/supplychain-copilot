from app.analytics.supplier_service import add_supplier_alias


result = add_supplier_alias(
    alias_name="Atlas Industrial",
    canonical_name="Atlas Industrial Supplies Ltd.",
)

print(result)