"""CSP2D 示例 / CSP2D example.

基本二维切割库存：生成切割方案。
Basic 2D cutting stock: generate cutting plans.
"""

from ospf_python.framework.csp2d.domain.material.model.sheet import Sheet
from ospf_python.framework.csp2d.domain.product.model.demand import Demand
from ospf_python.framework.csp2d.domain.product.model.shape import Shape
from ospf_python.framework.csp2d.domain.service.cutting_plan_generator import (
    CuttingPlanGenerator,
)

material = Sheet.create(name="S1", width=100.0, height=100.0, cost=50.0)
shapes = (
    Shape.create(shape_key="sh1", name="Panel", width=30.0, height=20.0),
)
demands = (
    Demand.create(demand_key="d1", shape_key="sh1", quantity=3),
)

generator = CuttingPlanGenerator()
plans = generator.generate_guillotine(material, shapes, demands)

total_items = sum(p.item_count for p in plans)
print(f"切割方案数: {len(plans)}")    # 切割方案数
print(f"总切割项: {total_items}")      # 总切割项: 3
