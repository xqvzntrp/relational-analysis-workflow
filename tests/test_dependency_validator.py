from pathlib import Path
import unittest

from dependency_validator import validate_dependencies


PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"


class DependencyValidatorTests(unittest.TestCase):
    def test_valid_example_has_no_dependency_issues(self):
        issues = validate_dependencies(PACKAGE / "manifest.csv")
        self.assertEqual([], issues)

    def test_unresolved_relation_is_reported(self):
        issues = validate_dependencies(
            PACKAGE / "manifest_unresolved_relation.csv"
        )

        self.assertEqual(1, len(issues))
        issue = issues[0]
        self.assertEqual("2", issue.step)
        self.assertEqual("review", issue.authority_zone)
        self.assertEqual("prepared_missing", issue.relation)
        self.assertEqual("unresolved_relation", issue.problem_type)


if __name__ == "__main__":
    unittest.main()
