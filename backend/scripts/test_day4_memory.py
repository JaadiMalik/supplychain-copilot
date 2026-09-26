import json
from app.memory.service import (
    get_relevant_corrections,
    list_corrections,
    remember_correction,
)


created = remember_correction(
    correction_type="terminology",
    key="GRN",
    value="goods receipt note",
    note="Training test",
)
print("CREATED")
print(json.dumps(created, indent=2))
print("\nRELEVANT")
print(json.dumps(get_relevant_corrections("Show GRN status"), indent=2))
print("\nALL")
print(json.dumps(list_corrections(), indent=2))
