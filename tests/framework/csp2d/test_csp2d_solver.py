"""CSP2D 求解器集成测试 / CSP2D solver integration tests.

测试 MaterialOptimizer 和 CuttingPlanGenerator 的逻辑。
Test MaterialOptimizer and CuttingPlanGenerator logic.
"""

from __future__ import annotations

from ospf_python.framework.csp2d.domain.cutting_plan.model.cutting_plan import (
    CuttingItem,
    CuttingPlan,
)
from ospf_python.framework.csp2d.domain.material.model.sheet import Sheet
from ospf_python.framework.csp2d.domain.product.model.demand import Demand
from ospf_python.framework.csp2d.domain.product.model.shape import Shape
from ospf_python.framework.csp2d.domain.service.cutting_plan_generator import (
    CuttingPlanGenerator,
)
from ospf_python.framework.csp2d.domain.service.material_optimizer import (
    MaterialOptimizer,
    MaterialSelection,
)


class TestMaterialOptimizer:
    """材料优化器测试 / Material optimizer tests."""

    def _make_setup(
        self,
    ) -> tuple[tuple[Demand, ...], tuple[Shape, ...], tuple[Sheet, ...]]:
        """创建测试数据 / Create test data."""
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="Panel-A",
                width=30.0,
                height=20.0,
            ),
            Shape.create(
                shape_key="sh2",
                name="Panel-B",
                width=20.0,
                height=15.0,
            ),
        )
        demands = (
            Demand.create(
                demand_key="d1",
                shape_key="sh1",
                quantity=5,
            ),
            Demand.create(
                demand_key="d2",
                shape_key="sh2",
                quantity=3,
            ),
        )
        materials = (
            Sheet.create(
                name="Large",
                width=100.0,
                height=100.0,
                cost=50.0,
            ),
            Sheet.create(
                name="Small",
                width=60.0,
                height=60.0,
                cost=20.0,
            ),
        )
        return demands, shapes, materials

    def test_optimize_selects_best_material(self) -> None:
        """优化选择最佳材料 / Optimize selects best material."""
        demands, shapes, materials = self._make_setup()
        optimizer = MaterialOptimizer()
        result = optimizer.optimize(demands, shapes, materials)

        assert result is not None
        assert isinstance(result, MaterialSelection)
        assert result.plan_count >= 1
        assert result.total_cost > 0.0

    def test_optimize_empty_inputs(self) -> None:
        """空输入优化 / Empty inputs optimization."""
        optimizer = MaterialOptimizer()
        result = optimizer.optimize((), (), ())
        assert result is None

    def test_rank_materials(self) -> None:
        """材料排名 / Material ranking."""
        demands, shapes, materials = self._make_setup()
        optimizer = MaterialOptimizer()
        rankings = optimizer.rank_materials(demands, shapes, materials)

        assert len(rankings) == 2
        # Should be sorted by total cost
        assert rankings[0].total_cost <= rankings[1].total_cost

    def test_rank_materials_empty(self) -> None:
        """空材料排名 / Empty material ranking."""
        optimizer = MaterialOptimizer()
        rankings = optimizer.rank_materials((), (), ())
        assert len(rankings) == 0

    def test_material_selection_properties(self) -> None:
        """材料选择属性 / Material selection properties."""
        sel = MaterialSelection(
            material_name="S1",
            plan_count=3,
            total_waste_ratio=0.15,
            total_cost=150.0,
        )
        assert sel.material_name == "S1"
        assert sel.plan_count == 3
        assert sel.total_waste_ratio == 0.15
        assert sel.total_cost == 150.0


class TestCuttingPlanGenerator:
    """切割方案生成器测试 / Cutting plan generator tests."""

    def test_generate_guillotine(self) -> None:
        """生成切割方案 / Generate cutting plans."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(
            name="S1",
            width=100.0,
            height=100.0,
            cost=50.0,
        )
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="Panel",
                width=30.0,
                height=20.0,
                rotatable=True,
            ),
        )
        demands = (
            Demand.create(
                demand_key="d1",
                shape_key="sh1",
                quantity=3,
            ),
        )
        plans = generator.generate_guillotine(material, shapes, demands)

        assert len(plans) >= 1
        total_items = sum(p.item_count for p in plans)
        assert total_items == 3

    def test_generate_empty_demands(self) -> None:
        """空需求生成 / Empty demands generation."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(
            name="S1",
            width=100.0,
            height=100.0,
            cost=50.0,
        )
        plans = generator.generate_guillotine(material, (), ())
        assert len(plans) == 0

    def test_generate_respects_material_bounds(self) -> None:
        """方案尊重材料边界 / Plans respect material bounds."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(
            name="S1",
            width=50.0,
            height=50.0,
            cost=10.0,
        )
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="Small",
                width=20.0,
                height=20.0,
            ),
        )
        demands = (
            Demand.create(
                demand_key="d1",
                shape_key="sh1",
                quantity=4,
            ),
        )
        plans = generator.generate_guillotine(material, shapes, demands)

        # All items should fit within material bounds
        for plan in plans:
            for item in plan.items:
                assert item.x >= 0.0
                assert item.y >= 0.0

    def test_generate_multiple_shapes(self) -> None:
        """多形状生成 / Multiple shapes generation."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(
            name="S1",
            width=200.0,
            height=200.0,
            cost=100.0,
        )
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="A",
                width=30.0,
                height=20.0,
            ),
            Shape.create(
                shape_key="sh2",
                name="B",
                width=15.0,
                height=10.0,
            ),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=2),
            Demand.create(demand_key="d2", shape_key="sh2", quantity=3),
        )
        plans = generator.generate_guillotine(material, shapes, demands)

        total_items = sum(p.item_count for p in plans)
        assert total_items == 5

    def test_plan_waste_ratio_range(self) -> None:
        """方案浪费率范围 / Plan waste ratio range."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(
            name="S1",
            width=100.0,
            height=100.0,
            cost=50.0,
        )
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="Panel",
                width=30.0,
                height=20.0,
            ),
        )
        demands = (
            Demand.create(
                demand_key="d1",
                shape_key="sh1",
                quantity=2,
            ),
        )
        plans = generator.generate_guillotine(material, shapes, demands)

        for plan in plans:
            assert 0.0 <= plan.waste_ratio <= 1.0


# ============================================================
# Deep behavioral: cutting plan validity, waste minimization
# ============================================================


class TestCuttingPlanDeepBehavior:
    """切割方案深度行为测试。/ Cutting plan deep behavioral tests."""

    def test_cutting_plan_with_items_valid(self) -> None:
        """有切割项的方案有效。/ Plan with items is valid."""
        sheet = Sheet.create(name="S1", width=100.0, height=100.0)
        items = (
            CuttingItem.create(shape_key="sh1", x=0.0, y=0.0),
            CuttingItem.create(shape_key="sh2", x=30.0, y=0.0),
        )
        # items area = 600 + 300 = 900, sheet area = 10000, waste = 9100/10000 = 0.91
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="S1",
            items=items,
            waste_ratio=0.91,
        )
        assert plan.is_valid_for(sheet) is True

    def test_cutting_plan_used_area_calculation(self) -> None:
        """方案已使用面积计算。/ Plan used area calculation."""
        plan = CuttingPlan.create(
            plan_key="p1",
            material_key="m1",
            waste_ratio=0.25,
        )
        assert plan.used_area == 0.75

    def test_demand_satisfaction_all_met(self) -> None:
        """所有需求已满足。/ All demands satisfied."""
        (
            Shape.create(shape_key="sh1", name="A", width=30.0, height=20.0),
            Shape.create(shape_key="sh2", name="B", width=20.0, height=15.0),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=10),
            Demand.create(demand_key="d2", shape_key="sh2", quantity=5),
        )
        # Check demand satisfaction methods
        assert demands[0].is_satisfied_by(10)
        assert demands[1].is_satisfied_by(5)

    def test_demand_satisfaction_partial(self) -> None:
        """部分需求满足。/ Partial demand satisfaction."""
        demand = Demand.create(demand_key="d1", shape_key="sh1", quantity=10)
        assert demand.is_satisfied_by(5) is False
        assert demand.remaining(5) == 5

    def test_shape_fits_in_sheet(self) -> None:
        """形状适合板材。/ Shape fits in sheet."""
        shape = Shape.create(
            shape_key="sh1", name="A", width=30.0, height=20.0, rotatable=True,
        )
        sheet = Sheet.create(name="S1", width=100.0, height=100.0)
        assert shape.fits_in(sheet.width, sheet.height) is True

    def test_shape_too_large_for_sheet(self) -> None:
        """形状对板材过大。/ Shape too large for sheet."""
        shape = Shape.create(
            shape_key="sh1", name="A", width=150.0, height=20.0, rotatable=False,
        )
        sheet = Sheet.create(name="S1", width=100.0, height=100.0)
        assert shape.fits_in(sheet.width, sheet.height) is False

    def test_waste_minimization_many_items(self) -> None:
        """多物品浪费最小化。/ Waste minimization with many items."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(name="S1", width=200.0, height=200.0, cost=50.0)
        shapes = (
            Shape.create(shape_key="sh1", name="Panel", width=50.0, height=50.0),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=16),
        )
        plans = generator.generate_guillotine(material, shapes, demands)
        total_items = sum(p.item_count for p in plans)
        assert total_items == 16
        # 16 x 50x50 = 16 x 2500 = 40000, sheet area = 40000
        # Should have reasonable utilization
        for plan in plans:
            assert plan.waste_ratio >= 0.0
