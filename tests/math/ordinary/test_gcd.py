"""最大公约数测试。

Greatest common divisor tests.

测试 gcd 和 extended_gcd 函数。
Tests gcd and extended_gcd functions.
"""

from __future__ import annotations

from ospf_python.math.ordinary.gcd import extended_gcd, gcd

# ── gcd ─────────────────────────────────────────────────────────


class TestGcd:
    """最大公约数测试。"""

    def test_coprime(self) -> None:
        """互质数。/ Coprime numbers."""
        assert gcd(7, 13) == 1

    def test_common_divisor(self) -> None:
        """有公因数。/ Common divisor."""
        assert gcd(12, 8) == 4

    def test_same_number(self) -> None:
        """相同数。/ Same number."""
        assert gcd(5, 5) == 5

    def test_one_and_n(self) -> None:
        """1 和 n。/ 1 and n."""
        assert gcd(1, 42) == 1

    def test_zero_and_n(self) -> None:
        """0 和 n。/ 0 and n."""
        assert gcd(0, 5) == 5

    def test_large_numbers(self) -> None:
        """大数 GCD。/ Large number GCD."""
        assert gcd(100, 75) == 25


# ── extended_gcd ────────────────────────────────────────────────


class TestExtendedGcd:
    """扩展欧几里得算法测试。"""

    def test_basic(self) -> None:
        """基本扩展 GCD。/ Basic extended GCD."""
        g, x, y = extended_gcd(35, 15)
        assert g == 5
        assert 35 * x + 15 * y == g

    def test_coprime(self) -> None:
        """互质数扩展 GCD。/ Coprime extended GCD."""
        g, x, y = extended_gcd(3, 7)
        assert g == 1
        assert 3 * x + 7 * y == g

    def test_same_number(self) -> None:
        """相同数扩展 GCD。/ Same number extended GCD."""
        g, x, y = extended_gcd(5, 5)
        assert g == 5
        assert 5 * x + 5 * y == g

    def test_zero_b(self) -> None:
        """b 为零。/ b is zero."""
        g, x, y = extended_gcd(7, 0)
        assert g == 7
        assert x == 1
        assert y == 0

    def test_identity(self) -> None:
        """恒等式验证。/ Identity verification."""
        a, b = 240, 46
        g, x, y = extended_gcd(a, b)
        assert a * x + b * y == g
