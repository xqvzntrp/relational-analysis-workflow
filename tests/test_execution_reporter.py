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
            input_path="/package/sql/review.sql",
            sql_line_number=7,
            sql_line_text="FROM prepared_missing",
            creates=("review_bundle",),
            references=("prepared_missing",),
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
        self.assertIn("Input: /package/sql/review.sql", text)
        self.assertIn("SQL line: 7", text)
        self.assertIn("SQL text: FROM prepared_missing", text)
        self.assertIn("SQL creates: review_bundle", text)
        self.assertIn("SQL references: prepared_missing", text)


if __name__ == "__main__":
    unittest.main()
