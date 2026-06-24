"""整数范围测试。

Integer range tests.

测试 IntegerRange 和 NumericUIntegerRange。
Tests IntegerRange and NumericUIntegerRange.
"""

from __future__ import annotations

from ospf_python.math.integer_range import (
    IntegerRange,
    NumericUIntegerRange,
)

# ── IntegerRange ────────────────────────────────────────────────


class TestIntegerRange:
    """整数范围测试。"""

    def test_basic_range(self) -> None:
        """基本范围。/ Basic range."""
        r = IntegerRange(start=0, end=5, step=1)
        assert list(r) == [0, 1, 2, 3, 4]

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        r = IntegerRange(start=0, end=10, step=2)
        assert 0 in r
        assert 2 in r
        assert 5 not in r

    def test_length(self) -> None:
        """范围长度。/ Range length."""
        r = IntegerRange(start=0, end=10, step=1)
        assert len(r) == 10

    def test_step_two(self) -> None:
        """步长为 2。/ Step size 2."""
        r = IntegerRange(start=0, end=10, step=2)
        assert list(r) == [0, 2, 4, 6, 8]

    def test_empty_range(self) -> None:
        """空范围。/ Empty range."""
        r = IntegerRange(start=5, end=5, step=1)
        assert len(r) == 0
        assert list(r) == []

    def test_zero_step_resets(self) -> None:
        """零步长重置为 1。/ Zero step resets to 1."""
        r = IntegerRange(start=0, end=5, step=0)
        assert r.step == 1

    def test_negative_range(self) -> None:
        """负范围。/ Negative range."""
        r = IntegerRange(start=5, end=0, step=-1)
        assert list(r) == [5, 4, 3, 2, 1]

    def test_single_element(self) -> None:
        """单元素范围。/ Single element range."""
        r = IntegerRange(start=3, end=4, step=1)
        assert list(r) == [3]
        assert len(r) == 1


# ── NumericUIntegerRange ────────────────────────────────────────


class TestNumericUIntegerRange:
    """无符号整数范围测试。"""

    def test_basic_range(self) -> None:
        """基本无符号范围。/ Basic unsigned range."""
        r = NumericUIntegerRange(start=0, end=5, step=1)
        assert list(r) == [0, 1, 2, 3, 4]

    def test_negative_start_clamped(self) -> None:
        """负起始值截断到零。/ Negative start clamped."""
        r = NumericUIntegerRange(start=-3, end=5, step=1)
        assert r.start == 0

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        r = NumericUIntegerRange(start=0, end=10, step=1)
        assert 5 in r
        assert 10 not in r

    def test_length(self) -> None:
        """范围长度。/ Range length."""
        r = NumericUIntegerRange(start=0, end=5, step=1)
        assert len(r) == 5
