from pathlib import Path
import shutil
import unittest

from executor import database_path_for_manifest, execute_manifest


FIXTURES = Path(__file__).parent / "fixtures"


class ExecutorTests(unittest.TestCase):
    def tearDown(self):
        artifacts = FIXTURES / "artifacts"
        if artifacts.exists():
            shutil.rmtree(artifacts)

    def test_valid_manifest_executes_load_csv_and_leaves_other_modes_pending(self):
        results, issues = execute_manifest(FIXTURES / "valid_manifest.csv")

        self.assertEqual([], issues)
        self.assertEqual(3, len(results))
        self.assertEqual("completed", results[0].status)
        self.assertIn("Loaded 2 rows", results[0].message)
        self.assertEqual("pending", results[1].status)
        self.assertEqual("pending", results[2].status)

        self.assertTrue(
            database_path_for_manifest(FIXTURES / "valid_manifest.csv").exists()
        )

    def test_invalid_manifest_never_builds_execution_plan(self):
        results, issues = execute_manifest(FIXTURES / "invalid_manifest.csv")

        self.assertEqual([], results)
        self.assertTrue(issues)


if __name__ == "__main__":
    unittest.main()
