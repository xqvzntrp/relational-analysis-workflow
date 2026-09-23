from pathlib import Path
import tempfile
import unittest

from sql_diagnostics import build_sql_failure_context, extract_line_number


class SqlDiagnosticsTests(unittest.TestCase):
    def test_extracts_duckdb_style_line_number(self):
        self.assertEqual(
            3,
            extract_line_number("Binder Error: problem\\nLINE 3: SELECT missing"),
        )

    def test_builds_file_and_dependency_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "example.sql"
            path.write_text(
                "CREATE VIEW review_example AS\\n"
                "SELECT missing_column\\n"
                "FROM prepared_example;\\n",
                encoding="utf-8",
            )

            context = build_sql_failure_context(
                path,
                "Binder Error: missing column\\nLINE 2: SELECT missing_column",
            )

            self.assertEqual(2, context.line_number)
            self.assertEqual("SELECT missing_column", context.line_text)
            self.assertEqual(("review_example",), context.creates)
            self.assertEqual(("prepared_example",), context.references)


if __name__ == "__main__":
    unittest.main()
