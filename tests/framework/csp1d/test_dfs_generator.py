"""DfsGenerator tests.

Test DFS cutting plan generator.
测试 DFS 切割方案生成器。
"""

from __future__ import annotations

from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.constraints import (
    Constraints,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.generation_constraints import (
    GenerationConstraints,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.dfs_generator import (
    DfsGenerator,
)


class TestDfsGenerator:
    """DfsGenerator frozen dataclass tests."""

    def test_creation_defaults(self) -> None:
        """Create with default constraints. / 默认约束创建。"""
        g = DfsGenerator()
        assert g.constraints is not None
        assert g.collector is not None

    def test_generate_single_product(self) -> None:
        """Generate plans for single product. / 单产品生成。"""
        constraints = Constraints(max_knife_count=5)
        gc = GenerationConstraints(
            material_constraints=constraints,
            max_depth=10,
        )
        g = DfsGenerator(constraints=gc)
        products = [("P1", 30.0, 3)]
        plans = g.generate(material_length=100.0, products=products)
        # Should generate plans with 0, 1, 2, 3 of P1
        assert len(plans) > 0
        # All plans should be non-empty dicts
        for plan in plans:
            assert len(plan) > 0

    def test_generate_two_products(self) -> None:
        """Generate plans for two products. / 双产品生成。"""
        constraints = Constraints(max_knife_count=5)
        gc = GenerationConstraints(
            material_constraints=constraints,
            max_depth=10,
            max_solutions=100,
        )
        g = DfsGenerator(constraints=gc)
        products = [("P1", 30.0, 2), ("P2", 20.0, 3)]
        plans = g.generate(material_length=100.0, products=products)
        assert len(plans) > 0

    def test_generate_respects_max_solutions(self) -> None:
        """Max solutions limit is respected. / 最大解数量限制。"""
        gc = GenerationConstraints(
            max_depth=100,
            max_solutions=3,
        )
        g = DfsGenerator(constraints=gc)
        products = [("P1", 10.0, 10)]
        plans = g.generate(material_length=100.0, products=products)
        assert len(plans) <= 3

    def test_generate_empty_products(self) -> None:
        """Generate with empty products. / 空产品生成。"""
        g = DfsGenerator()
        plans = g.generate(material_length=100.0, products=[])
        # No products means no non-empty plans
        assert len(plans) == 0
