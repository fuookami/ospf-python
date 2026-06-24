"""带类型值域测试。

Typed value range tests.

测试 TypedValueRange 的创建和包含检查。
Tests TypedValueRange creation and contains check.
"""

from __future__ import annotations

from ospf_python.math.algebra.value_range.interval import Interval
from ospf_python.math.algebra.value_range.typed_value_range import (
    TypedValueRange,
)
from ospf_python.math.algebra.value_range.value_range import ValueRange

# ── TypedValueRange ─────────────────────────────────────────────


class TestTypedValueRange:
    """带类型值域测试。"""

    def test_creation(self) -> None:
        """创建带类型值域。/ Create typed range."""
        tvr = TypedValueRange.of(
            "int",
            ValueRange.single(Interval.closed(0, 100)),
        )
        assert tvr.type_name == "int"

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        tvr = TypedValueRange.of(
            "int",
            ValueRange.single(Interval.closed(0, 10)),
        )
        assert tvr.contains(5)
        assert not tvr.contains(20)

    def test_contains_boundary(self) -> None:
        """边界包含。/ Boundary contains."""
        tvr = TypedValueRange.of(
            "int",
            ValueRange.single(Interval.closed(0, 10)),
        )
        assert tvr.contains(0)
        assert tvr.contains(10)

    def test_float_type(self) -> None:
        """浮点类型值域。/ Float type range."""
        tvr = TypedValueRange.of(
            "float",
            ValueRange.single(Interval.closed(0.0, 1.0)),
        )
        assert tvr.type_name == "float"
        assert tvr.contains(0.5)

    def test_unbounded_range(self) -> None:
        """无界值域。/ Unbounded range."""
        tvr: TypedValueRange[int] = TypedValueRange.of(
            "int",
            ValueRange.single(Interval.unbounded()),
        )
        assert tvr.contains(999)
