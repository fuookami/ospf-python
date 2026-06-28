"""BPP1D 约束逻辑测试 / BPP1D constraint logic tests.

测试约束创建、类型判断和约束检查器的行为。
Test constraint creation, type checks, and
constraint checker behavior in BPP1D.
"""

from __future__ import annotations

from ospf_python.framework.bpp1d.domain.constraint.model.constraint import (
    Constraint,
    ConstraintType,
)
from ospf_python.framework.bpp1d.domain.constraint.service.constraint_checker import (
    CheckResult,
    ConstraintChecker,
)
from ospf_python.framework.bpp1d.domain.item.model.bin import Bin
from ospf_python.framework.bpp1d.domain.item.model.item import Item


class TestConstraintModel:
    """约束模型测试 / Constraint model tests."""

    def test_create_weight_limit(self) -> None:
        """创建重量限制约束 / Create weight limit constraint."""
        c = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a", "b"),
            max_weight=10.0,
        )
        assert c.constraint_key == "w1"
        assert c.constraint_type == ConstraintType.WEIGHT_LIMIT
        assert c.max_value == 10.0
        assert c.is_weight_limit is True
        assert c.is_item_exclusion is False

    def test_create_item_exclusion(self) -> None:
        """创建物品互斥约束 / Create item exclusion constraint."""
        c = Constraint.item_exclusion(
            constraint_key="e1",
            item_keys=("a", "b"),
        )
        assert c.constraint_type == ConstraintType.ITEM_EXCLUSION
        assert c.is_item_exclusion is True
        assert c.is_item_grouping is False

    def test_create_generic_constraint(self) -> None:
        """创建通用约束 / Create generic constraint."""
        c = Constraint.create(
            constraint_key="g1",
            constraint_type=ConstraintType.ITEM_GROUPING,
            item_keys=("x", "y"),
            max_value=0.0,
        )
        assert c.is_item_grouping is True


class TestCheckResult:
    """检查结果测试 / Check result tests."""

    def test_ok_result(self) -> None:
        """成功检查结果 / Ok check result."""
        r = CheckResult.ok()
        assert r.satisfied is True
        assert r.message == ""

    def test_fail_result(self) -> None:
        """失败检查结果 / Fail check result."""
        r = CheckResult.fail(message="weight exceeded")
        assert r.satisfied is False
        assert "weight exceeded" in r.message


class TestConstraintChecker:
    """约束检查器测试 / Constraint checker tests."""

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

    def test_weight_limit_satisfied(self) -> None:
        """重量限制满足 / Weight limit satisfied."""
        checker = ConstraintChecker.create()
        bin_ = self._make_bin_with_items(("a", "b"), (2.0, 3.0))
        c = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a", "b"),
            max_weight=10.0,
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        assert result.satisfied is True

    def test_weight_limit_violated(self) -> None:
        """重量限制违反 / Weight limit violated."""
        checker = ConstraintChecker.create()
        bin_ = self._make_bin_with_items(("a", "b"), (5.0, 6.0))
        c = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a", "b"),
            max_weight=10.0,
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        assert result.satisfied is False
        assert "exceeds" in result.message

    def test_item_exclusion_satisfied(self) -> None:
        """物品互斥满足 / Item exclusion satisfied."""
        checker = ConstraintChecker.create()
        bin_ = self._make_bin_with_items(("a",), (1.0,))
        c = Constraint.item_exclusion(
            constraint_key="e1",
            item_keys=("a", "b"),
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        assert result.satisfied is True

    def test_item_exclusion_violated(self) -> None:
        """物品互斥违反 / Item exclusion violated."""
        checker = ConstraintChecker.create()
        bin_ = self._make_bin_with_items(("a", "b"), (1.0, 1.0))
        c = Constraint.item_exclusion(
            constraint_key="e1",
            item_keys=("a", "b"),
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        assert result.satisfied is False
        assert "Exclusion" in result.message

    def test_check_all(self) -> None:
        """批量检查约束 / Batch check constraints."""
        checker = ConstraintChecker.create()
        bin_ = self._make_bin_with_items(("a",), (1.0,))
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
        )
        results = checker.check_all(
            constraints=constraints,
            bin_=bin_,
            items=(),
        )
        assert len(results) == 2
        assert all(r.satisfied for r in results)

    def test_custom_tolerance(self) -> None:
        """自定义容差 / Custom tolerance."""
        checker = ConstraintChecker.create(tolerance=0.1)
        assert checker.tolerance == 0.1


# ============================================================
# Deep behavioral: capacity boundary & constraint edge cases
# ============================================================


class TestCapacityBoundaryBehavior:
    """容量边界行为测试。/ Capacity boundary behavioral tests."""

    def test_weight_limit_at_boundary(self) -> None:
        """重量恰好在限制上。/ Weight exactly at limit."""
        checker = ConstraintChecker.create()
        items = tuple(
            Item.create(item_key=k, width=1.0, height=1.0, weight=w)
            for k, w in (("a", 5.0), ("b", 5.0))
        )
        bin_ = Bin.create(bin_key="b1", capacity=10.0, items=items)
        c = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a", "b"),
            max_weight=10.0,
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        assert result.satisfied is True  # 恰好 10.0 = 10.0

    def test_weight_limit_one_epsilon_over(self) -> None:
        """重量超出限制极小值。/ Weight one epsilon over limit."""
        checker = ConstraintChecker.create()
        items = tuple(
            Item.create(item_key=k, width=1.0, height=1.0, weight=w)
            for k, w in (("a", 5.0), ("b", 5.01))
        )
        bin_ = Bin.create(bin_key="b1", capacity=10.0, items=items)
        c = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a", "b"),
            max_weight=10.0,
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        assert result.satisfied is False

    def test_item_exclusion_single_item_satisfied(self) -> None:
        """互斥约束仅一个物品时满足。/ Exclusion satisfied with single item."""
        checker = ConstraintChecker.create()
        items = (Item.create(item_key="a", width=1.0, height=1.0, weight=1.0),)
        bin_ = Bin.create(bin_key="b1", capacity=10.0, items=items)
        c = Constraint.item_exclusion(
            constraint_key="e1",
            item_keys=("a", "b"),
        )
        result = checker.check(constraint=c, bin_=bin_, items=())
        assert result.satisfied is True

    def test_empty_bin_all_constraints_satisfied(self) -> None:
        """空箱所有约束满足。/ All constraints satisfied on empty bin."""
        checker = ConstraintChecker.create()
        bin_ = Bin.create(bin_key="b1", capacity=10.0)
        constraints = (
            Constraint.weight_limit(constraint_key="w1", item_keys=("a",), max_weight=5.0),
            Constraint.item_exclusion(constraint_key="e1", item_keys=("a", "b")),
        )
        results = checker.check_all(constraints=constraints, bin_=bin_, items=())
        assert all(r.satisfied for r in results)

    def test_item_grouping_constraint_type(self) -> None:
        """物品分组约束类型。/ Item grouping constraint type."""
        c = Constraint.create(
            constraint_key="g1",
            constraint_type=ConstraintType.ITEM_GROUPING,
            item_keys=("x", "y"),
            max_value=0.0,
        )
        assert c.is_item_grouping is True
        assert c.is_weight_limit is False
        assert c.is_item_exclusion is False
