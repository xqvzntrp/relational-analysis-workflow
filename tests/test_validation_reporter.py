from pathlib import Path
import unittest

from manifest_validator import ValidationIssue
from validation_reporter import format_issue, format_validation_report


class ValidationReporterTests(unittest.TestCase):
    def test_format_issue_reads_like_prose(self):
        issue = ValidationIssue(
            step="2",
            problem_type="invalid_mode",
            message="Mode 'bad_mode' is not allowed.",
            hint="Use one of: load_csv, run_sql, export_sql",
        )

        text = format_issue(issue)

        self.assertIn("Step 2 failed because", text)
        self.assertIn("What to do:", text)

    def test_success_report_is_concise(self):
        text = format_validation_report(
            Path("manifest.csv"),
            [],
            verbose=False,
        )

        self.assertIn("Result: ready to run.", text)
        self.assertNotIn("Validation type:", text)

    def test_failure_report_states_nothing_executed(self):
        issue = ValidationIssue(
            step="-",
            problem_type="manifest_missing",
            message="Manifest does not exist.",
            hint="Check the path and try again.",
        )

        text = format_validation_report(
            Path("manifest.csv"),
            [issue],
            verbose=True,
        )

        self.assertIn("Result: not ready to run.", text)
        self.assertIn("No package steps were executed.", text)
        self.assertIn("Validation type: manifest_missing", text)


if __name__ == "__main__":
    unittest.main()
