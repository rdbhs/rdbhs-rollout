# RDBHS Warehouse Builder

Data warehouse pipeline for Right Direction Behavioral Health Services (RDBHS), powered by [Rollout](https://github.com/elcone/rollout) and DuckDB.

## Overview

The project extracts data from Alleva and the RDBHS Backoffice, then transforms it into analytics-ready datasets using SQL models organized into a dependency-aware DAG.

The resulting DuckDB warehouse serves as the data source for Apache Superset.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Rollout (local dependency)

## Setup

Clone `rollout` and `rdbhs-rollout` into the same parent directory:

```text
workspace/
├── rollout/
└── rdbhs-rollout/
```

Install dependencies:

```bash
cd rdbhs-rollout
uv sync --locked
```

Configure the required environment variables and credentials in `.env` and the secrets directory.

## Run

Execute the pipeline from the project root:

```bash
uv run rollout run
```

## Project Structure

```text
rdbhs-rollout/
├── models/              # SQL transformation models
├── seeders/             # Alleva and Backoffice extractors
├── backoffice_queries/  # Backoffice SQL queries
├── docs/                # Technical documentation
├── pyproject.toml
└── uv.lock
```

The warehouse is generated at `.rollout/warehouse.duckdb`.

## Time Zone

The pipeline runs on a UTC server. RDBHS business time follows `America/New_York`, including daylight saving time transitions.

## Treatment Plans Expiration Report

Run independently from the project root after `uv sync --locked`:

```bash
uv run python -m reports.treatment_plans --report-date 2026-11-17 --output-dir /secure/reports
```

Omit `--report-date` to use today's date in America/New_York. Python callers
can use `from reports.treatment_plans import generate_report` and call
`generate_report(report_date, Path('/secure/reports'))`.
The generator uses Rollout's `EngineConfig().warehouse_path`, opens its own
read-only connection, and closes it before rendering. It preserves all Silver
rows and versions in the inclusive 0–15 day window. ReportLab provides wrapped
text, repeated table headers and multipage PDF output without external services.
Each PDF has a unique filename and owner-only permissions on POSIX. The output
contains PHI: choose an appropriately secured directory and retention policy.
No delivery or orchestration is included.

## Service Utilization Report

```bash
uv run python -m reports.utilization --output-dir /secure/reports
```

Uses `gold_utilization.utilization` directly, selecting utilization strictly above
50%, in descending order. Hours and days remain separate on each row; no totals
combine them. The reference period is cumulative from 07/01/2026, matching the
current model, with no upper date bound. Optional `--report-date YYYY-MM-DD`
labels generation only and does not generate a historical snapshot. The default
is today's date in America/New_York. Python callers may use
`reports.utilization.generate_report(report_date, output_dir)`.
Like Treatment Plans, PDFs have unique filenames, private POSIX permissions and
contain PHI; use a secured destination. No new dependencies are required.
