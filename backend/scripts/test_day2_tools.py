import json
from app.tools.registry import registry


print(json.dumps(registry.schemas(), indent=2))
print("\n--- DATA TOOL TEST ---")
print(json.dumps(
    registry.execute(
        "query_operational_data",
        {"question": "Which purchase orders are open?"},
    ),
    indent=2,
    default=str,
))
