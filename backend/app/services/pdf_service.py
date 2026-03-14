"""PDF report generation - real export."""
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generate_daily_pdf(data: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("FocusAI PRO MONITOR", styles["Title"]))
    story.append(Paragraph("Daily Summary Report", styles["Heading1"]))
    story.append(Paragraph(datetime.now().strftime("%A, %B %d, %Y"), styles["Normal"]))
    story.append(Spacer(1, 20))

    rows = [
        ["Metric", "Value"],
        ["Focus Score", f"{data.get('focus_score', 0)}%"],
        ["Productivity Grade", data.get('productivity_grade', '-')],
        ["Work Mode", data.get('work_mode', '-')],
        ["Deep Work (productive time)", f"{data.get('productive_sec', 0) // 60} min"],
        ["Top App", data.get('top_app', '-')],
        ["Context Switches", str(data.get('switch_count', 0))],
        ["Distractions Flagged", str(data.get('distractions_count', 0))],
        ["Threats Detected", str(data.get('threats_count', 0))],
    ]
    t = Table(rows)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3fb950")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#161b22")),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Generated at {datetime.now().strftime('%H:%M:%S')}", styles["Normal"]))
    doc.build(story)
    return buf.getvalue()


def generate_weekly_pdf(data: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("FocusAI PRO MONITOR", styles["Title"]))
    story.append(Paragraph("Weekly AI Analysis", styles["Heading1"]))
    story.append(Paragraph(datetime.now().strftime("%A, %B %d, %Y"), styles["Normal"]))
    story.append(Spacer(1, 20))

    rows = [
        ["Metric", "Value"],
        ["Average Focus", f"{data.get('avg_focus', 0)}%"],
        ["Best Day", data.get('best_day', '-') or '-'],
        ["Recommendation", data.get('recommendation', '-')],
    ]
    t = Table(rows)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#a371f7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#161b22")),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Generated at {datetime.now().strftime('%H:%M:%S')}", styles["Normal"]))
    doc.build(story)
    return buf.getvalue()
