"""Shared ReportLab presentation only; no report data or business rules."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import TableStyle

GREEN = colors.HexColor("#53C43B")
TEXT = colors.HexColor("#2F3542")
SECONDARY = colors.HexColor("#6B7280")
HEADER = colors.HexColor("#F1F3F5")
STRIPE = colors.HexColor("#F8F9FA")
BORDER = colors.HexColor("#E2E8F0")
LOGO = Path(__file__).resolve().parent / "assets" / "rdbhs-green-logo.png"


def report_styles():
    styles = getSampleStyleSheet()
    for name in ("Title", "Heading2", "BodyText"):
        styles[name].fontName = "Helvetica-Bold" if name != "BodyText" else "Helvetica"
        styles[name].textColor = TEXT
    styles["Title"].fontSize = 18
    styles["Title"].leading = 22
    styles["Title"].alignment = 0
    styles["Heading2"].fontSize = 12
    styles["Heading2"].leading = 16
    styles["Heading2"].spaceBefore = 12
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 12
    styles["BodyText"].splitLongWords = 1
    for name, size, font in [
        ("TableHeader", 9, "Helvetica-Bold"),
        ("MetricValue", 18, "Helvetica-Bold"),
        ("MetricLabel", 8, "Helvetica"),
    ]:
        styles.add(
            ParagraphStyle(
                name,
                parent=styles["BodyText"],
                fontName=font,
                fontSize=size,
                leading=size + 4,
            )
        )
    styles["MetricLabel"].textColor = SECONDARY
    return styles


def table_style():
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), HEADER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, STRIPE]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]
    )


def page_decoration(title, report_date, date_label="Reference Date"):
    """Return a canvas callback for every page of one report."""

    def draw(canvas, doc):
        canvas.saveState()
        width, height = doc.pagesize
        if LOGO.is_file():
            canvas.drawImage(
                str(LOGO),
                46,
                height - 55,
                width=135,
                height=44,
                preserveAspectRatio=True,
                mask="auto",
            )
        else:
            canvas.setFont("Helvetica-Bold", 10)
            canvas.setFillColor(TEXT)
            canvas.drawString(46, height - 35, "Right Direction BHS")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(SECONDARY)
        canvas.drawRightString(width - 46, height - 34, title)
        canvas.drawRightString(
            width - 46, height - 47, f"{date_label}: {report_date:%m/%d/%Y}"
        )
        canvas.setStrokeColor(GREEN)
        canvas.line(46, height - 62, width - 46, height - 62)
        canvas.setStrokeColor(BORDER)
        canvas.line(46, 39, width - 46, 39)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(
            46, 26, "Right Direction Behavioral Health Services | Confidential"
        )
        canvas.drawRightString(width - 46, 26, f"Page {doc.page}")
        canvas.restoreState()

    return draw
