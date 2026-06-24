"""缩放因子测试。

Scale factor tests.

测试 math.scale 模块的 Scale 类。
Tests Scale class from math.scale module.
"""

from __future__ import annotations

from ospf_python.math.scale import Scale

# ── Scale ───────────────────────────────────────────────────────


class TestScale:
    """缩放因子测试。"""

    def test_creation(self) -> None:
        """创建缩放因子。/ Create scale."""
        s = Scale(factor=2.5)
        assert s.factor == 2.5

    def test_apply(self) -> None:
        """应用缩放。/ Apply scale."""
        s = Scale(factor=3.0)
        assert s.apply(4.0) == 12.0

    def test_apply_identity(self) -> None:
        """单位缩放。/ Identity scale."""
        s = Scale(factor=1.0)
        assert s.apply(5.0) == 5.0

    def test_apply_zero(self) -> None:
        """零缩放。/ Zero scale."""
        s = Scale(factor=0.0)
        assert s.apply(100.0) == 0.0

    def test_inverse(self) -> None:
        """逆缩放。/ Inverse scale."""
        s = Scale(factor=4.0)
        inv = s.inverse()
        assert inv.factor == 0.25

    def test_inverse_two(self) -> None:
        """2 的逆缩放。/ Inverse of 2."""
        s = Scale(factor=2.0)
        inv = s.inverse()
        assert inv.factor == 0.5

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        s = Scale(factor=5.0)
        assert s.factor == 5.0

    def test_equality(self) -> None:
        """相等比较。/ Equality."""
        a = Scale(factor=3.0)
        b = Scale(factor=3.0)
        assert a == b

    def test_inequality(self) -> None:
        """不等比较。/ Inequality."""
        a = Scale(factor=3.0)
        b = Scale(factor=4.0)
        assert a != b
