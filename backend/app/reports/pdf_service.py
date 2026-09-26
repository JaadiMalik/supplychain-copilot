from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.reports.common import answer_text, report_path, trace_rows


def build_pdf(analysis: dict):
    path = report_path(analysis["analysis_id"], "pdf")
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    story = [
        Paragraph("SupplyChain Copilot Analysis", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Analysis ID: {analysis['analysis_id']}", styles["BodyText"]),
        Paragraph(f"Created: {analysis.get('created_at', '')}", styles["BodyText"]),
        Spacer(1, 10),
        Paragraph("Question", styles["Heading2"]),
        Paragraph(analysis.get("question", ""), styles["BodyText"]),
        Spacer(1, 10),
        Paragraph("Answer", styles["Heading2"]),
        Paragraph(answer_text(analysis).replace("\n", "<br/>") or "No answer.", styles["BodyText"]),
        Spacer(1, 10),
        Paragraph("Agent Steps", styles["Heading2"]),
    ]

    rows = [["Round", "Tool", "Status", "Reason"]]
    for item in trace_rows(analysis):
        rows.append([
            str(item["round"] or ""),
            str(item["tool"] or ""),
            str(item["status"] or ""),
            str(item["planner_reason"] or "")[:120],
        ])
    if len(rows) == 1:
        rows.append(["-", "No tool calls", "-", "-"])

    table = Table(rows, repeatRows=1, colWidths=[16*mm, 42*mm, 24*mm, 90*mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, "#888888"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    doc.build(story)
    return path
