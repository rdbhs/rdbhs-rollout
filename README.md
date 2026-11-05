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
