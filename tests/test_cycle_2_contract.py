from pathlib import Path
import csv
import unittest

from manifest_schema import AUTHORITY_ZONES, MANIFEST_COLUMNS, MODES


ROOT = Path(__file__).parents[1]
PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"


class Cycle2ContractTests(unittest.TestCase):
    def test_manifest_surface_is_frozen(self):
        self.assertEqual(
            ("step", "mode", "input", "output", "authority_zone"),
            tuple(MANIFEST_COLUMNS),
        )
        self.assertEqual(
            ("load_csv", "run_sql", "export_sql"),
            tuple(MODES),
        )
        self.assertEqual(
            (
                "source",
                "prepared",
                "review",
                "focused",
                "inform",
                "business",
                "report",
            ),
            tuple(AUTHORITY_ZONES),
        )

    def test_reference_example_exports_review_and_report_products(self):
        with (PACKAGE / "manifest.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            exports = [
                row for row in csv.DictReader(handle)
                if row["mode"] == "export_sql"
            ]

        self.assertEqual(
            [
                (
                    "review_bundle",
                    "exports/bundle_analytical_base.csv",
                    "review",
                ),
                (
                    "report_bundle",
                    "exports/bundle_report.csv",
                    "report",
                ),
            ],
            [
                (row["input"], row["output"], row["authority_zone"])
                for row in exports
            ],
        )

    def test_cycle_2_contract_document_exists(self):
        self.assertTrue((ROOT / "docs" / "CYCLE_2_CONTRACT.org").is_file())


if __name__ == "__main__":
    unittest.main()
