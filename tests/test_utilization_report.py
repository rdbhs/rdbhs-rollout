import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import duckdb
from rollout.config import EngineConfig
from reports import utilization as report


class UtilizationTests(unittest.TestCase):
    def test_gold_threshold_units_order_and_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = EngineConfig(warehouse_path=root / 'synthetic.duckdb')
            with duckdb.connect(str(config.warehouse_path)) as con:
                con.execute('CREATE SCHEMA gold_utilization')
                con.execute('''CREATE TABLE gold_utilization.utilization (
                    client_full_name VARCHAR, service_code_group VARCHAR, usage DOUBLE,
                    usage_unit VARCHAR, usage_limit INTEGER, utilization DOUBLE, payment_basis VARCHAR)''')
                con.executemany('INSERT INTO gold_utilization.utilization VALUES (?, ?, ?, ?, ?, ?, ?)', [
                    ('Synthetic A', 'H', 25, 'HOURS', 50, .5, 'PER_UNIT'),
                    ('Synthetic B', 'H', 24, 'HOURS', 50, .48, 'PER_UNIT'),
                    ('Synthetic C', 'H', 26, 'HOURS', 50, .52, 'PER_UNIT'),
                    ('Synthetic C', 'D', 18, 'DAYS', 30, .6, 'PER_DIEM'),
                    # Deliberately not usage/limit: ensure the report trusts Gold.
                    ('Synthetic D', 'H', 1, 'HOURS', 50, .8, 'PER_UNIT')])
            with contextlib.chdir(root), patch.object(report, 'EngineConfig', return_value=config):
                rows = report._load_utilization()
                self.assertEqual([r[-1] for r in rows], [.8, .6, .52])
                self.assertEqual([r[3] for r in rows], ['HOURS', 'DAYS', 'HOURS'])
                self.assertEqual(rows[0][2], 1)
                output = io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    path = report.generate_report(date(2026, 11, 17), root)
                self.assertEqual(output.getvalue(), '')
                self.assertTrue(path.read_bytes().startswith(b'%PDF-'))
                if os.name == 'posix':
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                text = subprocess.check_output(['pdftotext', str(path), '-'], text=True)
                for expected in ('3 service utilization records exceed 50% utilization.', '18.00 days', '30.00 days', '1.00 hours', '80.00%'):
                    self.assertIn(expected, text)
                self.assertNotEqual(path, report.generate_report(output_dir=root))
            with patch.object(report, '_load_utilization', return_value=[]):
                empty = report.generate_report(output_dir=root)
                self.assertIn('No service utilization records exceed 50%.', subprocess.check_output(['pdftotext', str(empty), '-'], text=True))
            long_row = ('Synthetic long client name ' * 10, 'Synthetic group', 26, 'HOURS', 50, .52)
            with patch.object(report, '_load_utilization', return_value=[long_row] * 90):
                large = report.generate_report(output_dir=root)
                pages = subprocess.check_output(['pdftotext', str(large), '-'], text=True).split('\f')
                nonempty = [p for p in pages if p.strip()]
                self.assertGreater(len(nonempty), 1)
                self.assertTrue(all('Service Group' in p for p in nonempty))

    def test_connection_lifecycle(self):
        for failure in (False, True):
            connection = MagicMock()
            if failure:
                connection.execute.side_effect = RuntimeError('synthetic')
            else:
                connection.execute.return_value.fetchall.return_value = []
            with patch.object(report.duckdb, 'connect', return_value=connection) as connect:
                if failure:
                    with self.assertRaises(RuntimeError):
                        report._load_utilization()
                else:
                    self.assertEqual(report._load_utilization(), [])
                self.assertTrue(connect.call_args.kwargs['read_only'])
                connection.close.assert_called_once()

    def test_standalone_cli(self):
        import sys
        result = subprocess.run([sys.executable, '-m', 'reports.utilization', '--help'], capture_output=True)
        self.assertEqual(result.returncode, 0)

    def test_render_failure_removes_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(report, '_load_utilization', return_value=[]), patch.object(report.SimpleDocTemplate, 'build', side_effect=RuntimeError('synthetic')):
            with self.assertRaises(RuntimeError):
                report.generate_report(output_dir=Path(directory))
            self.assertEqual(list(Path(directory).iterdir()), [])


class ThresholdTests(unittest.TestCase):
    def test_validation(self):
        for value in (-1, float('nan'), float('inf'), True, '0.5'):
            with self.assertRaises(ValueError):
                report.generate_report(utilization_threshold=value)
        for value in (0, .5, 1, 1.5):
            self.assertEqual(report._validate_threshold(value), value)

    def test_parameterized_strict_threshold(self):
        connection = MagicMock()
        with patch.object(report.duckdb, 'connect', return_value=connection):
            report._load_utilization(1.25)
        sql, params = connection.execute.call_args.args
        self.assertIn('utilization > ?', sql)
        self.assertEqual(params, [1.25])


    def test_record_summary_limit_and_empty(self):
        rows = [('Same name', 'H', 1, 'HOURS', 1, value) for value in (.51, 1, 1.2)]
        self.assertIn('2 records have reached or exceeded 100%', report.utilization_summary(rows, .5))
        self.assertIn('1 service utilization record exceeds', report.utilization_summary(rows[:1], .5))
        self.assertEqual(report.utilization_summary([], 1.25), 'No service utilization records exceed 125%.')
