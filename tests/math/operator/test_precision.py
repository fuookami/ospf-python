"""精度控制类型测试。

Precision control type tests.

测试 Precision 类的创建和舍入操作。
Tests Precision creation and rounding operations.
"""

from __future__ import annotations

from ospf_python.math.operator.precision import Precision

# ── Precision ───────────────────────────────────────────────────


class TestPrecision:
    """精度控制测试。"""

    def test_creation(self) -> None:
        """创建精度控制。/ Create precision."""
        p = Precision(digits=2)
        assert p.digits == 2

    def test_round_to_two_digits(self) -> None:
        """四舍五入到两位小数。/ Round to two digits."""
        p = Precision(digits=2)
        assert p.round_to(3.14159) == 3.14

    def test_round_to_zero_digits(self) -> None:
        """四舍五入到整数。/ Round to integer."""
        p = Precision(digits=0)
        assert p.round_to(3.7) == 4.0

    def test_round_to_three_digits(self) -> None:
        """四舍五入到三位小数。/ Round to three digits."""
        p = Precision(digits=3)
        assert p.round_to(3.14159) == 3.142

    def test_round_negative(self) -> None:
        """负值舍入。/ Negative rounding."""
        p = Precision(digits=1)
        assert p.round_to(-3.15) == -3.1

    def test_round_zero(self) -> None:
        """零值舍入。/ Zero rounding."""
        p = Precision(digits=2)
        assert p.round_to(0.0) == 0.0

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        p = Precision(digits=3)
        assert p.digits == 3

    def test_equality(self) -> None:
        """相等比较。/ Equality."""
        assert Precision(digits=2) == Precision(digits=2)
        assert Precision(digits=2) != Precision(digits=3)
