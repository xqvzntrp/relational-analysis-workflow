from pathlib import Path
import builtins
import contextlib
import io
import json
import sys
import unittest
from unittest.mock import patch

import run


PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"
MANIFEST = PACKAGE / "manifest.csv"


class DryRunWithoutDuckDBTests(unittest.TestCase):
    def _blocked_import(self):
        original_import = builtins.__import__

        def blocked(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "duckdb" or name.startswith("duckdb."):
                raise ModuleNotFoundError(
                    "No module named 'duckdb'", name="duckdb"
                )
            return original_import(name, globals, locals, fromlist, level)

        return blocked

    def _main(self, *arguments):
        output = io.StringIO()
        with patch.object(sys, "argv", ["run.py", *arguments]), \
             patch("builtins.__import__", side_effect=self._blocked_import()), \
             contextlib.redirect_stdout(output):
            status = run.main()
        return status, output.getvalue()

    def test_plain_dry_run_does_not_import_duckdb(self):
        status, output = self._main("--dry-run", str(MANIFEST))
        self.assertEqual(0, status)
        self.assertIn("Dry run", output)

    def test_verbose_dry_run_does_not_import_duckdb(self):
        status, output = self._main("--dry-run", "--verbose", str(MANIFEST))
        self.assertEqual(0, status)
        self.assertIn("Discovered relation dependencies", output)

    def test_json_dry_run_does_not_import_duckdb(self):
        status, output = self._main("--dry-run", "--json", str(MANIFEST))
        self.assertEqual(0, status)
        self.assertTrue(json.loads(output)["ready"])

    def test_verbose_json_dry_run_does_not_import_duckdb(self):
        status, output = self._main(
            "--dry-run", "--verbose", "--json", str(MANIFEST)
        )
        self.assertEqual(0, status)
        document = json.loads(output)
        self.assertTrue(document["ready"])
        self.assertIn("dependencies", document)

    def test_run_reports_missing_duckdb_cleanly(self):
        status, output = self._main("--run", str(MANIFEST))
        self.assertEqual(1, status)
        self.assertIn("DuckDB is required for package execution.", output)
        self.assertIn("pip install -r requirements.txt", output)


if __name__ == "__main__":
    unittest.main()
