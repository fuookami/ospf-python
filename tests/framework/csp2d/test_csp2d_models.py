"""CSP2D 领域模型测试 / CSP2D domain model tests.

测试板材、卷材、形状、需求和切割方案的创建与属性。
Test creation and properties of Sheet, Strip, Shape,
Demand, and CuttingPlan in CSP2D.
"""

from __future__ import annotations

from ospf_python.framework.csp2d.domain.cutting_plan.model.cutting_plan import (
    CuttingItem,
    CuttingPlan,
)
from ospf_python.framework.csp2d.domain.material.model.sheet import Sheet
from ospf_python.framework.csp2d.domain.material.model.strip import Strip
from ospf_python.framework.csp2d.domain.product.model.demand import Demand
from ospf_python.framework.csp2d.domain.product.model.shape import Shape


class TestSheet:
    """板材模型测试 / Sheet model tests."""

    def test_create_sheet(self) -> None:
        """创建板材 / Create sheet."""
        s = Sheet.create(
            name="Plywood",
            width=1200.0,
            height=2400.0,
            cost=50.0,
            grain_direction=True,
        )
        assert s.name == "Plywood"
        assert s.width == 1200.0
        assert s.height == 2400.0
        assert s.cost == 50.0
        assert s.grain_direction is True

    def test_sheet_defaults(self) -> None:
        """板材默认值 / Sheet defaults."""
        s = Sheet(name="S1", width=100.0, height=200.0, cost=10.0)
        assert s.grain_direction is None

    def test_sheet_area(self) -> None:
        """板材面积 / Sheet area."""
        s = Sheet.create(name="S1", width=100.0, height=200.0)
        assert s.area == 20000.0

    def test_sheet_aspect_ratio(self) -> None:
        """板材宽高比 / Sheet aspect ratio."""
        s = Sheet.create(name="S1", width=200.0, height=100.0)
        assert s.aspect_ratio == 2.0

    def test_sheet_aspect_ratio_zero(self) -> None:
        """高度为零的宽高比 / Aspect ratio with zero height."""
        s = Sheet.create(name="S1", width=200.0, height=0.0)
        assert s.aspect_ratio == float("inf")

    def test_can_fit_normal(self) -> None:
        """正常方向放入 / Fits normal orientation."""
        s = Sheet.create(
            name="S1",
            width=100.0,
            height=200.0,
            grain_direction=True,
        )
        assert s.can_fit(50.0, 100.0) is True
        assert s.can_fit(150.0, 100.0) is False

    def test_can_fit_with_rotation(self) -> None:
        """旋转后放入 / Fits with rotation."""
        s = Sheet.create(
            name="S1",
            width=100.0,
            height=200.0,
            grain_direction=False,
        )
        # 150x50 does not fit normal, but fits rotated (50 <= 200, 150 <= 100)
        # Actually 150 > 100, so no. Let's use 150x80:
        # Normal: 150 > 100, no. Rotated: 150 > 200? No, 150 <= 200 and 80 <= 100. Yes!
        assert s.can_fit(150.0, 80.0) is True

    def test_can_fit_invalid_dimensions(self) -> None:
        """无效尺寸 / Invalid dimensions."""
        s = Sheet.create(name="S1", width=100.0, height=200.0)
        assert s.can_fit(0.0, 100.0) is False
        assert s.can_fit(100.0, -1.0) is False

    def test_rotate_sheet(self) -> None:
        """旋转板材 / Rotate sheet."""
        s = Sheet.create(
            name="S1",
            width=100.0,
            height=200.0,
            cost=50.0,
            grain_direction=True,
        )
        rotated = s.rotate()
        assert rotated.width == 200.0
        assert rotated.height == 100.0
        assert rotated.cost == 50.0
        assert rotated.grain_direction is False


class TestStrip:
    """卷材模型测试 / Strip model tests."""

    def test_create_strip(self) -> None:
        """创建卷材 / Create strip."""
        s = Strip.create(
            name="Roll-1",
            width=100.0,
            length=5000.0,
            cost=20.0,
        )
        assert s.name == "Roll-1"
        assert s.width == 100.0
        assert s.length == 5000.0
        assert s.cost == 20.0

    def test_strip_area(self) -> None:
        """卷材面积 / Strip area."""
        s = Strip.create(name="R1", width=100.0, length=500.0)
        assert s.area == 50000.0

    def test_strip_can_fit(self) -> None:
        """卷材放入检查 / Strip can fit."""
        s = Strip.create(name="R1", width=100.0, length=500.0)
        assert s.can_fit(50.0, 200.0) is True
        assert s.can_fit(150.0, 200.0) is False
        assert s.can_fit(50.0, 600.0) is False

    def test_strip_can_fit_invalid(self) -> None:
        """卷材无效尺寸 / Strip invalid dimensions."""
        s = Strip.create(name="R1", width=100.0, length=500.0)
        assert s.can_fit(0.0, 200.0) is False
        assert s.can_fit(50.0, -1.0) is False


class TestShape:
    """形状模型测试 / Shape model tests."""

    def test_create_shape(self) -> None:
        """创建形状 / Create shape."""
        s = Shape.create(
            shape_key="sh1",
            name="Panel",
            width=30.0,
            height=20.0,
            rotatable=True,
        )
        assert s.shape_key == "sh1"
        assert s.name == "Panel"
        assert s.width == 30.0
        assert s.height == 20.0
        assert s.rotatable is True

    def test_shape_area(self) -> None:
        """形状面积 / Shape area."""
        s = Shape.create(
            shape_key="sh1",
            name="P",
            width=30.0,
            height=20.0,
        )
        assert s.area == 600.0

    def test_shape_perimeter(self) -> None:
        """形状周长 / Shape perimeter."""
        s = Shape.create(
            shape_key="sh1",
            name="P",
            width=30.0,
            height=20.0,
        )
        assert s.perimeter == 100.0

    def test_shape_min_max_dimension(self) -> None:
        """形状最小最大边长 / Shape min/max dimension."""
        s = Shape.create(
            shape_key="sh1",
            name="P",
            width=30.0,
            height=20.0,
        )
        assert s.min_dimension == 20.0
        assert s.max_dimension == 30.0

    def test_rotations_rotatable(self) -> None:
        """可旋转形状的旋转 / Rotatable shape rotations."""
        s = Shape.create(
            shape_key="sh1",
            name="P",
            width=30.0,
            height=20.0,
            rotatable=True,
        )
        rots = s.rotations()
        assert len(rots) == 2
        assert rots[0].width == 30.0
        assert rots[1].width == 20.0

    def test_rotations_not_rotatable(self) -> None:
        """不可旋转形状的旋转 / Non-rotatable shape rotations."""
        s = Shape.create(
            shape_key="sh1",
            name="P",
            width=30.0,
            height=20.0,
            rotatable=False,
        )
        rots = s.rotations()
        assert len(rots) == 1

    def test_rotations_square(self) -> None:
        """正方形形状的旋转 / Square shape rotations."""
        s = Shape.create(
            shape_key="sh1",
            name="P",
            width=20.0,
            height=20.0,
            rotatable=True,
        )
        rots = s.rotations()
        assert len(rots) == 1

    def test_fits_in(self) -> None:
        """放入容器检查 / Fits in container."""
        s = Shape.create(
            shape_key="sh1",
            name="P",
            width=30.0,
            height=20.0,
            rotatable=True,
        )
        assert s.fits_in(100.0, 100.0) is True
        assert s.fits_in(25.0, 100.0) is True  # rotated: 20x30
        assert s.fits_in(15.0, 100.0) is False


class TestDemand:
    """需求模型测试 / Demand model tests."""

    def test_create_demand(self) -> None:
        """创建需求 / Create demand."""
        d = Demand.create(
            demand_key="d1",
            shape_key="sh1",
            quantity=10,
            priority=1,
        )
        assert d.demand_key == "d1"
        assert d.shape_key == "sh1"
        assert d.quantity == 10
        assert d.priority == 1

    def test_demand_is_satisfied(self) -> None:
        """需求满足检查 / Demand satisfied check."""
        d = Demand.create(
            demand_key="d1",
            shape_key="sh1",
            quantity=10,
        )
        assert d.is_satisfied_by(10) is True
        assert d.is_satisfied_by(15) is True
        assert d.is_satisfied_by(5) is False

    def test_demand_remaining(self) -> None:
        """剩余需求 / Demand remaining."""
        d = Demand.create(
            demand_key="d1",
            shape_key="sh1",
            quantity=10,
        )
        assert d.remaining(3) == 7
        assert d.remaining(10) == 0
        assert d.remaining(15) == 0

    def test_demand_with_quantity(self) -> None:
        """修改数量的需求 / Demand with new quantity."""
        d = Demand.create(
            demand_key="d1",
            shape_key="sh1",
            quantity=10,
            priority=2,
        )
        d2 = d.with_quantity(20)
        assert d2.quantity == 20
        assert d2.priority == 2
        assert d2.demand_key == "d1"
        assert d.quantity == 10  # original unchanged


class TestCuttingPlan:
    """切割方案模型测试 / Cutting plan model tests."""

    def test_create_cutting_plan(self) -> None:
        """创建切割方案 / Create cutting plan."""
        items = (
            CuttingItem.create(shape_key="sh1", x=0.0, y=0.0),
            CuttingItem.create(
                shape_key="sh2", x=30.0, y=0.0, rotated=True,
            ),
        )
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="sheet_1",
            items=items,
            waste_ratio=0.15,
        )
        assert plan.plan_key == "p1"
        assert plan.material_key == "sheet_1"
        assert plan.item_count == 2
        assert plan.waste_ratio == 0.15

    def test_cutting_plan_used_area(self) -> None:
        """已使用面积比 / Used area ratio."""
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="m1",
            waste_ratio=0.2,
        )
        assert plan.used_area == 0.8

    def test_cutting_plan_is_valid(self) -> None:
        """方案有效性 / Plan validity."""
        sheet = Sheet.create(name="S1", width=100.0, height=100.0)
        # 无 items 的方案 waste_ratio 必须 1.0（全浪费）
        # Plan with no items must have waste_ratio 1.0 (full waste)
        empty_plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
            waste_ratio=1.0,
        )
        assert empty_plan.is_valid_for(sheet) is True

    def test_cutting_plan_invalid_waste(self) -> None:
        """无效浪费率 / Invalid waste ratio."""
        sheet = Sheet.create(name="S1", width=100.0, height=100.0)
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
            waste_ratio=1.5,
        )
        assert plan.is_valid_for(sheet) is False

    def test_add_item_immutably(self) -> None:
        """不可变添加切割项 / Immutable add cutting item."""
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="m1",
        )
        item = CuttingItem.create(shape_key="sh1", x=0.0, y=0.0)
        plan2 = plan.add_item(item)
        assert plan.item_count == 0
        assert plan2.item_count == 1

    def test_waste_area(self) -> None:
        """浪费面积 / Waste area."""
        sheet = Sheet.create(name="S1", width=100.0, height=100.0, cost=0.0)
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
            waste_ratio=0.2,
        )
        assert plan.waste_area(sheet) == 2000.0
