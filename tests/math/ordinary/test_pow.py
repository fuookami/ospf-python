"""整数幂运算测试。

Integer power tests.

测试 pow_int 函数。
Tests pow_int function.
"""

from __future__ import annotations

from ospf_python.math.ordinary.pow import pow_int

# ── pow_int ─────────────────────────────────────────────────────


class TestPowInt:
    """整数幂运算测试。"""

    def test_basic_power(self) -> None:
        """基本幂运算。/ Basic power."""
        assert pow_int(2, 3) == 8

    def test_zero_exponent(self) -> None:
        """零指数。/ Zero exponent."""
        assert pow_int(5, 0) == 1

    def test_one_exponent(self) -> None:
        """单位指数。/ One exponent."""
        assert pow_int(7, 1) == 7

    def test_square(self) -> None:
        """平方。/ Square."""
        assert pow_int(3, 2) == 9

    def test_cube(self) -> None:
        """立方。/ Cube."""
        assert pow_int(2, 3) == 8

    def test_large_exponent(self) -> None:
        """大指数。/ Large exponent."""
        assert pow_int(2, 10) == 1024

    def test_zero_base(self) -> None:
        """零底数。/ Zero base."""
        assert pow_int(0, 5) == 0

    def test_one_base(self) -> None:
        """底数为一。/ Base is one."""
        assert pow_int(1, 100) == 1
