from pathlib import Path
import unittest

from package_tester import test_package


PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"


class PackageTesterTests(unittest.TestCase):
    def test_unresolved_dependency_fails_before_execution(self):
        result = test_package(PACKAGE / "manifest_unresolved_relation.csv")

        self.assertFalse(result.passed)
        self.assertIsNone(result.execution)
        self.assertTrue(result.preflight_issues)
        self.assertEqual(
            "unresolved_relation",
            result.preflight_issues[0].problem_type,
        )

    def test_backward_authority_flow_fails_before_execution(self):
        result = test_package(PACKAGE / "manifest_backward_zone.csv")

        self.assertFalse(result.passed)
        self.assertIsNone(result.execution)
        self.assertTrue(result.preflight_issues)
        self.assertEqual(
            "backward_authority_dependency",
            result.preflight_issues[0].problem_type,
        )


if __name__ == "__main__":
    unittest.main()
