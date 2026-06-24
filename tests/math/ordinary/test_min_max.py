"""最小值/最大值工具测试。

Minimum / maximum utility tests.

测试 min_of、max_of、min_max_of 函数。
Tests min_of, max_of, min_max_of functions.
"""

from __future__ import annotations

from ospf_python.math.ordinary.min_max import max_of, min_max_of, min_of

# ── min_of ──────────────────────────────────────────────────────


class TestMinOf:
    """最小值测试。"""

    def test_basic_min(self) -> None:
        """基本最小值。/ Basic minimum."""
        assert min_of([3, 1, 4, 1, 5]) == 1

    def test_single_element(self) -> None:
        """单元素最小值。/ Single element minimum."""
        assert min_of([42]) == 42

    def test_negative_values(self) -> None:
        """负值最小值。/ Negative values minimum."""
        assert min_of([-3, -1, -4]) == -4

    def test_float_min(self) -> None:
        """浮点最小值。/ Float minimum."""
        assert min_of([3.14, 2.71, 1.41]) == 1.41


# ── max_of ──────────────────────────────────────────────────────


class TestMaxOf:
    """最大值测试。"""

    def test_basic_max(self) -> None:
        """基本最大值。/ Basic maximum."""
        assert max_of([3, 1, 4, 1, 5]) == 5

    def test_single_element(self) -> None:
        """单元素最大值。/ Single element maximum."""
        assert max_of([42]) == 42

    def test_negative_values(self) -> None:
        """负值最大值。/ Negative values maximum."""
        assert max_of([-3, -1, -4]) == -1

    def test_float_max(self) -> None:
        """浮点最大值。/ Float maximum."""
        assert max_of([3.14, 2.71, 1.41]) == 3.14


# ── min_max_of ──────────────────────────────────────────────────


class TestMinMaxOf:
    """最小最大值测试。"""

    def test_basic_min_max(self) -> None:
        """基本最小最大值。/ Basic min max."""
        lo, hi = min_max_of([3, 1, 4, 1, 5])
        assert lo == 1
        assert hi == 5

    def test_single_element(self) -> None:
        """单元素最小最大值。/ Single element min max."""
        lo, hi = min_max_of([42])
        assert lo == 42
        assert hi == 42

    def test_sorted_input(self) -> None:
        """已排序输入。/ Sorted input."""
        lo, hi = min_max_of([1, 2, 3, 4, 5])
        assert lo == 1
        assert hi == 5
