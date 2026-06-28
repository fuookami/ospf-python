"""CSP2D 材料优化器行为测试 / CSP2D material optimizer behavioral tests.

测试 MaterialOptimizer 的边缘场景和内部逻辑。
Test MaterialOptimizer edge cases and internal logic.
"""

from __future__ import annotations

from ospf_python.framework.csp2d.domain.material.model.sheet import Sheet
from ospf_python.framework.csp2d.domain.product.model.demand import Demand
from ospf_python.framework.csp2d.domain.product.model.shape import Shape
from ospf_python.framework.csp2d.domain.service.material_optimizer import (
    MaterialOptimizer,
    MaterialSelection,
)


class TestMaterialOptimizerEdgeCases:
    """材料优化器边缘场景测试 / Material optimizer edge case tests."""

    def test_optimize_with_empty_demands(self) -> None:
        """空需求返回 None / Empty demands returns None."""
        optimizer = MaterialOptimizer()
        shapes = (
            Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0),
        )
        materials = (
            Sheet.create(name="S1", width=100.0, height=100.0, cost=10.0),
        )
        result = optimizer.optimize((), shapes, materials)
        assert result is None

    def test_optimize_with_empty_shapes(self) -> None:
        """空形状返回 None / Empty shapes returns None."""
        optimizer = MaterialOptimizer()
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=5),
        )
        materials = (
            Sheet.create(name="S1", width=100.0, height=100.0, cost=10.0),
        )
        result = optimizer.optimize(demands, (), materials)
        assert result is None

    def test_optimize_with_empty_materials(self) -> None:
        """空材料返回 None / Empty materials returns None."""
        optimizer = MaterialOptimizer()
        shapes = (
            Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=5),
        )
        result = optimizer.optimize(demands, shapes, ())
        assert result is None

    def test_optimize_shape_larger_than_all_materials(self) -> None:
        """所有材料都无法容纳形状 / No material can fit shape."""
        optimizer = MaterialOptimizer()
        shapes = (
            Shape.create(
                shape_key="sh1",
                name="Big",
                width=200.0,
                height=200.0,
                rotatable=False,
            ),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=1),
        )
        materials = (
            Sheet.create(name="S1", width=100.0, height=100.0, cost=10.0),
        )
        result = optimizer.optimize(demands, shapes, materials)
        # No shape fits in material -> _can_fit_any returns False -> _evaluate_material returns None
        assert result is None

    def test_optimize_with_zero_area_material(self) -> None:
        """零面积材料被跳过 / Zero area material is skipped."""
        optimizer = MaterialOptimizer()
        shapes = (
            Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=5),
        )
        materials = (
            Sheet.create(name="Zero", width=0.0, height=0.0, cost=0.0),
            Sheet.create(name="S1", width=100.0, height=100.0, cost=10.0),
        )
        result = optimizer.optimize(demands, shapes, materials)
        assert result is not None
        assert result.material_name == "S1"

    def test_optimize_demand_for_missing_shape(self) -> None:
        """需求引用不存在的形状 / Demand references missing shape."""
        optimizer = MaterialOptimizer()
        shapes = (
            Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh_missing", quantity=5),
        )
        materials = (
            Sheet.create(name="S1", width=100.0, height=100.0, cost=10.0),
        )
        # total_area will be 0 because shape_key "sh_missing" not in shape_map
        result = optimizer.optimize(demands, shapes, materials)
        assert result is None

    def test_optimize_selects_lower_effective_cost(self) -> None:
        """优化选择单位有效成本更低的材料 / Optimize selects lower effective unit cost."""
        optimizer = MaterialOptimizer()
        shapes = (
            Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=100),
        )
        materials = (
            Sheet.create(name="Expensive", width=100.0, height=100.0, cost=200.0),
            Sheet.create(name="Cheap", width=100.0, height=100.0, cost=50.0),
        )
        result = optimizer.optimize(demands, shapes, materials)
        assert result is not None
        assert result.material_name == "Cheap"

    def test_rank_materials_with_empty_demands(self) -> None:
        """空需求排名 / Rank with empty demands."""
        optimizer = MaterialOptimizer()
        shapes = (
            Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0),
        )
        materials = (
            Sheet.create(name="S1", width=100.0, height=100.0, cost=10.0),
        )
        rankings = optimizer.rank_materials((), shapes, materials)
        assert len(rankings) == 0

    def test_rank_materials_with_zero_area_material(self) -> None:
        """零面积材料排名时跳过 / Zero area material skipped in ranking."""
        optimizer = MaterialOptimizer()
        shapes = (
            Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=5),
        )
        materials = (
            Sheet.create(name="Zero", width=0.0, height=0.0, cost=0.0),
            Sheet.create(name="S1", width=100.0, height=100.0, cost=10.0),
        )
        rankings = optimizer.rank_materials(demands, shapes, materials)
        assert len(rankings) == 1
        assert rankings[0].material_name == "S1"

    def test_rank_materials_sorted_by_total_cost(self) -> None:
        """按总成本排序 / Sorted by total cost."""
        optimizer = MaterialOptimizer()
        shapes = (
            Shape.create(shape_key="sh1", name="A", width=10.0, height=10.0),
        )
        demands = (
            Demand.create(demand_key="d1", shape_key="sh1", quantity=5),
        )
        materials = (
            Sheet.create(name="Expensive", width=50.0, height=50.0, cost=100.0),
            Sheet.create(name="Cheap", width=100.0, height=100.0, cost=10.0),
        )
        rankings = optimizer.rank_materials(demands, shapes, materials)
        assert len(rankings) == 2
        assert rankings[0].total_cost <= rankings[1].total_cost

    def test_material_selection_dataclass(self) -> None:
        """MaterialSelection 数据类 / MaterialSelection dataclass."""
        sel = MaterialSelection(
            material_name="Test",
            plan_count=2,
            total_waste_ratio=0.3,
            total_cost=100.0,
        )
        assert sel.material_name == "Test"
        assert sel.plan_count == 2
        assert sel.total_waste_ratio == 0.3
        assert sel.total_cost == 100.0
