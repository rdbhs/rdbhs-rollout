import unittest
from pathlib import Path

import duckdb
import yaml
from rollout.config import ModelConfig
from rollout.execution import ExecutionStatus, build_model_sql, execute_model
from rollout.models import Model, ModelId
from rollout.quality import run_dataset_quality_checks


class TreatmentPlanQualityTests(unittest.TestCase):
    def setUp(self):
        self.connection = duckdb.connect()
        self.addCleanup(self.connection.close)
        self.identity = ModelId('silver_treatment_plans', 'treatment_plans')
        path = Path(__file__).resolve().parents[1] / 'models/silver_treatment_plans/treatment_plans.yaml'
        self.config = ModelConfig.model_validate(yaml.safe_load(path.read_text()))
        self.connection.execute('''
            CREATE SCHEMA silver_treatment_plans;
            CREATE TABLE silver_treatment_plans.treatment_plans (
                end_date DATE, client_id BIGINT, client_full_name VARCHAR, version_number BIGINT
            )
        ''')

    def observations(self):
        return list(run_dataset_quality_checks(self.connection, self.identity, self.config.quality))

    def test_six_rules_and_individual_violations(self):
        self.connection.execute('''
            INSERT INTO silver_treatment_plans.treatment_plans VALUES
                (NULL, NULL, NULL, NULL),
                (DATE '1999-12-31', 1, '   ', 0),
                (DATE '2000-01-01', 1, ' Valid ', 1),
                (DATE '9999-01-01', 1, 'Valid', -1)
        ''')
        observations = self.observations()
        self.assertEqual([item.observed_value for item in observations], [1, 1, 1, 2, 3, 1])
        self.assertEqual([item.severity.value for item in observations], ['ERROR'] * 2 + ['WARNING'] * 4)
        self.assertEqual([item.status.value for item in observations], ['FAIL'] * 6)

    def test_years_0026_0027_are_warnings(self):
        self.connection.execute('''
            INSERT INTO silver_treatment_plans.treatment_plans VALUES
                (DATE '0026-01-01', 1, 'Valid', 1),
                (DATE '0026-12-31', 1, 'Valid', 1),
                (DATE '0027-01-01', 1, 'Valid', 2)
        ''')
        observations = self.observations()
        self.assertEqual([item.observed_value for item in observations], [0, 0, 3, 0, 0, 0])
        self.assertEqual(observations[2].severity.value, 'WARNING')

    def test_business_date_boundary_and_expired_plans(self):
        self.connection.execute('''
            INSERT INTO silver_treatment_plans.treatment_plans
            SELECT (timezone('America/New_York', current_timestamp)::DATE + INTERVAL '2 years')::DATE,
                1, 'Valid', 1;
            INSERT INTO silver_treatment_plans.treatment_plans VALUES
                (DATE '2000-01-01', 1, 'Valid', 1)
        ''')
        self.assertTrue(all(item.status.value == 'PASS' for item in self.observations()))
        self.connection.execute('''
            INSERT INTO silver_treatment_plans.treatment_plans
            SELECT (timezone('America/New_York', current_timestamp)::DATE + INTERVAL '2 years' + INTERVAL '1 day')::DATE,
                1, 'Valid', 1
        ''')
        self.assertEqual(self.observations()[-1].observed_value, 1)

    def test_error_rolls_back_warning_commits_and_source_is_unchanged(self):
        self.connection.execute('''
            INSERT INTO silver_treatment_plans.treatment_plans VALUES
                (DATE '2000-01-01', 99, 'Existing', 1);
            CREATE TABLE source AS
                SELECT DATE '0026-01-01' AS end_date, NULL::BIGINT AS client_id,
                    '' AS client_full_name, 0::BIGINT AS version_number
        ''')
        model = Model(self.identity, Path('treatment_plans.sql'), 'SELECT * FROM main.source', config=self.config)
        failed = execute_model(self.connection, model, build_model_sql(model))
        self.assertIs(failed.status, ExecutionStatus.FAILED)
        self.assertEqual(len(failed.quality_results), 6)
        self.assertEqual(self.connection.sql('SELECT client_id FROM silver_treatment_plans.treatment_plans').fetchall(), [(99,)])
        self.assertEqual(self.connection.sql('SELECT year(end_date) FROM source').fetchone(), (26,))
        self.connection.execute("UPDATE source SET client_id = 1")
        warning = execute_model(self.connection, model, build_model_sql(model))
        self.assertIs(warning.status, ExecutionStatus.SUCCESS)
        self.assertEqual([item.status.value for item in warning.quality_results], ['PASS', 'PASS', 'FAIL', 'FAIL', 'FAIL', 'PASS'])
        self.assertEqual(self.connection.sql('SELECT client_id FROM silver_treatment_plans.treatment_plans').fetchall(), [(1,)])
