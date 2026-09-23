"""Concrete execution handlers for manifest modes."""

from __future__ import annotations

from pathlib import Path

import duckdb


def quote_identifier(identifier: str) -> str:
    """Safely quote a DuckDB identifier."""
    return '"' + identifier.replace('"', '""') + '"'


def load_csv(
    connection: duckdb.DuckDBPyConnection,
    input_path: Path,
    target_relation: str,
) -> int:
    """Create or replace a table from a CSV file and return its row count."""
    input_path = input_path.resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"CSV input does not exist: {input_path}")

    if not input_path.is_file():
        raise ValueError(f"CSV input is not a file: {input_path}")

    if not target_relation.strip():
        raise ValueError("Target relation name is required for load_csv.")

    relation = quote_identifier(target_relation.strip())

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE {relation} AS
        SELECT *
        FROM read_csv_auto(?, header = true)
        """,
        [str(input_path)],
    )

    row_count = connection.execute(
        f"SELECT COUNT(*) FROM {relation}"
    ).fetchone()[0]

    return int(row_count)


def run_sql(
    connection: duckdb.DuckDBPyConnection,
    sql_path: Path,
) -> None:
    """Execute the complete contents of a SQL file."""
    sql_path = sql_path.resolve()

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL input does not exist: {sql_path}")

    if not sql_path.is_file():
        raise ValueError(f"SQL input is not a file: {sql_path}")

    sql_text = sql_path.read_text(encoding="utf-8").strip()

    if not sql_text:
        raise ValueError(f"SQL input is empty: {sql_path}")

    connection.execute(sql_text)
