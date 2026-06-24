"""最小公倍数测试。

Least common multiple tests.

测试 lcm 函数。
Tests lcm function.
"""

from __future__ import annotations

from ospf_python.math.ordinary.lcm import lcm

# ── lcm ─────────────────────────────────────────────────────────


class TestLcm:
    """最小公倍数测试。"""

    def test_coprime(self) -> None:
        """互质数 LCM。/ Coprime LCM."""
        assert lcm(3, 5) == 15

    def test_common_multiple(self) -> None:
        """有公倍数。/ Common multiple."""
        assert lcm(4, 6) == 12

    def test_same_number(self) -> None:
        """相同数 LCM。/ Same number LCM."""
        assert lcm(5, 5) == 5

    def test_one_and_n(self) -> None:
        """1 和 n。/ 1 and n."""
        assert lcm(1, 42) == 42

    def test_zero(self) -> None:
        """零的 LCM。/ LCM with zero."""
        assert lcm(0, 5) == 0

    def test_large_numbers(self) -> None:
        """大数 LCM。/ Large number LCM."""
        assert lcm(12, 18) == 36
