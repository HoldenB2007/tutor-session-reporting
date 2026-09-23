"""Render a report dict (from queries.build_report) to PDF bytes with ReportLab."""

import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

COLUMNS = {
    "tutor": [
        ("Tutor", "tutor"), ("Students", "students"), ("Active", "active_students"),
        ("Hours", "hours"), ("Sessions", "sessions"), ("Absences", "absences"), ("Goals", "goals"),
    ],
    "assignment": [
        ("Tutor", "tutor"), ("Student", "student"), ("Subject", "subject"), ("Site", "site"),
        ("Hours", "hours"), ("Sessions", "sessions"), ("TA", "tutor_absent"), ("SA", "student_absent"),
        ("H", "holidays"), ("Goals achieved", "goals"), ("Status", "status"),
    ],
    "session": [("Date", "date"), ("Tutor", "tutor"), ("Hours", "hours"), ("Absence", "absence"), ("Note", "note")],
}


def _cell(value):
    if isinstance(value, list):
        return "\n".join(value) if value else "—"
    if isinstance(value, datetime.date):
        return value.strftime("%b %-d, %Y")
    if value is None or value == "":
        return "—"
    return str(value)


def _session_detail_flowables(groups, styles, body):
    """Tutor → student → dated session rows, mirroring the paper form's per-student grid."""
    if not groups:
        return [Paragraph("No sessions in this period.", body), Spacer(1, 8)]
    out = []
    grid = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])
    for g in groups:
        out.append(Paragraph(f"{g['tutor']} — {g['hours']} h", styles["Heading4"]))
        for sg in g["students"]:
            out.append(Paragraph(f"<b>{sg['student']}</b> · {sg['subject']} — {sg['hours']} h, {len(sg['rows'])} dates", body))
            data = [["Date", "Hours", "Absence", "Note"]] + [
                [_cell(r["date"]), _cell(r["hours"]), _cell(r["absence"]), Paragraph(_cell(r["note"]), body)]
                for r in sg["rows"]
            ]
            table = Table(data, repeatRows=1, colWidths=[1.4 * inch, 0.7 * inch, 1.2 * inch, None], hAlign="LEFT")
            table.setStyle(grid)
            out.extend([table, Spacer(1, 6)])
        out.append(Spacer(1, 8))
    return out


def render_pdf(report):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(letter), leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
        title=f"LVAEP {report['title']} — {report['period']}",
    )
    styles = getSampleStyleSheet()
    body = styles["BodyText"]
    body.fontSize = 8
    body.leading = 10

    story = [
        Paragraph("Literacy Volunteers of America, Essex/Passaic County", styles["Title"]),
        Paragraph(f"{report['title']} — {report['period']}", styles["Heading2"]),
        Paragraph(f"Generated {datetime.datetime.now():%b %-d, %Y %-I:%M %p}", body),
        Spacer(1, 12),
    ]

    for section in report["sections"]:
        story.append(Paragraph(section["heading"], styles["Heading3"]))
        if section["columns"] == "session_detail":
            story.extend(_session_detail_flowables(section["groups"], styles, body))
            continue
        cols = COLUMNS[section["columns"]]
        if not section["rows"]:
            story.append(Paragraph("No data in this period.", body))
            story.append(Spacer(1, 8))
            continue
        data = [[c[0] for c in cols]]
        for row in section["rows"]:
            data.append([Paragraph(_cell(row[key]), body) for _, key in cols])
        if section.get("totals"):
            t = section["totals"]
            totals_row = {key: "" for _, key in cols}
            totals_row.update({cols[0][1]: "Total", "hours": t["hours"], "sessions": t["sessions"],
                               "tutor_absent": t["tutor_absent"], "student_absent": t["student_absent"],
                               "holidays": t["holidays"], "goals": f"{t['goals']} achieved"})
            data.append([Paragraph(f"<b>{_cell(totals_row[key])}</b>", body) for _, key in cols])
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dddddd")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    doc.build(story)
    return buf.getvalue()
