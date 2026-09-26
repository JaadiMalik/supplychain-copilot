from app.agent.service import ask_v2
from app.reports.service import generate_report


result = ask_v2("Which purchase orders are open?")
analysis_id = result["analysis_id"]
print("Analysis:", analysis_id)
for fmt in ("pdf", "docx", "xlsx"):
    path = generate_report(analysis_id, fmt)
    print(fmt.upper(), path)
