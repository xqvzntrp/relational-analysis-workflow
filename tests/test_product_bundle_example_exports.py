from pathlib import Path
import csv
import unittest
from artifact_spec import read_artifact_expectations

PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"

class ProductBundleExampleExportTests(unittest.TestCase):
    def test_review_base_and_report_are_exported(self):
        with (PACKAGE/"manifest.csv").open("r",encoding="utf-8-sig",newline="") as h:
            exports=[r for r in csv.DictReader(h) if r["mode"]=="export_sql"]
        self.assertEqual(2,len(exports))
        self.assertEqual(("review_bundle","exports/bundle_analytical_base.csv","review"),
                         (exports[0]["input"],exports[0]["output"],exports[0]["authority_zone"]))
        self.assertEqual(("report_bundle","exports/bundle_report.csv","report"),
                         (exports[1]["input"],exports[1]["output"],exports[1]["authority_zone"]))

    def test_both_exports_are_golden_tested(self):
        expectations,issues=read_artifact_expectations(PACKAGE/"manifest.csv")
        self.assertEqual([],issues)
        self.assertEqual(
            ["exports/bundle_analytical_base.csv","exports/bundle_report.csv"],
            [x.artifact for x in expectations])

if __name__=="__main__":
    unittest.main()
