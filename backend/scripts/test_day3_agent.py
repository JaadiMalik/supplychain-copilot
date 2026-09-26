import json
from app.agent.service import ask_v2


question = "Which open purchase orders belong to suppliers with contractual late-delivery penalties?"
print(json.dumps(ask_v2(question), indent=2, default=str))
