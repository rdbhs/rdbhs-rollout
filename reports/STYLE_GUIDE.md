# RDBHS Report Visual Style Guide

Shared presentation lives in `reports/style.py`. Queries, business rules, and
orchestration stay in their current modules. The visual style adds no dependencies.

## Identity

Use only the official Right Direction Behavioral Health Services logo.
The original asset is preserved at `reports/assets/rdbhs-green-logo.png`.
Its path is resolved from `Path(__file__).resolve()` independently of the working
directory. Place it at the top left in a 135 × 44 pt box, preserving the aspect
ratio and original transparency. If the file is missing, display the
organization name.

Every page header includes the short title and reference date. The opening
body contains the full title and original metadata. In Utilization, the date
indicates when the report was generated. It does not indicate a historical cutoff
or how current the Gold data is. The footer includes the full organization name,
`Confidential`, and `Page N`.

## Palette

These proposed colors are based on the RDBHS visual identity and have no official
certification.

| Element | Color |
|---|---|
| Corporate green | `#53C43B` |
| Primary text | `#2F3542` |
| Secondary text | `#6B7280` |
| Table header | `#F1F3F5` |
| Alternating rows | `#F8F9FA` |
| Borders and dividers | `#E2E8F0` |
| Background | `#FFFFFF` |

## Typography and Layout

Use Helvetica and Helvetica-Bold, both built into ReportLab, with no external
font assets. Use 18/22 pt for titles, 9/12 pt for metadata and table body,
12/16 pt for section headings, and 9/12 pt for table headers. Use 8 pt for the
running header and 7 pt for the footer.
Use Letter paper with uniform 46 pt side margins. Reserve 78 pt at the top and
52 pt at the bottom to prevent overlap with the header and footer. Top-align table
cells with 7 pt vertical padding. Use 16 pt of initial spacing.

## Rules

Use a white background, dark text, and green only as an accent on the top
divider. Use light gray table headers, subtle borders, and alternating white and
very light gray rows. Avoid shadows, gradients, and extra decoration. Apply
semantic colors only when an explicit business rule calls for them.

Tables use `LongTable`, repeat their first row on each page, and allow
exceptionally tall rows to split. Escape text as literal content, preserve line
breaks, and wrap long words to fit the cell. Never truncate or reduce data or
change units to make content fit. Preserve the existing fallbacks. Treatment
Plans uses `Not available` and uses `Not assigned` for a null Case Manager.
Utilization uses `Not available` for null values and preserves empty strings.
Sections with no records retain their current messages.

## Validation

Run `python -m unittest discover -s tests`. For automated tests, generate
synthetic samples with the test dates (2026-01-01 and 2026-11-17), compare values
with the previous version, and inspect all rendered pages. Check repeated
headers, long text, page breaks, and footers. Generate PDFs with private
permissions and keep patient information out of logs.

### Review with the Existing Warehouse (2026-11-17)

The generators used their `read_only=True` connections. Seeders and data updates
were outside the scope of the review. The private samples for manual review are
`temp/treatment_2026-11-17_final.pdf` (15 records, 9 and 6 in the two windows, one
page) and `temp/utilization_2026-11-17_final.pdf` (118 records, six pages).

An ordered comparison against the original generators found that every cell was
identical. Text extraction also confirmed matching numeric values, excluding
the new header date and page numbers. The seven rendered pages were inspected.
The logo retained its proportions, the five columns and repeated headers were
present, and footers, null values, and long names showed no clipping or overlap.
The last Utilization page contains four rows. The six Treatment Plans pages
from the earlier review came from a synthetic sample.

All six report-specific tests passed in that review. Previously observed
failures in the full suite were unrelated to styling. Two Alleva tests expected
six outputs while their configuration contained seven. Another called
`execute_seeder` without `project_dir`. The Treatment Plans model test expected
one external dependency while the model also queried the Case Managers relation.
Those components were outside the scope of the review, as were pipeline runs.
The design was pending manual approval.

## Current Review Conventions

Present findings first, followed by the details readers need to investigate them.
Use `Upcoming Treatment Plans` and `Utilization Report` as the titles in both
the body and running header. Omit the redundant organization name from the body.
`Reference Date` identifies the Treatment Plans cutoff date. `Generation Date`
identifies when the report was generated. `Reporting Period` identifies the
span of service dates. Use MM/DD/YYYY for all visible dates. Omit technical
metadata about Gold, the warehouse, and the time zone. Preserve the internal
date logic.

Use bold table headers, left-aligned text, and right-aligned numbers. Emphasize
indicator values with understated labels and no cards. Preserve the margins,
logo, neutral palette, and footer. Use green only as a corporate accent. Keep
dates in their original column.

### Utilization Limitations

`utilization_threshold` is optional and defaults to 0.5. It must be finite and
nonnegative and can exceed 1. Use the strict, parameterized SQL comparison
`>`. Gold already filters on `utilization >= 0.3`. Thresholds below 0.3
cannot recover records filtered out by the model. Preserve the model and period.

Gold groups by name and exposes no stable identifier. The user deferred
client-level indicators and the multiple-service-group section. `Summary`
explicitly counts records, including those that reach 100% using `>= 1`,
without assigning unique identities or clinical meaning. The temporary
calculation lives in `utilization_summary`, outside `style.py`. The warehouse
should eventually provide these analytical views as the single source of truth.

Omit `Utilization Since` because Gold does not expose the start date as queryable
data. Avoid duplicating the SQL literal or inferring the start date from the
first service record.
