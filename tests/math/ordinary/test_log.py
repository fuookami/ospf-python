"""通用对数运算测试。

Generic logarithm tests.

测试 log_base 函数。
Tests log_base function.
"""

from __future__ import annotations

import math

from ospf_python.math.ordinary.log import log_base

# ── log_base ────────────────────────────────────────────────────


class TestLogBase:
    """通用对数测试。"""

    def test_log2(self) -> None:
        """以 2 为底。/ Base 2."""
        assert math.isclose(log_base(8.0, 2.0), 3.0)

    def test_log10(self) -> None:
        """以 10 为底。/ Base 10."""
        assert math.isclose(log_base(1000.0, 10.0), 3.0)

    def test_natural_log(self) -> None:
        """以 e 为底。/ Base e."""
        assert math.isclose(log_base(math.e, math.e), 1.0)

    def test_log_base_one(self) -> None:
        """对数值为 1。/ Log value is 1."""
        assert math.isclose(log_base(5.0, 5.0), 1.0)

    def test_log_base_fraction(self) -> None:
        """分数结果。/ Fractional result."""
        assert math.isclose(log_base(4.0, 8.0), 2.0 / 3.0)

    def test_log_base_large(self) -> None:
        """大值对数。/ Large value log."""
        assert math.isclose(log_base(1024.0, 2.0), 10.0)
