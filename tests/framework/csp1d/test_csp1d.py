"""CSP1D framework integration tests.

Test creation of core domain objects with proper fields.
测试使用正确字段创建核心领域对象。
"""

from __future__ import annotations

from ospf_python.framework.csp1d.application.model.csp1d_problem import (
    Csp1dProblem,
)
from ospf_python.framework.csp1d.application.model.csp1d_solution import (
    Csp1dSolution,
)
from ospf_python.framework.csp1d.domain.material.model.cutting_plan import (
    CuttingPlan,
)
from ospf_python.framework.csp1d.domain.material.model.machine import (
    Machine,
)
from ospf_python.framework.csp1d.domain.material.model.material import (
    Material,
)
from ospf_python.framework.csp1d.domain.material.model.product import (
    Product,
)
from ospf_python.framework.csp1d.domain.material.model.product_demand import (
    ProductDemand,
)


def test_material_creation() -> None:
    """Create a material with fields. / 使用字段创建材料。"""
    m = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
    assert m.name == "Steel"


def test_product_creation() -> None:
    """Create a product with fields. / 使用字段创建产品。"""
    p = Product(name="Panel-A", width=30.0, length=200.0, demand=10)
    assert p.name == "Panel-A"


def test_machine_creation() -> None:
    """Create a machine with fields. / 使用字段创建机器。"""
    m = Machine(name="Cutter-1", max_width=200.0, cut_loss=2.0)
    assert m.name == "Cutter-1"


def test_cutting_plan_creation() -> None:
    """Create a cutting plan with fields. / 使用字段创建切割计划。"""
    p = Product(name="P1", width=30.0, length=200.0, demand=10)
    cp = CuttingPlan(material="Steel", products=((p, 3),), waste=10.0)
    assert cp.material == "Steel"


def test_problem_creation() -> None:
    """Create a problem with fields. / 使用字段创建问题。"""
    mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
    prod = Product(name="P1", width=30.0, length=200.0, demand=10)
    machine = Machine(name="C1", max_width=200.0, cut_loss=2.0)
    demand = ProductDemand(product="P1", quantity=10)
    p = Csp1dProblem(
        materials=(mat,),
        products=(prod,),
        machines=(machine,),
        demands=(demand,),
    )
    assert len(p.materials) == 1


def test_solution_creation() -> None:
    """Create a solution with fields. / 使用字段创建解决方案。"""
    s = Csp1dSolution(assignments=(), total_waste=0.0, utilization=1.0)
    assert s.utilization == 1.0
