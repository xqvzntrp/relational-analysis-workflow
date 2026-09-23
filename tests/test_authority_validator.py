from pathlib import Path
import unittest

from authority_validator import validate_authority_progression


PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"


class AuthorityValidatorTests(unittest.TestCase):
    def test_valid_example_has_no_authority_issues(self):
        issues = validate_authority_progression(PACKAGE / "manifest.csv")
        self.assertEqual([], issues)

    def test_backward_zone_dependency_is_rejected(self):
        issues = validate_authority_progression(
            PACKAGE / "manifest_backward_zone.csv"
        )

        self.assertEqual(1, len(issues))
        issue = issues[0]
        self.assertEqual("2", issue.step)
        self.assertEqual("source", issue.authority_zone)
        self.assertEqual("business_seed", issue.relation)
        self.assertEqual("1", issue.producer_step)
        self.assertEqual("business", issue.producer_zone)
        self.assertEqual(
            "backward_authority_dependency",
            issue.problem_type,
        )


if __name__ == "__main__":
    unittest.main()
