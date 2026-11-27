"""Standalone service utilization PDF using the annual Gold snapshot."""

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


def _load_utilization(year, utilization_threshold=0.5):
    _validate_threshold(utilization_threshold)
    query = (Path(__file__).resolve().parent / "queries" / "utilization_above_threshold.sql").read_text(
        encoding="utf-8"
    )
    with closing(
        duckdb.connect(str(EngineConfig().warehouse_path), read_only=True)
    ) as connection:
        return connection.execute(
            query,
            [year, utilization_threshold],
        ).fetchall()


def multi_group_rows(rows):
    """Select distinct multi-group identities from the already filtered details."""
    clients = {}
    for row in rows:
        client_id = row[6]
        if client_id is not None:
            clients.setdefault(client_id, []).append(row)
    selected = [
        client_rows for client_rows in clients.values()
        if len({row[1] for row in client_rows if row[1] is not None}) > 1
    ]
    selected.sort(key=lambda client_rows: (
        (client_rows[0][0] or "").casefold(), client_rows[0][6]
    ))
    return [row for client_rows in selected
            for row in sorted(client_rows, key=lambda row: (-row[5], row[1] or ""))]


def generate_report(
    report_date: date | None = None,
    output_dir: Path = Path("."),
    utilization_threshold: float = 0.5,
    year: int | None = None,
) -> Path:
    """Write a private PDF. report_date labels generation, not a historical cutoff."""
    today = datetime.now(ZoneInfo("America/New_York")).date()
    year = today.year if year is None else year
    report_date = report_date or today
    _validate_threshold(utilization_threshold)
    rows = _load_utilization(year, utilization_threshold)
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
        paragraph(f"Reporting Year: {year}    |    Utilization Threshold: > {threshold_label}"),
        Spacer(1, styles["BodyText"].leading),
        Paragraph("Utilization Details", styles["Heading2"]),
    ]

    def detail_table(detail_rows):
        data = [[Paragraph(escape(label), styles["TableHeader"])
                 for label in ("Client", "Service Group", "Usage", "Limit", "Utilization %")]]
        data += [
            [paragraph(name), paragraph(group), quantity(usage, unit),
             quantity(limit, unit), paragraph(f"{utilization:.2%}")]
            for name, group, usage, unit, limit, utilization, _client_id in detail_rows
        ]
        table = LongTable(
            data, colWidths=[150, 105, 90, 85, 90], repeatRows=1, splitInRow=1
        )
        for row in data[1:]:
            for cell in row[2:]:
                cell.style = cell.style.clone("Numeric", alignment=2)
        table.setStyle(table_style())
        return table

    if not rows:
        story.append(
            paragraph(f"No service utilization records exceed {threshold_label}.")
        )
    else:
        story.append(detail_table(rows))
    multi_group = multi_group_rows(rows)
    if multi_group:
        story.extend([
            Spacer(1, styles["BodyText"].leading),
            Paragraph("Clients with Multiple Service Groups", styles["Heading2"]),
            detail_table(multi_group),
        ])
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
    parser.add_argument("--year", type=int, help="Reporting year; defaults to the current year in America/New_York.")
    args = parser.parse_args()
    generate_report(args.report_date, args.output_dir, year=args.year)
