from pathlib import Path
import unittest

from executor import execute_manifest


FIXTURES = Path(__file__).parent / "fixtures"


class ExecutorTests(unittest.TestCase):
    def test_valid_manifest_returns_pending_execution_results(self):
        results, issues = execute_manifest(FIXTURES / "valid_manifest.csv")

        self.assertEqual([], issues)
        self.assertEqual(3, len(results))
        self.assertEqual(["1", "2", "3"], [result.step for result in results])
        self.assertTrue(all(result.status == "pending" for result in results))

    def test_invalid_manifest_never_builds_execution_plan(self):
        results, issues = execute_manifest(FIXTURES / "invalid_manifest.csv")

        self.assertEqual([], results)
        self.assertTrue(issues)


if __name__ == "__main__":
    unittest.main()
