from app.analytics.duckdb_service import (
    load_inventory_csv,
    get_inventory_preview,
    get_items_below_reorder,
)


CSV_PATH = "data/structured/inventory.csv"


load_inventory_csv(CSV_PATH)


print("\nINVENTORY PREVIEW")
print("=" * 70)

print(get_inventory_preview())


print("\nITEMS BELOW REORDER LEVEL")
print("=" * 70)

print(get_items_below_reorder())