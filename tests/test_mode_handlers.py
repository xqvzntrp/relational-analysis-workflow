from pathlib import Path
import unittest

import duckdb

from mode_handlers import load_csv


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


if __name__ == "__main__":
    unittest.main()
