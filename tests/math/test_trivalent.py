"""三值逻辑测试。

Trivalent (three-valued) logic tests.

测试 math.trivalent 模块的 Trivalent、BalancedTrivalent
及其逻辑运算函数。
Tests Trivalent, BalancedTrivalent and their logic
operation functions from math.trivalent module.
"""

from __future__ import annotations

from ospf_python.math.trivalent import (
    BalancedTrivalent,
    Trivalent,
    and_,
    balanced_and,
    balanced_not,
    balanced_or,
    not_,
    or_,
)

# ── Trivalent enum ──────────────────────────────────────────────


class TestTrivalentEnum:
    """Trivalent 枚举测试。"""

    def test_values(self) -> None:
        """枚举值。/ Enum values."""
        assert Trivalent.TRUE.value == "true"
        assert Trivalent.FALSE.value == "false"
        assert Trivalent.UNKNOWN.value == "unknown"

    def test_unique(self) -> None:
        """值唯一。/ Values unique."""
        values = [e.value for e in Trivalent]
        assert len(values) == len(set(values))


# ── Trivalent AND ───────────────────────────────────────────────


class TestTrivalentAnd:
    """三值逻辑与运算测试。"""

    def test_true_and_true(self) -> None:
        """真 AND 真 = 真。/ True AND True = True."""
        assert and_(Trivalent.TRUE, Trivalent.TRUE) == Trivalent.TRUE

    def test_true_and_false(self) -> None:
        """真 AND 假 = 假。/ True AND False = False."""
        assert and_(Trivalent.TRUE, Trivalent.FALSE) == Trivalent.FALSE

    def test_false_and_unknown(self) -> None:
        """假 AND 未知 = 假。/ False AND Unknown = False."""
        assert and_(Trivalent.FALSE, Trivalent.UNKNOWN) == Trivalent.FALSE

    def test_true_and_unknown(self) -> None:
        """真 AND 未知 = 未知。/ True AND Unknown = Unknown."""
        assert and_(Trivalent.TRUE, Trivalent.UNKNOWN) == Trivalent.UNKNOWN

    def test_unknown_and_unknown(self) -> None:
        """未知 AND 未知 = 未知。/ Unknown AND Unknown = Unknown."""
        result = and_(Trivalent.UNKNOWN, Trivalent.UNKNOWN)
        assert result == Trivalent.UNKNOWN


# ── Trivalent OR ────────────────────────────────────────────────


class TestTrivalentOr:
    """三值逻辑或运算测试。"""

    def test_true_or_false(self) -> None:
        """真 OR 假 = 真。/ True OR False = True."""
        assert or_(Trivalent.TRUE, Trivalent.FALSE) == Trivalent.TRUE

    def test_false_or_false(self) -> None:
        """假 OR 假 = 假。/ False OR False = False."""
        assert or_(Trivalent.FALSE, Trivalent.FALSE) == Trivalent.FALSE

    def test_false_or_unknown(self) -> None:
        """假 OR 未知 = 未知。/ False OR Unknown = Unknown."""
        assert or_(Trivalent.FALSE, Trivalent.UNKNOWN) == Trivalent.UNKNOWN

    def test_true_or_unknown(self) -> None:
        """真 OR 未知 = 真。/ True OR Unknown = True."""
        assert or_(Trivalent.TRUE, Trivalent.UNKNOWN) == Trivalent.TRUE


# ── Trivalent NOT ───────────────────────────────────────────────


class TestTrivalentNot:
    """三值逻辑非运算测试。"""

    def test_not_true(self) -> None:
        """NOT 真 = 假。/ NOT True = False."""
        assert not_(Trivalent.TRUE) == Trivalent.FALSE

    def test_not_false(self) -> None:
        """NOT 假 = 真。/ NOT False = True."""
        assert not_(Trivalent.FALSE) == Trivalent.TRUE

    def test_not_unknown(self) -> None:
        """NOT 未知 = 未知。/ NOT Unknown = Unknown."""
        assert not_(Trivalent.UNKNOWN) == Trivalent.UNKNOWN


# ── BalancedTrivalent ───────────────────────────────────────────


class TestBalancedTrivalent:
    """平衡三值逻辑测试。"""

    def test_values(self) -> None:
        """枚举值。/ Enum values."""
        assert BalancedTrivalent.TRUE.value == "true"
        assert BalancedTrivalent.FALSE.value == "false"
        assert BalancedTrivalent.BALANCED.value == "balanced"

    def test_balanced_and(self) -> None:
        """平衡 AND 运算。/ Balanced AND operation."""
        assert (
            balanced_and(
                BalancedTrivalent.TRUE,
                BalancedTrivalent.BALANCED,
            )
            == BalancedTrivalent.BALANCED
        )

    def test_balanced_or(self) -> None:
        """平衡 OR 运算。/ Balanced OR operation."""
        assert (
            balanced_or(
                BalancedTrivalent.FALSE,
                BalancedTrivalent.BALANCED,
            )
            == BalancedTrivalent.BALANCED
        )

    def test_balanced_not(self) -> None:
        """平衡 NOT 运算。/ Balanced NOT operation."""
        assert (
            balanced_not(
                BalancedTrivalent.BALANCED,
            )
            == BalancedTrivalent.BALANCED
        )

    def test_balanced_not_true(self) -> None:
        """平衡 NOT 真 = 假。/ Balanced NOT True = False."""
        assert (
            balanced_not(
                BalancedTrivalent.TRUE,
            )
            == BalancedTrivalent.FALSE
        )
