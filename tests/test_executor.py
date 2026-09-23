from pathlib import Path
import shutil
import unittest

import duckdb

from executor import database_path_for_manifest, execute_manifest


FIXTURES = Path(__file__).parent / "fixtures"


class ExecutorTests(unittest.TestCase):
    def tearDown(self):
        artifacts = FIXTURES / "artifacts"
        if artifacts.exists():
            shutil.rmtree(artifacts)

    def test_valid_manifest_completes_all_steps(self):
        manifest = FIXTURES / "valid_manifest.csv"
        outcome = execute_manifest(manifest)

        self.assertEqual([], outcome.validation_issues)
        self.assertIsNone(outcome.execution_issue)
        self.assertEqual(3, len(outcome.results))
        self.assertTrue(all(r.status == "completed" for r in outcome.results))

        database_path = database_path_for_manifest(manifest)
        self.assertTrue(database_path.exists())

    def test_invalid_manifest_never_starts_execution(self):
        outcome = execute_manifest(FIXTURES / "invalid_manifest.csv")

        self.assertEqual([], outcome.results)
        self.assertTrue(outcome.validation_issues)
        self.assertIsNone(outcome.execution_issue)

    def test_execution_stops_at_first_runtime_failure(self):
        outcome = execute_manifest(FIXTURES / "failing_manifest.csv")

        self.assertEqual([], outcome.validation_issues)
        self.assertIsNotNone(outcome.execution_issue)
        self.assertEqual(1, len(outcome.results))
        self.assertEqual("2", outcome.execution_issue.step)
        self.assertEqual("run_sql", outcome.execution_issue.mode)

        export_path = FIXTURES / "artifacts" / "should_not_exist.csv"
        self.assertFalse(export_path.exists())


if __name__ == "__main__":
    unittest.main()
