"""质因数分解测试。

Prime factorization tests.

测试 prime_factors 函数。
Tests prime_factors function.
"""

from __future__ import annotations

from ospf_python.math.ordinary.factorization import prime_factors

# ── prime_factors ───────────────────────────────────────────────


class TestPrimeFactors:
    """质因数分解测试。"""

    def test_prime_number(self) -> None:
        """质数分解。/ Prime number factorization."""
        assert prime_factors(7) == [7]

    def test_small_composite(self) -> None:
        """小合数分解。/ Small composite factorization."""
        assert prime_factors(12) == [2, 2, 3]

    def test_power_of_two(self) -> None:
        """2 的幂分解。/ Power of two factorization."""
        assert prime_factors(8) == [2, 2, 2]

    def test_power_of_three(self) -> None:
        """3 的幂分解。/ Power of three factorization."""
        assert prime_factors(9) == [3, 3]

    def test_large_composite(self) -> None:
        """大合数分解。/ Large composite factorization."""
        assert prime_factors(60) == [2, 2, 3, 5]

    def test_two(self) -> None:
        """2 的分解。/ Factorization of 2."""
        assert prime_factors(2) == [2]

    def test_three(self) -> None:
        """3 的分解。/ Factorization of 3."""
        assert prime_factors(3) == [3]

    def test_product_of_primes(self) -> None:
        """质数乘积分解。/ Product of primes factorization."""
        result = prime_factors(2 * 3 * 5 * 7)
        assert result == [2, 3, 5, 7]
