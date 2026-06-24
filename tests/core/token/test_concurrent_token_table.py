"""ConcurrentTokenTable 测试。

测试并发令牌表的线程安全操作。
Tests ConcurrentTokenTable thread-safe operations.
"""

from __future__ import annotations

import threading

from ospf_python.core.token.concurrent_token_table import (
    ConcurrentTokenTable,
)
from ospf_python.core.token.token import Token


class TestConcurrentTokenTableBasic:
    """基础操作测试 / Basic operation tests."""

    def test_basic_set_get(self) -> None:
        """基本设置和获取。/ Basic set and get."""
        ctt = ConcurrentTokenTable()
        t = Token(name="x", index=0)
        ctt.set(t, 42)
        assert ctt.get(t) == 42

    def test_get_missing_returns_none(self) -> None:
        """不存在返回 None。/ Missing returns None."""
        ctt = ConcurrentTokenTable()
        t = Token(name="x", index=0)
        assert ctt.get(t) is None

    def test_remove(self) -> None:
        """移除操作。/ Remove operation."""
        ctt = ConcurrentTokenTable()
        t = Token(name="x", index=0)
        ctt.set(t, 1)
        assert ctt.remove(t) is True
        assert ctt.get(t) is None

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        ctt = ConcurrentTokenTable()
        t = Token(name="x", index=0)
        assert ctt.contains(t) is False
        ctt.set(t, 1)
        assert ctt.contains(t) is True

    def test_clear(self) -> None:
        """清空操作。/ Clear operation."""
        ctt = ConcurrentTokenTable()
        ctt.set(Token(name="a", index=0), 1)
        ctt.clear()
        assert ctt.size == 0


class TestConcurrentTokenTableThreadSafety:
    """线程安全测试 / Thread safety tests."""

    def test_thread_safety(self) -> None:
        """线程安全写入。/ Thread-safe writes."""
        ctt = ConcurrentTokenTable()
        errors: list[Exception] = []

        def writer(start: int) -> None:
            try:
                for i in range(100):
                    t = Token(
                        name=f"t{start + i}",
                        index=start + i,
                    )
                    ctt.set(t, i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i * 100,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert ctt.size == 400
