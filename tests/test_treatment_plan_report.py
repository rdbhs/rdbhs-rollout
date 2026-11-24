from contextlib import chdir
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import duckdb
from rollout.config import EngineConfig
from reports import treatment_plans as report


class ReportTests(unittest.TestCase):
    def test_windows_order_versions_and_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = EngineConfig(warehouse_path=root / 'test.duckdb')
            day = date(2026, 1, 1)
            with duckdb.connect(str(config.warehouse_path)) as con:
                con.execute('CREATE SCHEMA silver_treatment_plans')
                con.execute('CREATE TABLE silver_treatment_plans.treatment_plans (client_id INT, client_full_name VARCHAR, all_primary_clinicians VARCHAR, end_date DATE, version_number INT, case_manager_full_name VARCHAR)')
                con.executemany('INSERT INTO silver_treatment_plans.treatment_plans VALUES (?, ?, ?, ?, ?, ?)',
                                [(1, name, 'Synthetic clinician ' * 15, day + timedelta(days=n), v, None if v == 2 else 'Synthetic manager one, Synthetic manager two')
                                 for n, name, v in [(15, 'Z', 1), (8, 'B', 1), (7, 'B', 1), (0, 'A', 1), (0, 'A', 2), (-1, 'X', 1), (16, 'X', 1)]])
            with chdir(root), patch.object(report, 'EngineConfig', return_value=config):
                rows = report._load_plans(day)
                self.assertIsNone(rows[1][5])
                self.assertEqual(rows[0][5], 'Synthetic manager one, Synthetic manager two')
                self.assertEqual([(r[3]-day).days for r in rows], [0, 0, 7, 8, 15])
                with patch.object(report, 'LongTable', wraps=report.LongTable) as table:
                    first = report.generate_report(day, root)
                    cells = [cell.getPlainText() for call in table.call_args_list
                             for row in call.args[0] for cell in row]
                    self.assertIn('Case Manager', cells)
                    self.assertIn('Not assigned', cells)
                    self.assertIn('Synthetic manager one, Synthetic manager two', cells)
                second = report.generate_report(day, root)
                self.assertNotEqual(first, second)
                self.assertTrue(first.read_bytes().startswith(b'%PDF-'))
                self.assertEqual(first.stat().st_mode & 0o777, 0o600)
                empty = report.generate_report(day + timedelta(days=100), root)
                self.assertTrue(empty.read_bytes().startswith(b'%PDF-'))
            with patch.object(report, '_load_plans', return_value=rows * 100):
                large = report.generate_report(day, root)
                self.assertGreater(large.read_bytes().count(b'/Type /Page'), 2)

    def test_connection_closed_on_success_and_failure(self):
        for fail in (False, True):
            connection = MagicMock()
            if fail:
                connection.execute.side_effect = RuntimeError('synthetic failure')
            else:
                connection.execute.return_value.fetchall.return_value = []
            with patch.object(report.duckdb, 'connect', return_value=connection) as connect:
                if fail:
                    with self.assertRaises(RuntimeError):
                        report._load_plans(date(2026, 1, 1))
                else:
                    report._load_plans(date(2026, 1, 1))
                self.assertTrue(connect.call_args.kwargs['read_only'])
                connection.close.assert_called_once()
