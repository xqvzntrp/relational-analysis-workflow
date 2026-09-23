from pathlib import Path
import csv
import tempfile
import unittest

import duckdb

from mode_handlers import export_sql, load_csv, run_sql


FIXTURES = Path(__file__).parent / "fixtures"


class LoadCsvTests(unittest.TestCase):
    def test_load_csv_creates_relation_and_returns_row_count(self):
        connection = duckdb.connect(":memory:")
        try:
            count = load_csv(
                connection,
                FIXTURES / "data" / "product.csv",
                "source_product",
            )

            self.assertEqual(2, count)

            rows = connection.execute(
                "SELECT product_id, product_name "
                "FROM source_product ORDER BY product_id"
            ).fetchall()

            self.assertEqual(
                [("P001", "Sofa"), ("P002", "Coffee Table")],
                rows,
            )
        finally:
            connection.close()

    def test_load_csv_replaces_existing_relation(self):
        connection = duckdb.connect(":memory:")
        try:
            connection.execute(
                "CREATE TABLE source_product AS SELECT 999 AS old_value"
            )

            load_csv(
                connection,
                FIXTURES / "data" / "product.csv",
                "source_product",
            )

            columns = connection.execute(
                "DESCRIBE source_product"
            ).fetchall()

            self.assertEqual(
                ["product_id", "product_name"],
                [column[0] for column in columns],
            )
        finally:
            connection.close()


class RunSqlTests(unittest.TestCase):
    def test_run_sql_executes_sql_file(self):
        connection = duckdb.connect(":memory:")
        try:
            load_csv(
                connection,
                FIXTURES / "data" / "product.csv",
                "source_product",
            )

            run_sql(
                connection,
                FIXTURES / "sql" / "prepared_product.sql",
            )

            rows = connection.execute(
                "SELECT product_id, product_name_upper "
                "FROM prepared_product ORDER BY product_id"
            ).fetchall()

            self.assertEqual(
                [("P001", "SOFA"), ("P002", "COFFEE TABLE")],
                rows,
            )
        finally:
            connection.close()


class ExportSqlTests(unittest.TestCase):
    def test_export_sql_exports_relation_to_csv(self):
        connection = duckdb.connect(":memory:")
        try:
            load_csv(
                connection,
                FIXTURES / "data" / "product.csv",
                "source_product",
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "product.csv"

                count = export_sql(
                    connection,
                    "source_product",
                    output_path,
                )

                self.assertEqual(2, count)
                self.assertTrue(output_path.exists())

                with output_path.open("r", encoding="utf-8", newline="") as handle:
                    rows = list(csv.reader(handle))

                self.assertEqual(
                    [
                        ["product_id", "product_name"],
                        ["P001", "Sofa"],
                        ["P002", "Coffee Table"],
                    ],
                    rows,
                )
        finally:
            connection.close()

    def test_export_sql_accepts_select_query(self):
        connection = duckdb.connect(":memory:")
        try:
            load_csv(
                connection,
                FIXTURES / "data" / "product.csv",
                "source_product",
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "filtered.csv"

                count = export_sql(
                    connection,
                    "SELECT * FROM source_product WHERE product_id = 'P001'",
                    output_path,
                )

                self.assertEqual(1, count)
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
