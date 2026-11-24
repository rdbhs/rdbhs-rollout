"""Standalone service utilization PDF using the current cumulative Gold snapshot."""

import argparse
import math
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

import duckdb
from reportlab.lib.pagesizes import letter
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer
from rollout.config import EngineConfig

from reports.style import page_decoration, report_styles, table_style


def _validate_threshold(value):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError("utilization_threshold must be a finite nonnegative number")
    return value


def _load_utilization(utilization_threshold=0.5):
    _validate_threshold(utilization_threshold)
    query = (Path(__file__).resolve().parent / "queries" / "utilization_above_threshold.sql").read_text(
        encoding="utf-8"
    )
    with closing(
        duckdb.connect(str(EngineConfig().warehouse_path), read_only=True)
    ) as connection:
        return connection.execute(
            query,
            [utilization_threshold],
        ).fetchall()


def utilization_summary(rows, threshold):
    """Temporary record-level summary; Gold does not preserve client identity."""
    label = f"{threshold * 100:g}%"
    if not rows:
        return f"No service utilization records exceed {label}."
    count = len(rows)
    reached = sum(row[-1] >= 1 for row in rows)
    noun = "record" if count == 1 else "records"
    verb = "exceeds" if count == 1 else "exceed"
    limit_noun = "record has" if reached == 1 else "records have"
    return (
        f"{count} service utilization {noun} {verb} {label} utilization. "
        f"Of these, {reached} {limit_noun} reached or exceeded 100% utilization."
    )


def generate_report(
    report_date: date | None = None,
    output_dir: Path = Path("."),
    utilization_threshold: float = 0.5,
) -> Path:
    """Write a private PDF. report_date labels generation, not a historical cutoff."""
    report_date = report_date or datetime.now(ZoneInfo("America/New_York")).date()
    _validate_threshold(utilization_threshold)
    rows = _load_utilization(utilization_threshold)
    styles = report_styles()

    def paragraph(value):
        text = "Not available" if value is None else str(value)
        return Paragraph(escape(text).replace("\n", "<br/>"), styles["BodyText"])

    def quantity(value, unit):
        label = {"HOURS": "hours", "DAYS": "days"}.get(unit, unit or "unit unavailable")
        return paragraph(f"{value:,.2f} {label}")

    threshold_label = f"{utilization_threshold * 100:g}%"
    story = [
        Paragraph("Utilization Report", styles["Title"]),
        paragraph(f"Generation Date: {report_date:%m/%d/%Y}"),
        Paragraph("Summary", styles["Heading2"]),
        paragraph(utilization_summary(rows, utilization_threshold)),
        Spacer(1, 16),
        Paragraph("Utilization Details", styles["Heading2"]),
    ]
    if not rows:
        story.append(
            paragraph(f"No service utilization records exceed {threshold_label}.")
        )
    else:
        data = [
            [
                Paragraph(escape(v), styles["TableHeader"])
                for v in ("Client", "Service Group", "Usage", "Limit", "Utilization %")
            ]
        ]
        data += [
            [
                paragraph(name),
                paragraph(group),
                quantity(usage, unit),
                quantity(limit, unit),
                paragraph(f"{utilization:.2%}"),
            ]
            for name, group, usage, unit, limit, utilization in rows
        ]
        table = LongTable(
            data, colWidths=[150, 105, 90, 85, 90], repeatRows=1, splitInRow=1
        )
        for row in data[1:]:
            for cell in row[2:]:
                cell.style = cell.style.clone("Numeric", alignment=2)
        table.setStyle(table_style())
        story.append(table)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        prefix=f"utilization_{report_date.isoformat()}_",
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
                onFirstPage=page_decoration(
                    "Utilization Report", report_date, "Generation Date"
                ),
                onLaterPages=page_decoration(
                    "Utilization Report", report_date, "Generation Date"
                ),
            )
        except BaseException:
            path.unlink(missing_ok=True)
            raise
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-date",
        type=date.fromisoformat,
        help="Generation label only; does not filter the Gold snapshot.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    generate_report(args.report_date, args.output_dir)
