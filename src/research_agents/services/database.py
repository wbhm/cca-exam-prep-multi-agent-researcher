"""Simulated database service with pre-built structured data.

Supports simple keyword-based queries against named tables.
"""

from __future__ import annotations


class TableNotFoundError(Exception):
    """Raised when a table name is not in the database."""


class DatabaseService:
    """In-memory database with named tables of dictionaries."""

    def __init__(self, tables: dict[str, list[dict]]) -> None:
        self._tables = tables

    def query(self, table: str, filters: dict | None = None) -> list[dict]:
        """Query a table, optionally filtering by exact field matches."""
        if table not in self._tables:
            raise TableNotFoundError(f"Table not found: {table}")
        rows = self._tables[table]
        if not filters:
            return rows
        return [
            row
            for row in rows
            if all(row.get(k) == v for k, v in filters.items())
        ]

    def get_schema(self, table: str) -> dict:
        """Return the schema (column names and inferred types) for a table."""
        if table not in self._tables:
            raise TableNotFoundError(f"Table not found: {table}")
        rows = self._tables[table]
        if not rows:
            return {"table": table, "columns": []}
        sample = rows[0]
        columns = [
            {"name": k, "type": type(v).__name__} for k, v in sample.items()
        ]
        return {"table": table, "columns": columns}

    @property
    def table_names(self) -> list[str]:
        return list(self._tables.keys())
