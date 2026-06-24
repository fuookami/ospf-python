"""常用数学类型模块测试。

Common math types module tests.

测试 Trivalent、Scale、Toleranced 等常用数学类型。
Tests Trivalent, Scale, Toleranced common math types.
"""

from __future__ import annotations

from ospf_python.math.ordinary.scale import Scale
from ospf_python.math.ordinary.toleranced import Toleranced
from ospf_python.math.ordinary.trivalent import Trivalent

# ── Trivalent ─────────────────────────────────────────────────────


class TestTrivalent:
    """三值逻辑测试。"""

    def test_true_value(self) -> None:
        """真值。/ True value."""
        assert Trivalent.TRUE.is_true
        assert not Trivalent.TRUE.is_false
        assert not Trivalent.TRUE.is_unknown

    def test_false_value(self) -> None:
        """假值。/ False value."""
        assert Trivalent.FALSE.is_false
        assert not Trivalent.FALSE.is_true
        assert not Trivalent.FALSE.is_unknown

    def test_unknown_value(self) -> None:
        """未知值。/ Unknown value."""
        assert Trivalent.UNKNOWN.is_unknown
        assert not Trivalent.UNKNOWN.is_true
        assert not Trivalent.UNKNOWN.is_false

    def test_and_true_true(self) -> None:
        """真 AND 真 = 真。/ True AND True = True."""
        assert (Trivalent.TRUE & Trivalent.TRUE).is_true

    def test_and_true_false(self) -> None:
        """真 AND 假 = 假。/ True AND False = False."""
        assert (Trivalent.TRUE & Trivalent.FALSE).is_false

    def test_and_unknown(self) -> None:
        """真 AND 未知 = 未知。/ True AND Unknown = Unknown."""
        result = Trivalent.TRUE & Trivalent.UNKNOWN
        assert result.is_unknown

    def test_and_false_unknown(self) -> None:
        """假 AND 未知 = 假。/ False AND Unknown = False."""
        result = Trivalent.FALSE & Trivalent.UNKNOWN
        assert result.is_false

    def test_or_true_false(self) -> None:
        """真 OR 假 = 真。/ True OR False = True."""
        assert (Trivalent.TRUE | Trivalent.FALSE).is_true

    def test_or_false_false(self) -> None:
        """假 OR 假 = 假。/ False OR False = False."""
        assert (Trivalent.FALSE | Trivalent.FALSE).is_false

    def test_or_unknown(self) -> None:
        """假 OR 未知 = 未知。/ False OR Unknown = Unknown."""
        result = Trivalent.FALSE | Trivalent.UNKNOWN
        assert result.is_unknown

    def test_or_true_unknown(self) -> None:
        """真 OR 未知 = 真。/ True OR Unknown = True."""
        result = Trivalent.TRUE | Trivalent.UNKNOWN
        assert result.is_true

    def test_not_true(self) -> None:
        """NOT 真 = 假。/ NOT True = False."""
        assert (~Trivalent.TRUE).is_false

    def test_not_false(self) -> None:
        """NOT 假 = 真。/ NOT False = True."""
        assert (~Trivalent.FALSE).is_true

    def test_not_unknown(self) -> None:
        """NOT 未知 = 未知。/ NOT Unknown = Unknown."""
        assert (~Trivalent.UNKNOWN).is_unknown

    def test_to_bool(self) -> None:
        """转换为 bool。/ Convert to bool."""
        assert Trivalent.TRUE.to_bool() is True
        assert Trivalent.FALSE.to_bool() is False
        assert Trivalent.UNKNOWN.to_bool() is None


# ── Scale ─────────────────────────────────────────────────────────


class TestScale:
    """比例类型测试。"""

    def test_identity(self) -> None:
        """单位比例。/ Identity scale."""
        s = Scale.identity()
        assert s.value == 1.0

    def test_zero(self) -> None:
        """零比例。/ Zero scale."""
        s = Scale.zero()
        assert s.value == 0.0

    def test_multiply(self) -> None:
        """比例复合。/ Scale composition."""
        s = Scale(2.0) * Scale(3.0)
        assert s == Scale(6.0)

    def test_divide(self) -> None:
        """比例除法。/ Scale division."""
        s = Scale(10.0) / Scale(2.0)
        assert s == Scale(5.0)

    def test_divide_by_zero(self) -> None:
        """除以零比例。/ Divide by zero scale."""
        s = Scale(5.0) / Scale(0.0)
        assert s == Scale(0.0)

    def test_apply(self) -> None:
        """应用比例。/ Apply scale."""
        assert Scale(2.5).apply(4.0) == 10.0

    def test_inverse(self) -> None:
        """逆比例。/ Inverse scale."""
        s = Scale(4.0).inverse()
        assert s == Scale(0.25)

    def test_inverse_zero(self) -> None:
        """零比例的逆。/ Inverse of zero scale."""
        s = Scale(0.0).inverse()
        assert s == Scale(0.0)

    def test_equality(self) -> None:
        """相等比较。/ Equality."""
        assert Scale(1.0) == Scale(1.0)
        assert Scale(1.0) != Scale(2.0)

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        assert repr(Scale(2.5)) == "Scale(2.5)"

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        s = Scale(1.0)
        assert s.value == 1.0

    def test_hash(self) -> None:
        """哈希值。/ Hash value."""
        a = Scale(3.0)
        b = Scale(3.0)
        assert hash(a) == hash(b)


# ── Toleranced ────────────────────────────────────────────────────


class TestToleranced:
    """容差值测试。"""

    def test_basic_creation(self) -> None:
        """基本创建。/ Basic creation."""
        t = Toleranced(value=10.0, tolerance=0.5)
        assert t.value == 10.0
        assert t.tolerance == 0.5

    def test_bounds(self) -> None:
        """边界值。/ Bound values."""
        t = Toleranced(value=10.0, tolerance=0.5)
        assert t.lower_bound == 9.5
        assert t.upper_bound == 10.5

    def test_contains_within(self) -> None:
        """包含在容差内。/ Contains within tolerance."""
        t = Toleranced(value=10.0, tolerance=0.5)
        assert t.contains(10.0)
        assert t.contains(10.3)
        assert t.contains(9.7)

    def test_contains_outside(self) -> None:
        """不包含在容差外。/ Not contains outside tolerance."""
        t = Toleranced(value=10.0, tolerance=0.5)
        assert not t.contains(10.6)
        assert not t.contains(9.4)

    def test_contains_boundary(self) -> None:
        """容差边界值。/ Tolerance boundary value."""
        t = Toleranced(value=10.0, tolerance=0.5)
        assert t.contains(10.5)
        assert t.contains(9.5)

    def test_overlaps_true(self) -> None:
        """重叠。/ Overlaps."""
        a = Toleranced(value=10.0, tolerance=1.0)
        b = Toleranced(value=11.0, tolerance=1.0)
        assert a.overlaps(b)

    def test_overlaps_false(self) -> None:
        """不重叠。/ No overlap."""
        a = Toleranced(value=10.0, tolerance=0.5)
        b = Toleranced(value=20.0, tolerance=0.5)
        assert not a.overlaps(b)

    def test_overlaps_touching(self) -> None:
        """刚好接触。/ Just touching."""
        a = Toleranced(value=10.0, tolerance=1.0)
        b = Toleranced(value=12.0, tolerance=1.0)
        assert a.overlaps(b)

    def test_addition(self) -> None:
        """容差值加法。/ Toleranced addition."""
        a = Toleranced(value=10.0, tolerance=0.5)
        b = Toleranced(value=5.0, tolerance=0.3)
        result = a + b
        assert result.value == 15.0
        assert result.tolerance == 0.8

    def test_scalar_multiply(self) -> None:
        """标量乘法。/ Scalar multiplication."""
        t = Toleranced(value=10.0, tolerance=0.5)
        result = t * 2.0
        assert result.value == 20.0
        assert result.tolerance == 1.0

    def test_negative_tolerance_clamped(self) -> None:
        """负容差截断到零。/ Negative tolerance clamped."""
        t = Toleranced(value=10.0, tolerance=-1.0)
        assert t.tolerance == 0.0

    def test_equality(self) -> None:
        """相等比较。/ Equality."""
        a = Toleranced(value=10.0, tolerance=0.5)
        b = Toleranced(value=10.0, tolerance=0.5)
        assert a == b

    def test_inequality(self) -> None:
        """不等比较。/ Inequality."""
        a = Toleranced(value=10.0, tolerance=0.5)
        b = Toleranced(value=10.0, tolerance=0.3)
        assert a != b

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        t = Toleranced(value=5.0, tolerance=0.1)
        assert "Toleranced" in repr(t)

    def test_hash(self) -> None:
        """哈希值。/ Hash value."""
        a = Toleranced(value=10.0, tolerance=0.5)
        b = Toleranced(value=10.0, tolerance=0.5)
        assert hash(a) == hash(b)

    def test_scalar_multiply_negative(self) -> None:
        """负标量乘法。/ Negative scalar multiplication."""
        t = Toleranced(value=10.0, tolerance=0.5)
        result = t * -2.0
        assert result.value == -20.0
        assert result.tolerance == 1.0
