"""Standalone executive report; run from the repository root."""

import argparse
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

import duckdb
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)
from rollout.config import EngineConfig

from reports.style import page_decoration, report_styles, table_style


def _load_plans(report_date):
    query = (Path(__file__).resolve().parent / "queries" / "upcoming_treatment_plans.sql").read_text(
        encoding="utf-8"
    )
    with closing(
        duckdb.connect(str(EngineConfig().warehouse_path), read_only=True)
    ) as connection:
        return connection.execute(
            query,
            [report_date, report_date + timedelta(days=15)],
        ).fetchall()


def generate_report(
    report_date: date | None = None, output_dir: Path = Path(".")
) -> Path:
    """Query Silver with an independent read-only connection and write a private PDF."""
    report_date = report_date or datetime.now(ZoneInfo("America/New_York")).date()
    plans = _load_plans(report_date)
    groups = [
        [row for row in plans if low <= (row[3] - report_date).days <= high]
        for low, high in ((0, 7), (8, 15))
    ]
    styles = report_styles()
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 12
    styles["BodyText"].splitLongWords = 1

    def paragraph(value):
        return Paragraph(
            escape(str(value or "Not available")).replace("\n", "<br/>"),
            styles["BodyText"],
        )

    story = [
        Paragraph("Upcoming Treatment Plans", styles["Title"]),
        paragraph(f"Reference Date: {report_date:%m/%d/%Y}"),
        Spacer(1, 12),
    ]
    metrics = LongTable(
        [
            [
                Paragraph(str(value), styles["MetricValue"])
                for value in (len(plans), len(groups[0]), len(groups[1]))
            ],
            [
                Paragraph(label, styles["MetricLabel"])
                for label in (
                    "Total Expiring Plans",
                    "Expiring Within 7 Days",
                    "Expiring in 8–15 Days",
                )
            ],
        ],
        colWidths=[520 / 3] * 3,
    )
    story.extend([metrics, Spacer(1, 12)])
    if not plans:
        story.append(
            paragraph(
                "No treatment plans expire within the next 15 days (including the report date)."
            )
        )
    for title, rows in zip(("Expiring Within 7 Days", "Expiring in 8–15 Days"), groups):
        story.append(Paragraph(title, styles["Heading2"]))
        if not rows:
            story.append(paragraph("No treatment plans in this window."))
            continue
        data = [
            [
                Paragraph(escape(v), styles["TableHeader"])
                for v in (
                    "Client",
                    "Case Manager",
                    "Primary Clinician(s)",
                    "Expiration Date",
                    "Days Remaining",
                )
            ]
        ]
        data += [
            [
                paragraph(row[1]),
                paragraph(row[5] if row[5] is not None else "Not assigned"),
                paragraph(row[2]),
                paragraph(row[3].strftime("%m/%d/%Y")),
                paragraph(str((row[3] - report_date).days)),
            ]
            for row in rows
        ]
        table = LongTable(
            data, colWidths=[110, 120, 130, 86, 74], repeatRows=1, splitInRow=1
        )
        table.setStyle(table_style())
        for row in data[1:]:
            for cell in row[3:]:
                cell.style = cell.style.clone("Numeric", alignment=2)
        table.setStyle(TableStyle([("ALIGN", (3, 0), (-1, -1), "RIGHT")]))
        story.append(table)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Atomic exclusive creation, mode 0600 on POSIX; no intermediate PHI files.
    with NamedTemporaryFile(
        prefix=f"treatment_plans_{report_date.isoformat()}_",
        suffix=".pdf",
        dir=output_dir,
        delete=False,
    ) as output:
        path = Path(output.name)
        try:
            SimpleDocTemplate(
                output,
                pagesize=letter,
                rightMargin=46,
                leftMargin=46,
                topMargin=78,
                bottomMargin=52,
            ).build(
                story,
                onFirstPage=page_decoration("Upcoming Treatment Plans", report_date),
                onLaterPages=page_decoration("Upcoming Treatment Plans", report_date),
            )
        except BaseException:
            path.unlink(missing_ok=True)
            raise
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-date", type=date.fromisoformat)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    generate_report(args.report_date, args.output_dir)
