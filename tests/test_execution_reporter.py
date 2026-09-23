from pathlib import Path
import unittest

from execution_errors import ExecutionIssue
from execution_reporter import format_execution_failure


class ExecutionReporterTests(unittest.TestCase):
    def test_failure_report_reads_like_prose(self):
        issue = ExecutionIssue(
            step="2",
            mode="run_sql",
            problem_type="duckdb_error",
            message="Binder Error: missing column",
            hint="Check the SQL.",
        )

        text = format_execution_failure(
            Path("manifest.csv"),
            completed_steps=1,
            issue=issue,
            verbose=True,
        )

        self.assertIn("Result: stopped before completion.", text)
        self.assertIn("Completed steps before failure: 1.", text)
        self.assertIn("Step 2 (run_sql) stopped because", text)
        self.assertIn("What to do:", text)
        self.assertIn("Later manifest steps were not executed.", text)
        self.assertIn("Execution type: duckdb_error", text)


if __name__ == "__main__":
    unittest.main()
