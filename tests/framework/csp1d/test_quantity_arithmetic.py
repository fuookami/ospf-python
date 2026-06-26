"""QuantityArithmetic tests.

Test safe quantity arithmetic operations.
测试安全数量算术运算。
"""

from __future__ import annotations

from ospf_python.framework.csp1d.domain.material.model.quantity_arithmetic import (
    QuantityArithmetic,
)


class TestQuantityArithmetic:
    """QuantityArithmetic static method tests."""

    def test_add_positive(self) -> None:
        """Add two positive numbers."""
        result = QuantityArithmetic.add(3, 5)
        assert result.is_ok()
        assert result.unwrap() == 8

    def test_add_zero(self) -> None:
        """Add with zero."""
        result = QuantityArithmetic.add(0, 5)
        assert result.is_ok()
        assert result.unwrap() == 5

    def test_add_result_negative(self) -> None:
        """Add resulting in negative fails."""
        result = QuantityArithmetic.add(-10, 5)
        assert result.is_failed()

    def test_subtract_valid(self) -> None:
        """Subtract yielding non-negative."""
        result = QuantityArithmetic.subtract(10, 3)
        assert result.is_ok()
        assert result.unwrap() == 7

    def test_subtract_result_negative(self) -> None:
        """Subtract resulting in negative fails."""
        result = QuantityArithmetic.subtract(3, 10)
        assert result.is_failed()

    def test_multiply_positive(self) -> None:
        """Multiply two positive numbers."""
        result = QuantityArithmetic.multiply(3, 5)
        assert result.is_ok()
        assert result.unwrap() == 15

    def test_multiply_by_zero(self) -> None:
        """Multiply by zero."""
        result = QuantityArithmetic.multiply(0, 5)
        assert result.is_ok()
        assert result.unwrap() == 0

    def test_multiply_result_negative(self) -> None:
        """Multiply resulting in negative fails."""
        result = QuantityArithmetic.multiply(-3, 5)
        assert result.is_failed()
