"""带容差值测试。

Toleranced value tests.

测试 math.toleranced 模块的 Toleranced 类。
Tests Toleranced class from math.toleranced module.
"""

from __future__ import annotations

from ospf_python.math.toleranced import Toleranced

# ── Toleranced ──────────────────────────────────────────────────


class TestToleranced:
    """带容差值测试。"""

    def test_creation(self) -> None:
        """创建容差值。/ Create toleranced."""
        t = Toleranced(value=10.0, tolerance=0.5)
        assert t.value == 10.0
        assert t.tolerance == 0.5

    def test_is_close_same(self) -> None:
        """相同值接近。/ Same value is close."""
        a = Toleranced(value=10.0, tolerance=0.5)
        b = Toleranced(value=10.0, tolerance=0.5)
        assert a.is_close(b)

    def test_is_close_within(self) -> None:
        """容差内接近。/ Within tolerance is close."""
        a = Toleranced(value=10.0, tolerance=1.0)
        b = Toleranced(value=10.5, tolerance=1.0)
        assert a.is_close(b)

    def test_is_close_outside(self) -> None:
        """容差外不接近。/ Outside tolerance not close."""
        a = Toleranced(value=10.0, tolerance=0.1)
        b = Toleranced(value=20.0, tolerance=0.1)
        assert not a.is_close(b)

    def test_eq_within_tolerance(self) -> None:
        """容差内相等。/ Equal within tolerance."""
        a = Toleranced(value=10.0, tolerance=0.5)
        b = Toleranced(value=10.3, tolerance=0.5)
        assert a == b

    def test_eq_outside_tolerance(self) -> None:
        """容差外不等。/ Not equal outside tolerance."""
        a = Toleranced(value=10.0, tolerance=0.1)
        b = Toleranced(value=10.5, tolerance=0.1)
        assert a != b

    def test_eq_different_type(self) -> None:
        """不同类型不等。/ Different type not equal."""
        t = Toleranced(value=10.0, tolerance=0.5)
        assert t.__eq__("not toleranced") is NotImplemented

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        t = Toleranced(value=5.0, tolerance=0.1)
        assert t.value == 5.0
        assert t.tolerance == 0.1
