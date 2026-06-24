"""随机数工具测试。

Random utility tests.

测试 random_int、random_float、random_choice 函数。
Tests random_int, random_float, random_choice functions.
"""

from __future__ import annotations

from ospf_python.math.random import (
    random_choice,
    random_float,
    random_int,
)

# ── random_int ──────────────────────────────────────────────────


class TestRandomInt:
    """随机整数测试。"""

    def test_in_range(self) -> None:
        """在范围内。/ In range."""
        for _ in range(100):
            val = random_int(1, 10)
            assert 1 <= val <= 10

    def test_same_bounds(self) -> None:
        """相同边界。/ Same bounds."""
        assert random_int(5, 5) == 5

    def test_negative_range(self) -> None:
        """负范围。/ Negative range."""
        for _ in range(100):
            val = random_int(-10, -1)
            assert -10 <= val <= -1


# ── random_float ────────────────────────────────────────────────


class TestRandomFloat:
    """随机浮点数测试。"""

    def test_in_range(self) -> None:
        """在范围内。/ In range."""
        for _ in range(100):
            val = random_float(0.0, 1.0)
            assert 0.0 <= val < 1.0

    def test_negative_range(self) -> None:
        """负范围。/ Negative range."""
        for _ in range(100):
            val = random_float(-5.0, -1.0)
            assert -5.0 <= val < -1.0

    def test_returns_float(self) -> None:
        """返回浮点数。/ Returns float."""
        val = random_float(0.0, 10.0)
        assert isinstance(val, float)


# ── random_choice ───────────────────────────────────────────────


class TestRandomChoice:
    """随机选择测试。"""

    def test_choice_from_list(self) -> None:
        """从列表选择。/ Choice from list."""
        items = [1, 2, 3, 4, 5]
        for _ in range(100):
            val = random_choice(items)
            assert val in items

    def test_single_element(self) -> None:
        """单元素列表。/ Single element list."""
        assert random_choice([42]) == 42

    def test_choice_from_string_list(self) -> None:
        """从字符串列表选择。/ Choice from string list."""
        items = ["a", "b", "c"]
        for _ in range(50):
            val = random_choice(items)
            assert val in items
