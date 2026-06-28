"""CSP2D 切割方案生成器行为测试 / CSP2D cutting plan generator behavioral tests.

测试 CuttingPlanGenerator 的边缘场景和内部逻辑。
Test CuttingPlanGenerator edge cases and internal logic.
"""

from __future__ import annotations

from ospf_python.framework.csp2d.domain.material.model.sheet import Sheet
from ospf_python.framework.csp2d.domain.product.model.demand import Demand
from ospf_python.framework.csp2d.domain.product.model.shape import Shape
from ospf_python.framework.csp2d.domain.service.cutting_plan_generator import (
    CuttingPlanGenerator,
)


class TestCuttingPlanGeneratorEdgeCases:
    """切割方案生成器边缘场景测试 / Cutting plan generator edge case tests."""

    def test_shape_larger_than_material(self) -> None:
        """形状大于材料时无方案 / No plans when shape larger than material."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(name="S1", width=10.0, height=10.0, cost=5.0)
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="Big",
                width=50.0,
                height=50.0,
                rotatable=False,
            ),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=1),
        )
        plans = generator.generate_guillotine(material, shapes, demands)
        assert len(plans) == 0

    def test_empty_shapes_returns_empty(self) -> None:
        """空形状返回空方案 / Empty shapes returns empty plans."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(name="S1", width=100.0, height=100.0, cost=5.0)
        plans = generator.generate_guillotine(material, (), ())
        assert len(plans) == 0

    def test_demand_for_missing_shape(self) -> None:
        """需求引用不存在的形状 / Demand references nonexistent shape."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(name="S1", width=100.0, height=100.0, cost=5.0)
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="A",
                width=10.0,
                height=10.0,
            ),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh_missing", quantity=1),
        )
        plans = generator.generate_guillotine(material, shapes, demands)
        # Shape not found in shape_map -> no placements
        assert len(plans) == 0

    def test_single_shape_fits_exactly(self) -> None:
        """单个形状恰好填满材料 / Single shape fills material exactly."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(name="S1", width=10.0, height=10.0, cost=5.0)
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="Exact",
                width=10.0,
                height=10.0,
                rotatable=False,
            ),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=1),
        )
        plans = generator.generate_guillotine(material, shapes, demands)
        assert len(plans) == 1
        assert plans[0].item_count == 1

    def test_multiple_plans_for_high_demand(self) -> None:
        """高需求量生成多个方案 / High demand generates multiple plans."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(name="S1", width=10.0, height=10.0, cost=5.0)
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="Small",
                width=5.0,
                height=5.0,
                rotatable=False,
            ),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=10),
        )
        plans = generator.generate_guillotine(material, shapes, demands)
        total_items = sum(p.item_count for p in plans)
        assert total_items == 10
        assert len(plans) >= 1

    def test_rotatable_shape(self) -> None:
        """可旋转形状生成方案 / Rotatable shape generates plans."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(name="S1", width=100.0, height=50.0, cost=5.0)
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="Tall",
                width=20.0,
                height=80.0,
                rotatable=True,
            ),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=1),
        )
        plans = generator.generate_guillotine(material, shapes, demands)
        # Should rotate to fit: 80x20 -> 20x80, then 20x80 -> rotatable: 80x20 fits in 100x50
        # Actually: 20x80 rotated becomes 80x20, which fits in 100x50
        assert len(plans) >= 1

    def test_plan_key_includes_material_name(self) -> None:
        """方案键包含材料名 / Plan key includes material name."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(name="Plywood", width=100.0, height=100.0, cost=5.0)
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="Panel",
                width=20.0,
                height=20.0,
            ),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=1),
        )
        plans = generator.generate_guillotine(material, shapes, demands)
        assert len(plans) >= 1
        assert plans[0].plan_key.startswith("Plywood_plan_")

    def test_waste_ratio_within_bounds(self) -> None:
        """浪费率在合理范围内 / Waste ratio within bounds."""
        generator = CuttingPlanGenerator()
        material = Sheet.create(name="S1", width=100.0, height=100.0, cost=5.0)
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="Panel",
                width=30.0,
                height=20.0,
            ),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=5),
        )
        plans = generator.generate_guillotine(material, shapes, demands)
        for plan in plans:
            assert 0.0 <= plan.waste_ratio <= 1.0
