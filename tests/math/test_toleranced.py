"""math.toleranced 转发测试。

Tests for the math.toleranced re-export.

该模块只转发 ``math.ordinary.toleranced.Toleranced``；这里钉住"同一个类"，并钉住
相等与哈希的一致契约，防止再出现一份按容差比较却按精确值哈希的副本。

The module only re-exports ``math.ordinary.toleranced.Toleranced``. These tests pin the class
identity and the equality/hash contract, so a duplicate that compares within tolerance but hashes
exact fields cannot come back.
"""

from __future__ import annotations

from ospf_python.math import ordinary
from ospf_python.math.toleranced import Toleranced


class TestTolerancedReExport:
    """转发与契约 / Re-export and contract."""

    def test_is_the_single_implementation(self) -> None:
        """必须是同一个类。/ Must be the same class."""
        assert Toleranced is ordinary.Toleranced

    def test_equal_values_share_a_hash(self) -> None:
        """相等必须同哈希，否则 set/dict 会失效。

        Equal values must share a hash, otherwise sets and dicts break.
        """
        a = Toleranced(value=10.0, tolerance=0.5)
        b = Toleranced(value=10.0, tolerance=0.5)
        assert a == b
        assert hash(a) == hash(b)
        assert b in {a}
        assert {a: "x"}[b] == "x"

    def test_equality_is_exact_not_tolerance_based(self) -> None:
        """容差内的值不相等；容差比较用 contains / overlaps。

        Values within tolerance are not equal; use contains / overlaps for that.
        """
        a = Toleranced(value=10.0, tolerance=0.5)
        b = Toleranced(value=10.3, tolerance=0.5)
        assert a != b
        assert a.contains(10.3)
        assert a.overlaps(b)
