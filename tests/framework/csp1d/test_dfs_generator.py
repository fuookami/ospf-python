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
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_knife_pruning import (
    GenerationKnifePruning,
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


class TestKnifePruningKeepsPlansAtTheLimit:
    """恰好等于刀数上限的方案必须保留 / A plan at exactly the knife limit must be kept."""

    def test_zero_waste_plan_at_the_limit_is_enumerated(self) -> None:
        """料长 100、产品长 20、上限 5 刀时，零余料的 {"P1": 5} 必须被枚举。

        旧实现的 should_prune 用 >=，把恰好 5 刀的方案剪掉，DFS 只出 1..4。
        With material 100, product 20 and a limit of 5 knives, the zero-waste {"P1": 5} must be
        enumerated. The old should_prune used >= and dropped it, leaving DFS with 1..4 only.
        """
        products = [("P1", 20.0, 5)]
        constraints = GenerationConstraints(
            material_constraints=Constraints(max_knife_count=5),
            max_depth=10,
            max_solutions=100,
        )
        quantities = sorted(
            plan["P1"]
            for plan in DfsGenerator(constraints=constraints).generate(
                material_length=100.0, products=products
            )
        )
        assert quantities == [1, 2, 3, 4, 5]

    def test_pruning_agrees_with_can_add_cuts(self) -> None:
        """should_prune 与 can_add_cuts 对上限的判定必须一致。

        should_prune and can_add_cuts must agree about the limit.
        """
        pruning = GenerationKnifePruning(max_knife_count=5)
        assert pruning.should_prune(5) is False
        assert pruning.can_add_cuts(0, 5) is True
        assert pruning.should_prune(6) is True
        assert pruning.can_add_cuts(5, 1) is False
