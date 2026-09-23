from pathlib import Path
import unittest

from relation_contract import read_relation_contract
from relation_contract_validator import validate_contract_declarations


PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"


class RelationContractTests(unittest.TestCase):
    def test_example_contract_is_valid(self):
        declarations, parse_issues = read_relation_contract(PACKAGE / "manifest.csv")
        self.assertTrue(declarations)
        self.assertEqual([], parse_issues)
        self.assertEqual([], validate_contract_declarations(PACKAGE / "manifest.csv"))

    def test_grain_keys_are_marked_as_keys(self):
        declarations, _ = read_relation_contract(PACKAGE / "manifest.csv")
        lookup = {(item.relation, item.column): item for item in declarations}

        self.assertTrue(lookup[("review_bundle", "bundle_id")].key)
        self.assertTrue(lookup[("prepared_product_bundle", "bundle_id")].key)
        self.assertTrue(lookup[("prepared_product_bundle", "product_id")].key)


if __name__ == "__main__":
    unittest.main()
