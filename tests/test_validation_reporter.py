from pathlib import Path
import unittest

from manifest_inspector import ManifestRowInspection
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
        text = format_validation_report(Path("manifest.csv"), [], verbose=False)
        self.assertIn("Result: ready to run.", text)
        self.assertNotIn("Execution plan:", text)

    def test_failure_report_states_nothing_executed(self):
        issue = ValidationIssue(
            step="-",
            problem_type="manifest_missing",
            message="Manifest does not exist.",
            hint="Check the path and try again.",
        )
        text = format_validation_report(
            Path("manifest.csv"), [issue], verbose=True
        )
        self.assertIn("Result: not ready to run.", text)
        self.assertIn("No package steps were executed.", text)
        self.assertIn("Validation type: manifest_missing", text)

    def test_verbose_success_describes_execution_plan(self):
        row = ManifestRowInspection(
            line_number=2,
            step="1",
            mode="load_csv",
            input_value="data/product.csv",
            output_value="source_product",
            authority_zone="source",
            resolved_input="/tmp/package/data/product.csv",
            resolved_output="/tmp/package/source_product",
        )
        text = format_validation_report(
            Path("manifest.csv"), [], verbose=True, inspections=[row]
        )
        self.assertIn("Execution plan: 1 step.", text)
        self.assertIn("Step 1 on line 2:", text)
        self.assertIn("Mode: load_csv", text)
        self.assertIn("Authority zone: source", text)
        self.assertIn("Resolved input:", text)


if __name__ == "__main__":
    unittest.main()
