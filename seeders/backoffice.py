import os
from pathlib import Path

import duckdb
import yaml
from dotenv import load_dotenv
from rollout.config import SeederConfig


def run(
    connection: duckdb.DuckDBPyConnection,
    staging_dir: Path,
) -> dict[str, duckdb.DuckDBPyRelation]:
    seeder_path = Path(__file__)
    queries_path = seeder_path.parent / "backoffice_queries"

    load_dotenv(seeder_path.parent.parent / ".env", override=False)
    url = os.environ.get("BACKOFFICE_DATABASE_URL", "").strip()
    if not url:
        raise ValueError("BACKOFFICE_DATABASE_URL must be configured")

    try:
        connection.execute("LOAD postgres")
        connection.execute("DETACH DATABASE IF EXISTS backoffice_source")
        escaped_url = url.replace("'", "''")
        connection.execute(
            f"ATTACH '{escaped_url}' AS backoffice_source (TYPE postgres, READ_ONLY)"
        )
    except duckdb.Error:
        raise RuntimeError(
            "Cannot connect to Backoffice PostgreSQL in read-only mode"
        ) from None

    config = SeederConfig.model_validate(
        yaml.safe_load(seeder_path.with_suffix(".yaml").read_text())
    )

    results = {}
    for output in config.outputs:
        query = queries_path / f"{output.removeprefix('backoffice_')}.sql"
        sql = query.read_text()
        try:
            results[output] = connection.sql(sql)
        except duckdb.Error:
            raise RuntimeError(
                f"Backoffice query failed for output {output!r}"
            ) from None

    return results
