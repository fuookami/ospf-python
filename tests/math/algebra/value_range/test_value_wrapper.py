"""值包装器测试。

Value wrapper tests.

测试 ValueWrapper 的创建和有效性检查。
Tests ValueWrapper creation and validity check.
"""

from __future__ import annotations

from ospf_python.math.algebra.value_range.interval import Interval
from ospf_python.math.algebra.value_range.value_range import ValueRange
from ospf_python.math.algebra.value_range.value_wrapper import (
    ValueWrapper,
)

# ── ValueWrapper ────────────────────────────────────────────────


class TestValueWrapper:
    """值包装器测试。"""

    def test_creation(self) -> None:
        """创建值包装器。/ Create value wrapper."""
        vr = ValueRange.single(Interval.closed(0, 10))
        vw = ValueWrapper(_value=5, _range=vr)
        assert vw.value == 5

    def test_valid_range(self) -> None:
        """有效范围属性。/ Valid range property."""
        vr = ValueRange.single(Interval.closed(0, 10))
        vw = ValueWrapper(_value=5, _range=vr)
        assert vw.valid_range == vr

    def test_is_valid_in_range(self) -> None:
        """范围内的值有效。/ Value in range is valid."""
        vr = ValueRange.single(Interval.closed(0, 10))
        vw = ValueWrapper(_value=5, _range=vr)
        assert vw.is_valid()

    def test_is_valid_out_of_range(self) -> None:
        """范围外的值无效。/ Value out of range is invalid."""
        vr = ValueRange.single(Interval.closed(0, 10))
        vw = ValueWrapper(_value=15, _range=vr)
        assert not vw.is_valid()

    def test_is_valid_boundary(self) -> None:
        """边界值有效。/ Boundary value is valid."""
        vr = ValueRange.single(Interval.closed(0, 10))
        vw = ValueWrapper(_value=0, _range=vr)
        assert vw.is_valid()

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        vr = ValueRange.single(Interval.closed(0, 10))
        vw = ValueWrapper(_value=5, _range=vr)
        assert vw.value == 5
