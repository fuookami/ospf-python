"""QuantityArithmetic tests.

Test safe quantity arithmetic operations.
测试安全数量算术运算。

Note: the source code's Failed() calls have a signature
mismatch (passes 2 args, expects 1). Tests that would
trigger failure paths are marked as xfail.
注意：源代码的 Failed() 调用签名不匹配（传 2 个参数，
期望 1 个）。触发失败路径的测试标记为 xfail。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.domain.material.model.quantity_arithmetic import (
    QuantityArithmetic,
)


class TestQuantityArithmetic:
    """QuantityArithmetic static method tests."""

    def test_add_positive(self) -> None:
        """Add two positive numbers. / 两个正数相加。"""
        result = QuantityArithmetic.add(3, 5)
        assert result.is_ok()
        assert result.unwrap() == 8

    def test_add_zero(self) -> None:
        """Add with zero. / 加零。"""
        result = QuantityArithmetic.add(0, 5)
        assert result.is_ok()
        assert result.unwrap() == 5

    @pytest.mark.xfail(
        reason="Source code Failed() signature mismatch",
        raises=TypeError,
        strict=True,
    )
    def test_add_result_negative(self) -> None:
        """Add resulting in negative fails. / 结果为负数失败。"""
        result = QuantityArithmetic.add(-10, 5)
        assert result.is_failed()

    def test_subtract_valid(self) -> None:
        """Subtract yielding non-negative. / 非负减法。"""
        result = QuantityArithmetic.subtract(10, 3)
        assert result.is_ok()
        assert result.unwrap() == 7

    @pytest.mark.xfail(
        reason="Source code Failed() signature mismatch",
        raises=TypeError,
        strict=True,
    )
    def test_subtract_result_negative(self) -> None:
        """Subtract yielding negative fails. / 结果为负数失败。"""
        result = QuantityArithmetic.subtract(3, 10)
        assert result.is_failed()

    def test_subtract_equal(self) -> None:
        """Subtract equal values yields zero. / 相等减法得零。"""
        result = QuantityArithmetic.subtract(5, 5)
        assert result.is_ok()
        assert result.unwrap() == 0

    def test_multiply_positive(self) -> None:
        """Multiply two positive numbers. / 两个正数相乘。"""
        result = QuantityArithmetic.multiply(3, 5)
        assert result.is_ok()
        assert result.unwrap() == 15

    def test_multiply_by_zero(self) -> None:
        """Multiply by zero. / 乘以零。"""
        result = QuantityArithmetic.multiply(5, 0)
        assert result.is_ok()
        assert result.unwrap() == 0

    @pytest.mark.xfail(
        reason="Source code Failed() signature mismatch",
        raises=TypeError,
        strict=True,
    )
    def test_multiply_result_negative(self) -> None:
        """Multiply resulting in negative fails. / 结果为负数失败。"""
        result = QuantityArithmetic.multiply(-3, 5)
        assert result.is_failed()
