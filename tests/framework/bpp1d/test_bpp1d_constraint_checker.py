"""BPP1D 约束检查器行为测试 / BPP1D constraint checker behavioral tests.

测试 ConstraintChecker 的分组约束和边缘场景。
Test ConstraintChecker grouping constraints and edge cases.
"""

from __future__ import annotations

from ospf_python.framework.bpp1d.domain.constraint.model.constraint import (
    Constraint,
    ConstraintType,
)
from ospf_python.framework.bpp1d.domain.constraint.service.constraint_checker import (
    ConstraintChecker,
)
from ospf_python.framework.bpp1d.domain.item.model.bin import Bin
from ospf_python.framework.bpp1d.domain.item.model.item import Item


class TestConstraintCheckerGrouping:
    """约束检查器分组测试 / Constraint checker grouping tests."""

    def _make_bin_with_items(
        self,
        item_keys: tuple[str, ...],
        weights: tuple[float, ...],
    ) -> Bin:
        """创建含物品的箱子 / Create bin with items."""
        items = tuple(
            Item.create(
                item_key=k,
                width=1.0,
                height=1.0,
                weight=w,
            )
            for k, w in zip(item_keys, weights, strict=True)
        )
        return Bin.create(bin_key="b1", capacity=10.0, items=items)

    def test_item_grouping_all_in_bin(self) -> None:
        """分组约束：所有物品在同一箱 / Grouping: all items in same bin."""
        checker = ConstraintChecker.create()
        bin_ = self._make_bin_with_items(("x", "y"), (1.0, 1.0))
        c = Constraint.create(
            constraint_key="g1",
            constraint_type=ConstraintType.ITEM_GROUPING,
            item_keys=("x", "y"),
            max_value=0.0,
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        assert result.satisfied is True

    def test_item_grouping_none_in_bin(self) -> None:
        """分组约束：没有物品在箱中 / Grouping: no items in bin."""
        checker = ConstraintChecker.create()
        bin_ = Bin.create(bin_key="b1", capacity=10.0)
        c = Constraint.create(
            constraint_key="g1",
            constraint_type=ConstraintType.ITEM_GROUPING,
            item_keys=("x", "y"),
            max_value=0.0,
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        assert result.satisfied is True

    def test_item_grouping_partial_in_bin(self) -> None:
        """分组约束：部分物品在箱中 / Grouping: partial items in bin."""
        checker = ConstraintChecker.create()
        bin_ = self._make_bin_with_items(("x",), (1.0,))
        c = Constraint.create(
            constraint_key="g1",
            constraint_type=ConstraintType.ITEM_GROUPING,
            item_keys=("x", "y"),
            max_value=0.0,
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        assert result.satisfied is False
        assert "Grouping violated" in result.message

    def test_check_unknown_constraint_type(self) -> None:
        """未知约束类型返回 ok / Unknown constraint type returns ok."""
        checker = ConstraintChecker.create()
        bin_ = Bin.create(bin_key="b1", capacity=10.0)
        c = Constraint.create(
            constraint_key="unknown_1",
            constraint_type=ConstraintType.WEIGHT_LIMIT,
            item_keys=(),
            max_value=0.0,
        )
        # Empty bin with weight limit of 0 and no items -> 0.0 <= 0.0 + tolerance
        result = checker.check(constraint=c, bin_=bin_, items=())
        assert result.satisfied is True

    def test_check_all_with_mixed_constraints(self) -> None:
        """混合约束批量检查 / Batch check with mixed constraints."""
        checker = ConstraintChecker.create()
        bin_ = self._make_bin_with_items(("a",), (2.0,))
        constraints = (
            Constraint.weight_limit(
                constraint_key="w1",
                item_keys=("a",),
                max_weight=5.0,
            ),
            Constraint.item_exclusion(
                constraint_key="e1",
                item_keys=("a", "b"),
            ),
            Constraint.create(
                constraint_key="g1",
                constraint_type=ConstraintType.ITEM_GROUPING,
                item_keys=("a", "c"),
                max_value=0.0,
            ),
        )
        results = checker.check_all(
            constraints=constraints,
            bin_=bin_,
            items=(),
        )
        assert len(results) == 3
        # Weight: 2.0 <= 5.0 -> ok
        assert results[0].satisfied is True
        # Exclusion: only 'a' in bin -> ok
        assert results[1].satisfied is True
        # Grouping: only 'a' in bin (partial) -> violated
        assert results[2].satisfied is False

    def test_weight_limit_with_irrelevant_items(self) -> None:
        """重量限制：箱中有不在约束中的物品 / Weight limit with irrelevant items."""
        checker = ConstraintChecker.create()
        items = (
            Item.create(item_key="a", width=1.0, height=1.0, weight=10.0),
            Item.create(item_key="b", width=1.0, height=1.0, weight=10.0),
            Item.create(item_key="c", width=1.0, height=1.0, weight=10.0),
        )
        bin_ = Bin.create(bin_key="b1", capacity=10.0, items=items)
        c = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a",),  # Only 'a' is constrained
            max_weight=5.0,
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        # Only 'a' weight (10.0) exceeds 5.0
        assert result.satisfied is False

    def test_item_exclusion_with_no_constrained_items(self) -> None:
        """互斥约束：箱中没有受约束物品 / Exclusion with no constrained items."""
        checker = ConstraintChecker.create()
        items = (
            Item.create(item_key="c", width=1.0, height=1.0, weight=1.0),
        )
        bin_ = Bin.create(bin_key="b1", capacity=10.0, items=items)
        c = Constraint.item_exclusion(
            constraint_key="e1",
            item_keys=("a", "b"),
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        # No constrained items in bin -> ok
        assert result.satisfied is True
