"""值域限制工具测试。

Clamp utility tests.

测试 clamp 函数的边界和中间值行为。
Tests clamp function boundary and mid-value behavior.
"""

from __future__ import annotations

from ospf_python.math.ordinary.clamp import clamp

# ── clamp ───────────────────────────────────────────────────────


class TestClamp:
    """值域限制测试。"""

    def test_within_range(self) -> None:
        """范围内的值。/ Value within range."""
        assert clamp(5, min_val=0, max_val=10) == 5

    def test_below_min(self) -> None:
        """低于下界。/ Below minimum."""
        assert clamp(-5, min_val=0, max_val=10) == 0

    def test_above_max(self) -> None:
        """高于上界。/ Above maximum."""
        assert clamp(15, min_val=0, max_val=10) == 10

    def test_at_min(self) -> None:
        """在下界。/ At minimum."""
        assert clamp(0, min_val=0, max_val=10) == 0

    def test_at_max(self) -> None:
        """在上界。/ At maximum."""
        assert clamp(10, min_val=0, max_val=10) == 10

    def test_float_clamp(self) -> None:
        """浮点限制。/ Float clamp."""
        assert clamp(0.5, min_val=0.0, max_val=1.0) == 0.5

    def test_float_below(self) -> None:
        """浮点低于下界。/ Float below minimum."""
        assert clamp(-0.5, min_val=0.0, max_val=1.0) == 0.0

    def test_negative_range(self) -> None:
        """负范围。/ Negative range."""
        assert clamp(0, min_val=-10, max_val=-1) == -1

    def test_single_point_range(self) -> None:
        """单点范围。/ Single point range."""
        assert clamp(5, min_val=3, max_val=3) == 3
