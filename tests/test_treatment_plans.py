import tempfile
import unittest
from pathlib import Path

import duckdb
from rollout.config import EngineConfig
from rollout.dag import build_dag
from rollout.discovery import discover_models
from rollout.execution import ExecutionStatus, execute_models
from rollout.models import ModelId
from rollout.parser import parse_models


class TreatmentPlanTests(unittest.TestCase):
    def test_validity_filters_preserve_columns_and_multiple_versions(self):
        identity = ModelId('silver_treatment_plans', 'treatment_plans')
        root = Path(__file__).resolve().parents[1]
        models = [model for model in discover_models(root / 'models') if model.id == identity]
        dag = build_dag(parse_models(models))
        self.assertEqual(dag.external_nodes, {ModelId('bronze', 'alleva_treatment_plans')})
        with tempfile.TemporaryDirectory() as directory:
            config = EngineConfig(warehouse_path=Path(directory) / 'warehouse.duckdb')
            with duckdb.connect(str(config.warehouse_path)) as connection:
                connection.execute('''
                    CREATE SCHEMA bronze;
                    CREATE TABLE bronze.alleva_treatment_plans (
                        system_lead_id BIGINT, full_name VARCHAR,
                        all_primary_clinicians VARCHAR, end_date DATE,
                        length_of_program BIGINT, version_no BIGINT,
                        is_active BOOLEAN, is_complete BOOLEAN, is_deleted BOOLEAN,
                        is_client BOOLEAN, lead_is_deleted BOOLEAN, lead_status VARCHAR
                    )
                ''')
                valid = [1, 'Test client', 'Test clinician', '2000-01-01', 30, 1,
                         True, True, False, True, False, 'ACTIVE']
                rows = [valid, valid.copy(), valid.copy()]
                rows[-1][5] = 2
                # Reject each failed or unknown predicate, independently.
                for column, invalid in ((9, False), (10, True), (11, 'INACTIVE'),
                                        (6, False), (7, False), (8, True)):
                    for value in (invalid, None):
                        row = valid.copy()
                        row[column] = value
                        rows.append(row)
                connection.executemany(
                    'INSERT INTO bronze.alleva_treatment_plans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    rows,
                )
            results = execute_models(dag, config, run_id='treatment-plans-test')
            self.assertIs(results[identity].status, ExecutionStatus.SUCCESS)
            with duckdb.connect(str(config.warehouse_path)) as connection:
                self.assertEqual(connection.sql('SELECT count(*) FROM silver_treatment_plans.treatment_plans').fetchone(), (3,))
                self.assertEqual(connection.sql('SELECT version_number, count(*) FROM silver_treatment_plans.treatment_plans GROUP BY ALL ORDER BY version_number').fetchall(), [(1, 2), (2, 1)])
                self.assertEqual(connection.sql("SELECT table_type FROM information_schema.tables WHERE table_schema = 'silver_treatment_plans' AND table_name = 'treatment_plans'").fetchone(), ('BASE TABLE',))
                self.assertEqual(
                    connection.sql('DESCRIBE silver_treatment_plans.treatment_plans').fetchall(),
                    connection.sql('DESCRIBE (SELECT system_lead_id AS client_id, full_name AS client_full_name, all_primary_clinicians, end_date, length_of_program, version_no AS version_number, is_active, is_complete, is_deleted, is_client, lead_is_deleted, lead_status FROM bronze.alleva_treatment_plans)').fetchall(),
                )
                self.assertEqual(connection.sql('SELECT count(*) FROM bronze.alleva_treatment_plans').fetchone(), (15,))
