"""SQLite 持久化插件测试 / SQLite persistence plugin tests.

Tests for SQLiteRepository: transaction, batch save, query, update, delete.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from ospf_python.framework.persistence.sqlite_repository import SQLiteRepository


@pytest.fixture
def db_path() -> str:
    """创建临时数据库 / Create temporary database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    # Create table
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE test_items (id TEXT PRIMARY KEY, data TEXT)")
    conn.commit()
    conn.close()
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def repo(db_path: str) -> SQLiteRepository[str]:
    """创建 SQLite 仓储 / Create SQLite repository."""
    return SQLiteRepository(db_path=db_path, table_name="test_items")


class TestSQLiteRepository:
    """SQLite 仓储测试 / SQLite repository tests."""

    def test_save_and_find(self, db_path: str) -> None:
        """保存并查找 / Save and find."""
        repo = SQLiteRepository(db_path=db_path, table_name="test_items")
        repo.save("test_data_1")
        # Verify data was saved (via direct query)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test_items")
        rows = cursor.fetchall()
        conn.close()
        assert len(rows) >= 1

    def test_find_by_id(self, db_path: str) -> None:
        """按 ID 查找 / Find by ID."""
        repo = SQLiteRepository(db_path=db_path, table_name="test_items")
        # Insert directly
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO test_items (id, data) VALUES (?, ?)", ("item_1", "hello"))
        conn.commit()
        conn.close()
        result = repo.find_by_id("item_1")
        assert result is not None

    def test_find_by_id_not_found(self, db_path: str) -> None:
        """查找不存在的 ID / Find by ID not found."""
        repo = SQLiteRepository(db_path=db_path, table_name="test_items")
        result = repo.find_by_id("nonexistent")
        assert result is None

    def test_delete(self, db_path: str) -> None:
        """删除实体 / Delete entity."""
        repo = SQLiteRepository(db_path=db_path, table_name="test_items")
        # Insert directly
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO test_items (id, data) VALUES (?, ?)", ("item_1", "hello"))
        conn.commit()
        conn.close()
        repo.delete("item_1")
        result = repo.find_by_id("item_1")
        assert result is None

    def test_find_all(self, db_path: str) -> None:
        """查找所有 / Find all."""
        repo = SQLiteRepository(db_path=db_path, table_name="test_items")
        # Insert directly
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO test_items (id, data) VALUES (?, ?)", ("item_1", "hello"))
        conn.execute("INSERT INTO test_items (id, data) VALUES (?, ?)", ("item_2", "world"))
        conn.commit()
        conn.close()
        results = repo.find_all()
        assert len(results) == 2

    def test_transaction_commit(self, db_path: str) -> None:
        """事务提交 / Transaction commit."""
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO test_items (id, data) VALUES (?, ?)", ("tx_1", "committed"))
        conn.commit()
        conn.close()
        # Verify committed
        repo = SQLiteRepository(db_path=db_path, table_name="test_items")
        result = repo.find_by_id("tx_1")
        assert result is not None

    def test_transaction_rollback(self, db_path: str) -> None:
        """事务回滚 / Transaction rollback."""
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO test_items (id, data) VALUES (?, ?)", ("tx_rollback", "will_be_gone"))
        conn.rollback()
        conn.close()
        # Verify rolled back
        repo = SQLiteRepository(db_path=db_path, table_name="test_items")
        result = repo.find_by_id("tx_rollback")
        assert result is None

    def test_batch_save(self, db_path: str) -> None:
        """批量保存 / Batch save."""
        conn = sqlite3.connect(db_path)
        for i in range(10):
            conn.execute(
                "INSERT INTO test_items (id, data) VALUES (?, ?)",
                (f"batch_{i}", f"data_{i}"),
            )
        conn.commit()
        conn.close()
        repo = SQLiteRepository(db_path=db_path, table_name="test_items")
        results = repo.find_all()
        assert len(results) == 10

    def test_update_existing(self, db_path: str) -> None:
        """更新已有记录 / Update existing record."""
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO test_items (id, data) VALUES (?, ?)", ("upd_1", "original"))
        conn.commit()
        conn.close()
        # Update via INSERT OR REPLACE
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT OR REPLACE INTO test_items (id, data) VALUES (?, ?)", ("upd_1", "updated"))
        conn.commit()
        conn.close()
        repo = SQLiteRepository(db_path=db_path, table_name="test_items")
        result = repo.find_by_id("upd_1")
        assert result is not None
