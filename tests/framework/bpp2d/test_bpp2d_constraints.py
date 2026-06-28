"""BPP2D 约束逻辑测试 / BPP2D constraint logic tests.

测试几何约束、重量约束和约束检查器。
Test geometric constraints, weight constraints,
and constraint checker in BPP2D.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.bpp2d.domain.constraint.model.constraint_base import (
    ConstraintType,
)
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
    ConstraintChecker,
)


class TestGeometricConstraint:
    """几何约束测试 / Geometric constraint tests."""

    def test_create_geometric_constraint(self) -> None:
        """创建几何约束 / Create geometric constraint."""
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            item_keys=("r1", "r2"),
            min_x=0.0,
            max_x=100.0,
            min_y=0.0,
            max_y=50.0,
            no_overlap=True,
        )
        assert gc.constraint_key == "geo_1"
        assert gc.constraint_type == ConstraintType.GEOMETRIC
        assert gc.min_x == 0.0
        assert gc.max_x == 100.0
        assert gc.no_overlap is True

    def test_applies_to_specific_items(self) -> None:
        """适用于特定物品 / Applies to specific items."""
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            item_keys=("r1", "r2"),
        )
        assert gc.applies_to("r1") is True
        assert gc.applies_to("r3") is False

    def test_applies_to_all_when_empty(self) -> None:
        """空 item_keys 适用于所有 / Empty item_keys applies to all."""
        gc = GeometricConstraint.create(constraint_key="geo_1")
        assert gc.applies_to("any_item") is True

    def test_check_placement_valid(self) -> None:
        """有效放置检查 / Valid placement check."""
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            min_x=0.0,
            max_x=100.0,
            min_y=0.0,
            max_y=100.0,
        )
        assert gc.check_placement(10.0, 10.0, 20.0, 20.0) is True

    def test_check_placement_out_of_bounds(self) -> None:
        """越界放置检查 / Out of bounds placement."""
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            min_x=0.0,
            max_x=50.0,
            min_y=0.0,
            max_y=50.0,
        )
        # Beyond max_x
        assert gc.check_placement(40.0, 10.0, 20.0, 20.0) is False
        # Beyond max_y
        assert gc.check_placement(10.0, 40.0, 20.0, 20.0) is False
        # Before min_x
        assert gc.check_placement(-1.0, 10.0, 20.0, 20.0) is False

    def test_allowed_dimensions(self) -> None:
        """允许的尺寸范围 / Allowed dimensions."""
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            min_x=10.0,
            max_x=60.0,
            min_y=20.0,
            max_y=80.0,
        )
        assert gc.allowed_width == 50.0
        assert gc.allowed_height == 60.0

    def test_allowed_dimensions_infinite(self) -> None:
        """无限尺寸范围 / Infinite dimensions."""
        gc = GeometricConstraint.create(constraint_key="geo_1")
        assert gc.allowed_width == float("inf")
        assert gc.allowed_height == float("inf")


class TestWeightConstraint:
    """重量约束测试 / Weight constraint tests."""

    def test_create_weight_constraint(self) -> None:
        """创建重量约束 / Create weight constraint."""
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            item_keys=("r1",),
            max_weight=50.0,
        )
        assert wc.constraint_key == "wt_1"
        assert wc.constraint_type == ConstraintType.WEIGHT
        assert wc.max_weight == 50.0

    def test_check_weight_within_limit(self) -> None:
        """重量在限制内 / Weight within limit."""
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            max_weight=50.0,
        )
        assert wc.check_weight(30.0) is True
        assert wc.check_weight(30.0, 10.0) is True
        assert wc.check_weight(50.0) is True

    def test_check_weight_exceeded(self) -> None:
        """重量超出限制 / Weight exceeded."""
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            max_weight=50.0,
        )
        assert wc.check_weight(51.0) is False
        assert wc.check_weight(40.0, 15.0) is False

    def test_remaining_capacity(self) -> None:
        """剩余容量 / Remaining capacity."""
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            max_weight=50.0,
        )
        assert wc.remaining_capacity(30.0) == 20.0
        assert wc.remaining_capacity(50.0) == 0.0
        assert wc.remaining_capacity(60.0) == 0.0

    def test_applies_to_specific_items(self) -> None:
        """适用于特定物品 / Applies to specific items."""
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            item_keys=("r1", "r2"),
            max_weight=50.0,
        )
        assert wc.applies_to("r1") is True
        assert wc.applies_to("r3") is False

    def test_applies_to_all_when_empty(self) -> None:
        """空 item_keys 适用于所有 / Empty applies to all."""
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            max_weight=50.0,
        )
        assert wc.applies_to("any") is True


class TestConstraintChecker:
    """约束检查器测试 / Constraint checker tests."""

    def _make_placed(self) -> tuple[PackingResult, ...]:
        """创建放置结果 / Create placed results."""
        return (
            PackingResult.create(
                item_key="r1",
                x=10.0,
                y=10.0,
                placed_width=20.0,
                placed_height=20.0,
            ),
            PackingResult.create(
                item_key="r2",
                x=50.0,
                y=50.0,
                placed_width=10.0,
                placed_height=10.0,
            ),
        )

    def test_check_geometric_ok(self) -> None:
        """几何约束满足 / Geometric constraint satisfied."""
        checker = ConstraintChecker.create()
        placed = self._make_placed()
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            min_x=0.0,
            max_x=200.0,
            min_y=0.0,
            max_y=200.0,
        )
        result = checker.check(
            constraint=gc,
            placed=placed,
            item_weights={},
        )
        assert result.is_ok()
        assert result.unwrap().satisfied is True

    def test_check_geometric_violated(self) -> None:
        """几何约束违反 / Geometric constraint violated."""
        checker = ConstraintChecker.create()
        placed = self._make_placed()
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            min_x=0.0,
            max_x=25.0,
            min_y=0.0,
            max_y=200.0,
        )
        result = checker.check(
            constraint=gc,
            placed=placed,
            item_weights={},
        )
        assert result.is_ok()
        assert result.unwrap().satisfied is False

    def test_check_weight_ok(self) -> None:
        """重量约束满足 / Weight constraint satisfied."""
        checker = ConstraintChecker.create()
        placed = self._make_placed()
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            max_weight=100.0,
        )
        result = checker.check(
            constraint=wc,
            placed=placed,
            item_weights={"r1": 10.0, "r2": 20.0},
        )
        assert result.is_ok()
        assert result.unwrap().satisfied is True

    def test_check_weight_violated(self) -> None:
        """重量约束违反 / Weight constraint violated."""
        checker = ConstraintChecker.create()
        placed = self._make_placed()
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            max_weight=20.0,
        )
        result = checker.check(
            constraint=wc,
            placed=placed,
            item_weights={"r1": 10.0, "r2": 15.0},
        )
        assert result.is_ok()
        assert result.unwrap().satisfied is False

    def test_check_all(self) -> None:
        """批量检查 / Batch check."""
        checker = ConstraintChecker.create()
        placed = self._make_placed()
        constraints = (
            GeometricConstraint.create(
                constraint_key="geo_1",
                max_x=200.0,
                max_y=200.0,
            ),
            WeightConstraint.create(
                constraint_key="wt_1",
                max_weight=100.0,
            ),
        )
        result = checker.check_all(
            constraints=constraints,
            placed=placed,
            item_weights={"r1": 10.0, "r2": 20.0},
        )
        assert result.is_ok()
        results = result.unwrap()
        assert len(results) == 2
        assert all(r.satisfied for r in results)

    def test_validate_solution(self) -> None:
        """验证完整方案 / Validate complete solution."""
        checker = ConstraintChecker.create()
        placed = self._make_placed()
        constraints = (
            GeometricConstraint.create(
                constraint_key="geo_1",
                max_x=200.0,
                max_y=200.0,
            ),
        )
        result = checker.validate_solution(
            constraints=constraints,
            placed=placed,
            item_weights={"r1": 10.0, "r2": 20.0},
        )
        assert result.is_ok()
        assert result.unwrap() is True


# ============================================================
# Deep behavioral: overlap detection, boundary contact, weight
# ============================================================


class TestOverlapDetection:
    """重叠检测深度测试。/ Overlap detection deep tests."""

    def test_partial_overlap_detected(self) -> None:
        """部分重叠检测。/ Partial overlap detected."""
        p1 = PackingResult.create(
            item_key="a",
            x=0.0,
            y=0.0,
            placed_width=10.0,
            placed_height=10.0,
        )
        p2 = PackingResult.create(
            item_key="b",
            x=5.0,
            y=5.0,
            placed_width=10.0,
            placed_height=10.0,
        )
        assert p1.overlaps_with(p2) is True

    def test_no_overlap_edge_touching(self) -> None:
        """边缘相切无重叠。/ Edge touching no overlap."""
        p1 = PackingResult.create(
            item_key="a",
            x=0.0,
            y=0.0,
            placed_width=10.0,
            placed_height=10.0,
        )
        p2 = PackingResult.create(
            item_key="b",
            x=10.0,
            y=0.0,
            placed_width=10.0,
            placed_height=10.0,
        )
        assert p1.overlaps_with(p2) is False

    def test_complete_containment_overlap(self) -> None:
        """完全包含重叠。/ Complete containment overlap."""
        p1 = PackingResult.create(
            item_key="a",
            x=0.0,
            y=0.0,
            placed_width=20.0,
            placed_height=20.0,
        )
        p2 = PackingResult.create(
            item_key="b",
            x=5.0,
            y=5.0,
            placed_width=5.0,
            placed_height=5.0,
        )
        assert p1.overlaps_with(p2) is True


class TestBoundaryContactDetection:
    """边界接触检测测试。/ Boundary contact detection tests."""

    def test_item_touches_left_boundary(self) -> None:
        """物品接触左边界。/ Item touches left boundary."""
        p = PackingResult.create(
            item_key="r1",
            x=0.0,
            y=10.0,
            placed_width=10.0,
            placed_height=10.0,
        )
        assert p.x == 0.0

    def test_item_touches_bottom_boundary(self) -> None:
        """物品接触下边界。/ Item touches bottom boundary."""
        p = PackingResult.create(
            item_key="r1",
            x=10.0,
            y=0.0,
            placed_width=10.0,
            placed_height=10.0,
        )
        assert p.y == 0.0

    def test_item_touches_right_boundary(self) -> None:
        """物品接触右边界。/ Item touches right boundary."""
        container_width = 100.0
        p = PackingResult.create(
            item_key="r1",
            x=90.0,
            y=0.0,
            placed_width=10.0,
            placed_height=10.0,
        )
        assert p.right == pytest.approx(container_width)

    def test_item_touches_top_boundary(self) -> None:
        """物品接触上边界。/ Item touches top boundary."""
        container_height = 100.0
        p = PackingResult.create(
            item_key="r1",
            x=0.0,
            y=90.0,
            placed_width=10.0,
            placed_height=10.0,
        )
        assert p.top == pytest.approx(container_height)


class TestWeightConstraintDeep:
    """重量约束深度测试。/ Weight constraint deep tests."""

    def test_weight_constraint_at_exact_limit(self) -> None:
        """重量恰好等于限制。/ Weight at exact limit."""
        wc = WeightConstraint.create(constraint_key="wt_1", max_weight=50.0)
        assert wc.check_weight(50.0) is True

    def test_weight_constraint_zero_weight_always_ok(self) -> None:
        """零重量始终满足。/ Zero weight always OK."""
        wc = WeightConstraint.create(constraint_key="wt_1", max_weight=50.0)
        assert wc.check_weight(0.0) is True

    def test_weight_constraint_negative_treated_as_exceeded(self) -> None:
        """负剩余容量视为超限。/ Negative remaining treated as exceeded."""
        wc = WeightConstraint.create(constraint_key="wt_1", max_weight=10.0)
        assert wc.remaining_capacity(20.0) == 0.0
