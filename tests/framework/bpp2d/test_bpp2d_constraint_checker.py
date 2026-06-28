"""BPP2D 约束检查器行为测试 / BPP2D constraint checker behavioral tests.

测试 ConstraintChecker 的边缘场景。
Test ConstraintChecker edge cases.
"""

from __future__ import annotations

from ospf_python.framework.bpp2d.domain.constraint.model.geometric_constraint import (
    GeometricConstraint,
)
from ospf_python.framework.bpp2d.domain.constraint.model.weight_constraint import (
    WeightConstraint,
)
from ospf_python.framework.bpp2d.domain.item.model.packing_result import (
    PackingResult,
)
from ospf_python.framework.bpp2d.domain.service.constraint_checker import (
    CheckResult,
    ConstraintChecker,
)


class TestConstraintCheckerEdgeCases:
    """约束检查器边缘场景测试 / Constraint checker edge case tests."""

    def test_validate_solution_with_violation(self) -> None:
        """方案验证失败 / Solution validation fails."""
        checker = ConstraintChecker.create()
        placed = (
            PackingResult.create(
                item_key="r1",
                x=0.0,
                y=0.0,
                placed_width=100.0,
                placed_height=100.0,
            ),
        )
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            min_x=0.0,
            max_x=50.0,
            min_y=0.0,
            max_y=50.0,
        )
        result = checker.validate_solution(
            constraints=(gc,),
            placed=placed,
            item_weights={},
        )
        assert result.is_failed()

    def test_check_geometric_with_item_not_applicable(self) -> None:
        """几何约束不适用于物品时通过 / Geometric constraint passes when item not applicable."""
        checker = ConstraintChecker.create()
        placed = (
            PackingResult.create(
                item_key="r3",
                x=0.0,
                y=0.0,
                placed_width=100.0,
                placed_height=100.0,
            ),
        )
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            item_keys=("r1", "r2"),
            max_x=10.0,
            max_y=10.0,
        )
        result = checker.check(
            constraint=gc,
            placed=placed,
            item_weights={},
        )
        assert result.is_ok()
        assert result.unwrap().satisfied is True

    def test_check_weight_with_missing_item_key(self) -> None:
        """重量约束中物品键不在权重映射中 / Weight constraint with missing item key in weights."""
        checker = ConstraintChecker.create()
        placed = (
            PackingResult.create(
                item_key="r1",
                x=0.0,
                y=0.0,
                placed_width=10.0,
                placed_height=10.0,
            ),
        )
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            max_weight=5.0,
        )
        # item_weights missing "r1" key -> defaults to 0.0
        result = checker.check(
            constraint=wc,
            placed=placed,
            item_weights={},
        )
        assert result.is_ok()
        assert result.unwrap().satisfied is True  # 0.0 <= 5.0

    def test_check_weight_item_not_applicable(self) -> None:
        """重量约束不适用于物品 / Weight constraint with non-applicable item."""
        checker = ConstraintChecker.create()
        placed = (
            PackingResult.create(
                item_key="r3",
                x=0.0,
                y=0.0,
                placed_width=10.0,
                placed_height=10.0,
            ),
        )
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            item_keys=("r1", "r2"),
            max_weight=1.0,
        )
        # r3 not in constraint's item_keys, so weight is not counted
        result = checker.check(
            constraint=wc,
            placed=placed,
            item_weights={"r3": 100.0},
        )
        assert result.is_ok()
        assert result.unwrap().satisfied is True

    def test_check_weight_violated_message(self) -> None:
        """重量约束违反消息包含数值 / Weight violation message contains numeric values."""
        checker = ConstraintChecker.create()
        placed = (
            PackingResult.create(
                item_key="r1",
                x=0.0,
                y=0.0,
                placed_width=10.0,
                placed_height=10.0,
            ),
        )
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            max_weight=5.0,
        )
        result = checker.check(
            constraint=wc,
            placed=placed,
            item_weights={"r1": 10.0},
        )
        assert result.is_ok()
        check_result = result.unwrap()
        assert check_result.satisfied is False
        assert "exceeds" in check_result.message

    def test_geometric_violated_message(self) -> None:
        """几何约束违反消息 / Geometric violation message."""
        checker = ConstraintChecker.create()
        placed = (
            PackingResult.create(
                item_key="r1",
                x=0.0,
                y=0.0,
                placed_width=60.0,
                placed_height=60.0,
            ),
        )
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            max_x=50.0,
            max_y=50.0,
        )
        result = checker.check(
            constraint=gc,
            placed=placed,
            item_weights={},
        )
        assert result.is_ok()
        check_result = result.unwrap()
        assert check_result.satisfied is False
        assert "violates" in check_result.message

    def test_check_result_ok_static(self) -> None:
        """CheckResult.ok() 静态方法 / CheckResult.ok() static method."""
        r = CheckResult.ok()
        assert r.satisfied is True
        assert r.message == ""

    def test_check_result_fail_static(self) -> None:
        """CheckResult.fail() 静态方法 / CheckResult.fail() static method."""
        r = CheckResult.fail(message="test failure")
        assert r.satisfied is False
        assert r.message == "test failure"

    def test_constraint_checker_create_with_tolerance(self) -> None:
        """创建带容差的检查器 / Create checker with tolerance."""
        checker = ConstraintChecker.create(tolerance=0.01)
        assert checker.tolerance == 0.01
