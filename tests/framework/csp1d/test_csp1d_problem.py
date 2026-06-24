"""Csp1dProblem and builder tests.

Test problem creation and builder workflow.
测试问题创建和构建器工作流。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.application.model.csp1d_problem import (
    Csp1dProblem,
)
from ospf_python.framework.csp1d.application.model.csp1d_problem_builder import (
    Csp1dProblemBuilder,
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


class TestCsp1dProblem:
    """Csp1dProblem frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
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
        assert len(p.products) == 1
        assert len(p.machines) == 1
        assert len(p.demands) == 1

    def test_empty_tuples(self) -> None:
        """Create with empty tuples. / 使用空元组创建。"""
        p = Csp1dProblem(materials=(), products=(), machines=(), demands=())
        assert len(p.materials) == 0
        assert len(p.products) == 0

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        p = Csp1dProblem(materials=(), products=(), machines=(), demands=())
        with pytest.raises(AttributeError):
            p.materials = ()  # type: ignore[misc]

    def test_equality(self) -> None:
        """Same field values yield equality. / 相同字段值相等。"""
        a = Csp1dProblem(materials=(), products=(), machines=(), demands=())
        b = Csp1dProblem(materials=(), products=(), machines=(), demands=())
        assert a == b

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        p = Csp1dProblem(materials=(), products=(), machines=(), demands=())
        assert hash(p) is not None


class TestCsp1dProblemBuilder:
    """Csp1dProblemBuilder tests."""

    def test_build_empty(self) -> None:
        """Build with no data yields empty problem. / 空构建。"""
        builder = Csp1dProblemBuilder()
        problem = builder.build()
        assert len(problem.materials) == 0
        assert len(problem.products) == 0
        assert len(problem.machines) == 0
        assert len(problem.demands) == 0

    def test_add_material(self) -> None:
        """Add a material. / 添加材料。"""
        builder = Csp1dProblemBuilder()
        builder.add_material(name="Steel", width=100.0, length=600.0, cost=50.0)
        problem = builder.build()
        assert len(problem.materials) == 1
        assert problem.materials[0].name == "Steel"

    def test_add_product(self) -> None:
        """Add a product. / 添加产品。"""
        builder = Csp1dProblemBuilder()
        builder.add_product(name="P1", width=30.0, length=200.0, demand=10)
        problem = builder.build()
        assert len(problem.products) == 1
        assert problem.products[0].name == "P1"

    def test_add_machine(self) -> None:
        """Add a machine. / 添加机器。"""
        builder = Csp1dProblemBuilder()
        builder.add_machine(name="C1", max_width=200.0, cut_loss=2.0)
        problem = builder.build()
        assert len(problem.machines) == 1
        assert problem.machines[0].name == "C1"

    def test_add_demand(self) -> None:
        """Add a demand. / 添加需求。"""
        builder = Csp1dProblemBuilder()
        builder.add_demand(product="P1", quantity=10)
        problem = builder.build()
        assert len(problem.demands) == 1
        assert problem.demands[0].product == "P1"

    def test_chaining(self) -> None:
        """Methods return builder for chaining. / 链式调用。"""
        builder = Csp1dProblemBuilder()
        result = (
            builder.add_material(name="M1", width=100.0, length=600.0, cost=50.0)
            .add_product(name="P1", width=30.0, length=200.0, demand=10)
            .add_machine(name="C1", max_width=200.0, cut_loss=2.0)
            .add_demand(product="P1", quantity=10)
        )
        problem = result.build()
        assert len(problem.materials) == 1
        assert len(problem.products) == 1
        assert len(problem.machines) == 1
        assert len(problem.demands) == 1

    def test_full_build(self) -> None:
        """Build a complete problem. / 构建完整问题。"""
        builder = Csp1dProblemBuilder()
        builder.add_material(name="Steel", width=100.0, length=600.0, cost=50.0)
        builder.add_material(name="Aluminum", width=80.0, length=500.0, cost=70.0)
        builder.add_product(name="P1", width=30.0, length=200.0, demand=20)
        builder.add_product(name="P2", width=25.0, length=150.0, demand=15)
        builder.add_machine(name="C1", max_width=200.0, cut_loss=2.0)
        builder.add_demand(product="P1", quantity=20)
        builder.add_demand(product="P2", quantity=15)
        problem = builder.build()
        assert len(problem.materials) == 2
        assert len(problem.products) == 2
        assert len(problem.machines) == 1
        assert len(problem.demands) == 2
