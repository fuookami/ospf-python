"""SQLite persistence plugin / SQLite 持久化插件.

Provides SQLite-based repository implementation.
"""

from __future__ import annotations

import sqlite3
from typing import TypeVar

from ospf_python.framework.persistence.repository import Repository

T = TypeVar("T")


class SQLiteRepository(Repository[T]):
    """SQLite repository implementation.

    SQLite 仓储实现。
    """

    def __init__(self, db_path: str, table_name: str) -> None:
        """Initialize SQLite repository.

        Args:
            db_path: Database file path.
            table_name: Table name.
        """
        self._db_path = db_path
        self._table_name = table_name

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(self._db_path)

    def find_by_id(self, id: str) -> T | None:
        """Find entity by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self._table_name} WHERE id = ?", (id,))
            row = cursor.fetchone()
            return row  # type: ignore[return-value]
        finally:
            conn.close()

    def save(self, entity: T) -> None:
        """Save entity."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Simplified: insert or replace
            cursor.execute(
                f"INSERT OR REPLACE INTO {self._table_name} (data) VALUES (?)",
                (str(entity),),
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, id: str) -> None:
        """Delete entity."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self._table_name} WHERE id = ?", (id,))
            conn.commit()
        finally:
            conn.close()

    def find_all(self) -> list[T]:
        """Find all entities."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self._table_name}")
            rows = cursor.fetchall()
            return rows  # type: ignore[return-value]
        finally:
            conn.close()
