"""素数工具测试。

Prime number utility tests.

测试 is_prime、primes_up_to、nth_prime 函数。
Tests is_prime, primes_up_to, nth_prime functions.
"""

from __future__ import annotations

from ospf_python.math.ordinary.prime import (
    is_prime,
    nth_prime,
    primes_up_to,
)

# ── is_prime ────────────────────────────────────────────────────


class TestIsPrime:
    """素数判断测试。"""

    def test_small_primes(self) -> None:
        """小素数。/ Small primes."""
        assert is_prime(2)
        assert is_prime(3)
        assert is_prime(5)
        assert is_prime(7)

    def test_non_primes(self) -> None:
        """非素数。/ Non-primes."""
        assert not is_prime(0)
        assert not is_prime(1)
        assert not is_prime(4)
        assert not is_prime(6)

    def test_larger_primes(self) -> None:
        """较大素数。/ Larger primes."""
        assert is_prime(13)
        assert is_prime(17)
        assert is_prime(19)

    def test_larger_non_primes(self) -> None:
        """较大非素数。/ Larger non-primes."""
        assert not is_prime(15)
        assert not is_prime(21)
        assert not is_prime(25)

    def test_negative(self) -> None:
        """负数非素数。/ Negative non-prime."""
        assert not is_prime(-5)


# ── primes_up_to ────────────────────────────────────────────────


class TestPrimesUpTo:
    """素数列表测试。"""

    def test_primes_up_to_10(self) -> None:
        """10 以内的素数。/ Primes up to 10."""
        assert primes_up_to(10) == [2, 3, 5, 7]

    def test_primes_up_to_20(self) -> None:
        """20 以内的素数。/ Primes up to 20."""
        result = primes_up_to(20)
        assert result == [2, 3, 5, 7, 11, 13, 17, 19]

    def test_primes_up_to_1(self) -> None:
        """1 以内无素数。/ No primes up to 1."""
        assert primes_up_to(1) == []

    def test_primes_up_to_2(self) -> None:
        """2 以内的素数。/ Primes up to 2."""
        assert primes_up_to(2) == [2]


# ── nth_prime ───────────────────────────────────────────────────


class TestNthPrime:
    """第 n 个素数测试。"""

    def test_first_prime(self) -> None:
        """第一个素数。/ First prime."""
        assert nth_prime(1) == 2

    def test_second_prime(self) -> None:
        """第二个素数。/ Second prime."""
        assert nth_prime(2) == 3

    def test_fifth_prime(self) -> None:
        """第五个素数。/ Fifth prime."""
        assert nth_prime(5) == 11

    def test_tenth_prime(self) -> None:
        """第十个素数。/ Tenth prime."""
        assert nth_prime(10) == 29
