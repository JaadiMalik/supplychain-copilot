from app.memory.service import get_analysis
from app.reports.docx_service import build_docx
from app.reports.excel_service import build_excel
from app.reports.pdf_service import build_pdf


BUILDERS = {
    "pdf": build_pdf,
    "docx": build_docx,
    "xlsx": build_excel,
}


def generate_report(analysis_id: str, report_format: str):
    report_format = report_format.lower().strip()
    if report_format not in BUILDERS:
        raise ValueError("Supported report formats: pdf, docx, xlsx")
    analysis = get_analysis(analysis_id)
    if not analysis:
        raise LookupError("Analysis not found.")
    return BUILDERS[report_format](analysis)
