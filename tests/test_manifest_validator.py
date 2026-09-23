from pathlib import Path
import unittest

from manifest_validator import validate_manifest


FIXTURES = Path(__file__).parent / "fixtures"


class ManifestValidatorTests(unittest.TestCase):
    def test_valid_manifest_has_no_issues(self):
        issues = validate_manifest(FIXTURES / "valid_manifest.csv")
        self.assertEqual([], issues)

    def test_invalid_manifest_reports_multiple_issues(self):
        issues = validate_manifest(FIXTURES / "invalid_manifest.csv")
        problem_types = {issue.problem_type for issue in issues}

        self.assertIn("duplicate_step", problem_types)
        self.assertIn("invalid_mode", problem_types)
        self.assertIn("invalid_authority_zone", problem_types)
        self.assertIn("missing_input", problem_types)
        self.assertIn("missing_output", problem_types)

    def test_missing_manifest_fails_cleanly(self):
        issues = validate_manifest(FIXTURES / "does_not_exist.csv")
        self.assertEqual("manifest_missing", issues[0].problem_type)


if __name__ == "__main__":
    unittest.main()
