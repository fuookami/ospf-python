"""csp1d 框架额外测试 / Additional csp1d framework tests.

覆盖 Csp1dShadowPriceLifecycle, Csp1dSolutionEnrichment,
CuttingPlanGenerationContext, FullSumGenerator, GenerationContribution,
GenerationParallelism, NSameGenerator, NSumGenerator,
BatchMinimizationObjective, DemandConstraintPipeline,
MachineConstraintPipeline, MaterialConstraintPipeline,
RenderDto 等类。
Covers Csp1dShadowPriceLifecycle, Csp1dSolutionEnrichment,
CuttingPlanGenerationContext, FullSumGenerator,
GenerationContribution, GenerationParallelism,
NSameGenerator, NSumGenerator,
BatchMinimizationObjective, DemandConstraintPipeline,
MachineConstraintPipeline, MaterialConstraintPipeline,
RenderDto, etc.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.application.model.csp1d_assignment import (
    Csp1dAssignment,
)
from ospf_python.framework.csp1d.application.model.csp1d_solution import (
    Csp1dSolution,
)
from ospf_python.framework.csp1d.application.service.csp1d_shadow_price_lifecycle import (
    Csp1dShadowPriceLifecycle,
)
from ospf_python.framework.csp1d.application.service.csp1d_solution_enrichment import (
    Csp1dSolutionEnrichment,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.cutting_plan_generation_context import (
    CuttingPlanGenerationContext,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.constraints import (
    Constraints,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.cutting_plan_canonical_key import (
    CuttingPlanCanonicalKey,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.cutting_plan_constraint import (
    CuttingPlanConstraint,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.full_sum_generator import (
    FullSumGenerator,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_collector import (
    GenerationCollector,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_contribution import (
    GenerationContribution,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_length_pruning import (
    GenerationLengthPruning,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_parallelism import (
    GenerationParallelism,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.n_same_generator import (
    NSameGenerator,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.n_sum_generator import (
    NSumGenerator,
)
from ospf_python.framework.csp1d.domain.produce.service.pipeline.batch_minimization_objective import (
    BatchMinimizationObjective,
)
from ospf_python.framework.csp1d.domain.produce.service.pipeline.demand_constraint_pipeline import (
    DemandConstraintPipeline,
)
from ospf_python.framework.csp1d.domain.produce.service.pipeline.machine_constraint_pipeline import (
    MachineConstraintPipeline,
)
from ospf_python.framework.csp1d.domain.produce.service.pipeline.material_constraint_pipeline import (
    MaterialConstraintPipeline,
)
from ospf_python.framework.csp1d.infrastructure.cutting_plan_product_order import (
    CuttingPlanProductOrder,
)
from ospf_python.framework.csp1d.infrastructure.dto.render_dto import (
    RenderDto,
)

# ============================================================
# Csp1dShadowPriceLifecycle tests
# ============================================================


class TestCsp1dShadowPriceLifecycle:
    """Csp1dShadowPriceLifecycle 测试 / Tests."""

    def test_initialize(self) -> None:
        """初始化影子价格 / Initialize shadow prices."""
        lc = Csp1dShadowPriceLifecycle()
        lc.initialize(("p1", "p2", "p3"))
        assert lc.prices.products == ("p1", "p2", "p3")
        assert lc.prices.get("p1") == 0.0

    def test_update_changes_prices(self) -> None:
        """更新改变价格 / Update changes prices."""
        lc = Csp1dShadowPriceLifecycle()
        lc.initialize(("p1", "p2"))
        lc.update({"p1": 1.5, "p2": 2.5})
        assert lc.prices.get("p1") == 1.5
        assert lc.prices.get("p2") == 2.5

    def test_iteration_count(self) -> None:
        """迭代计数 / Iteration count."""
        lc = Csp1dShadowPriceLifecycle()
        lc.initialize(("p1",))
        assert lc.iteration == 0
        lc.update({"p1": 1.0})
        assert lc.iteration == 1
        lc.update({"p1": 1.1})
        assert lc.iteration == 2

    def test_convergence(self) -> None:
        """收敛判定 / Convergence check."""
        lc = Csp1dShadowPriceLifecycle(tolerance=0.1)
        lc.initialize(("p1",))
        lc.update({"p1": 1.0})
        assert lc.converged is False
        lc.update({"p1": 1.001})
        assert lc.converged is True

    def test_not_converged(self) -> None:
        """未收敛 / Not converged."""
        lc = Csp1dShadowPriceLifecycle(tolerance=1e-10)
        lc.initialize(("p1",))
        lc.update({"p1": 1.0})
        lc.update({"p1": 2.0})
        assert lc.converged is False


# ============================================================
# Csp1dSolutionEnrichment tests
# ============================================================


class TestCsp1dSolutionEnrichment:
    """Csp1dSolutionEnrichment 测试 / Tests."""

    def _make_solution(self) -> Csp1dSolution:
        """创建测试用解决方案 / Create test solution."""
        return Csp1dSolution(
            assignments=(
                Csp1dAssignment(
                    material="m1",
                    cutting_plan="p1",
                    quantity=3,
                    waste=0.5,
                ),
            ),
            total_waste=1.5,
            utilization=0.85,
        )

    def test_add_kpi(self) -> None:
        """添加 KPI / Add KPI."""
        svc = Csp1dSolutionEnrichment()
        svc.add_kpi("throughput", 42.0)
        enriched = svc.enrich(self._make_solution())
        assert enriched.kpi_data["throughput"] == 42.0

    def test_add_trace(self) -> None:
        """添加追踪 / Add trace."""
        svc = Csp1dSolutionEnrichment()
        svc.add_trace("step 1")
        svc.add_trace("step 2")
        enriched = svc.enrich(self._make_solution())
        assert enriched.trace_data == ("step 1", "step 2")

    def test_set_render_data(self) -> None:
        """设置渲染数据 / Set render data."""
        svc = Csp1dSolutionEnrichment()
        svc.set_render_data("color", "red")
        enriched = svc.enrich(self._make_solution())
        assert enriched.render_data["color"] == "red"

    def test_enrich_solution_preserved(self) -> None:
        """增强保留原始方案 / Enrichment preserves solution."""
        solution = self._make_solution()
        svc = Csp1dSolutionEnrichment()
        enriched = svc.enrich(solution)
        assert enriched.solution is solution

    def test_clear(self) -> None:
        """清空增强数据 / Clear enrichment data."""
        svc = Csp1dSolutionEnrichment()
        svc.add_kpi("k", 1.0)
        svc.add_trace("msg")
        svc.clear()
        enriched = svc.enrich(self._make_solution())
        assert enriched.kpi_data == {}
        assert enriched.trace_data == ()


# ============================================================
# CuttingPlanGenerationContext tests
# ============================================================


class TestCuttingPlanGenerationContext:
    """CuttingPlanGenerationContext 测试 / Tests."""

    def test_register(self) -> None:
        """注册生成任务 / Register generation task."""
        ctx = CuttingPlanGenerationContext()
        reg = ctx.register(
            material_length=100.0,
            products=[("p1", 10.0, 10)],
        )
        assert reg.material_length == 100.0

    def test_generate_plans_n_same(self) -> None:
        """n_same 策略生成 / n_same strategy generation."""
        ctx = CuttingPlanGenerationContext()
        plans = ctx.generate_plans(
            material_length=100.0,
            products=[("p1", 20.0, 5)],
            strategy="n_same",
        )
        assert len(plans) > 0

    def test_generate_plans_full_sum(self) -> None:
        """full_sum 策略生成 / full_sum strategy."""
        ctx = CuttingPlanGenerationContext()
        plans = ctx.generate_plans(
            material_length=100.0,
            products=[("p1", 20.0, 3), ("p2", 30.0, 2)],
            strategy="full_sum",
        )
        assert isinstance(plans, list)

    def test_generate_plans_empty(self) -> None:
        """空产品列表 / Empty product list."""
        ctx = CuttingPlanGenerationContext()
        plans = ctx.generate_plans(
            material_length=100.0,
            products=[],
        )
        assert plans == []


# ============================================================
# Generator tests
# ============================================================


class TestFullSumGenerator:
    """FullSumGenerator 测试 / Tests."""

    def test_empty_products(self) -> None:
        """空产品返回空 / Empty products returns empty."""
        gen = FullSumGenerator()
        result = gen.generate(
            material_length=100.0,
            products=[],
        )
        assert result == []

    def test_single_product(self) -> None:
        """单产品生成 / Single product generation."""
        gen = FullSumGenerator()
        result = gen.generate(
            material_length=100.0,
            products=[("p1", 25.0, 5)],
        )
        assert len(result) > 0
        for plan in result:
            assert "p1" in plan


class TestNSameGenerator:
    """NSameGenerator 测试 / Tests."""

    def test_empty_products(self) -> None:
        """空产品返回空 / Empty products returns empty."""
        gen = NSameGenerator()
        result = gen.generate(
            material_length=100.0,
            products=[],
        )
        assert result == []

    def test_single_product_generates_plans(self) -> None:
        """单产品生成多个方案 / Single product plans."""
        gen = NSameGenerator()
        result = gen.generate(
            material_length=100.0,
            products=[("p1", 20.0, 5)],
        )
        assert len(result) > 0
        for plan in result:
            assert set(plan.keys()) == {"p1"}


class TestNSumGenerator:
    """NSumGenerator 测试 / Tests."""

    def test_single_product_returns_empty(self) -> None:
        """单产品返回空（需至少两种）/ Single product empty."""
        gen = NSumGenerator()
        result = gen.generate(
            material_length=100.0,
            products=[("p1", 20.0, 5)],
        )
        assert result == []

    def test_two_products_generates(self) -> None:
        """两产品生成方案 / Two products generate plans."""
        gen = NSumGenerator()
        result = gen.generate(
            material_length=100.0,
            products=[("p1", 20.0, 3), ("p2", 30.0, 2)],
        )
        assert isinstance(result, list)


# ============================================================
# GenerationContribution tests
# ============================================================


class TestGenerationContribution:
    """GenerationContribution 测试 / Tests."""

    def test_create(self) -> None:
        """创建贡献 / Create contribution."""
        c = GenerationContribution.create(
            contributions={"p1": 3, "p2": 2},
            waste_length=5.0,
        )
        assert c.total_cuts == 5
        assert c.waste_length == 5.0

    def test_contribution_of(self) -> None:
        """获取产品贡献 / Get product contribution."""
        c = GenerationContribution.create(
            contributions={"p1": 3, "p2": 2},
        )
        assert c.contribution_of("p1") == 3
        assert c.contribution_of("p2") == 2

    def test_contribution_of_missing(self) -> None:
        """不存在产品贡献为 0 / Missing product is 0."""
        c = GenerationContribution.create(contributions={"p1": 1})
        assert c.contribution_of("unknown") == 0

    def test_has_waste(self) -> None:
        """有余料判断 / Has waste check."""
        c = GenerationContribution.create(
            contributions={"p1": 1},
            waste_length=0.5,
        )
        assert c.has_waste is True

    def test_no_waste(self) -> None:
        """无余料判断 / No waste check."""
        c = GenerationContribution.create(
            contributions={"p1": 1},
            waste_length=0.0,
        )
        assert c.has_waste is False

    def test_is_empty(self) -> None:
        """空贡献判断 / Is empty check."""
        c = GenerationContribution.create(contributions={})
        assert c.is_empty is True

    def test_not_empty(self) -> None:
        """非空贡献 / Not empty contribution."""
        c = GenerationContribution.create(
            contributions={"p1": 1},
        )
        assert c.is_empty is False


# ============================================================
# GenerationParallelism tests
# ============================================================


class TestGenerationParallelism:
    """GenerationParallelism 测试 / Tests."""

    def test_default_values(self) -> None:
        """默认值 / Default values."""
        p = GenerationParallelism()
        assert p.max_workers == 4
        assert p.use_process_pool is False
        assert p.chunk_size == 1

    def test_is_parallel(self) -> None:
        """并行判断 / Is parallel check."""
        p = GenerationParallelism(max_workers=4)
        assert p.is_parallel is True

    def test_is_not_parallel(self) -> None:
        """非并行判断 / Not parallel check."""
        p = GenerationParallelism.sequential()
        assert p.is_parallel is False

    def test_sequential(self) -> None:
        """顺序执行配置 / Sequential config."""
        p = GenerationParallelism.sequential()
        assert p.max_workers == 1

    def test_with_workers(self) -> None:
        """指定并行数配置 / With workers config."""
        p = GenerationParallelism.with_workers(max_workers=8)
        assert p.max_workers == 8

    def test_chunk_items(self) -> None:
        """项目分块 / Chunk items."""
        p = GenerationParallelism(chunk_size=2)
        chunks = p.chunk_items([1, 2, 3, 4, 5])
        assert chunks == [[1, 2], [3, 4], [5]]

    def test_chunk_items_single(self) -> None:
        """单项分块 / Single item chunks."""
        p = GenerationParallelism(chunk_size=1)
        chunks = p.chunk_items([1, 2, 3])
        assert chunks == [[1], [2], [3]]

    def test_execute_parallel_sequential(self) -> None:
        """顺序执行 / Sequential execution."""
        p = GenerationParallelism.sequential()
        result = p.execute_parallel(
            items=[1, 2, 3],
            task=lambda x: x * 2,
        )
        assert result == [2, 4, 6]


# ============================================================
# Constraint pipeline tests
# ============================================================


class TestBatchMinimizationObjective:
    """BatchMinimizationObjective 测试 / Tests."""

    def test_default_values(self) -> None:
        """默认值 / Default values."""
        obj = BatchMinimizationObjective()
        assert obj.batch_penalty == 1.0
        assert obj.setup_penalty == 0.5

    def test_compute_batch_cost(self) -> None:
        """批次成本 / Batch cost."""
        obj = BatchMinimizationObjective()
        assert obj.compute_batch_cost(batch_count=3) == 3.0

    def test_compute_setup_cost(self) -> None:
        """切换成本 / Setup cost."""
        obj = BatchMinimizationObjective()
        assert obj.compute_setup_cost(setup_count=4) == 2.0

    def test_compute_total_cost(self) -> None:
        """总成本 / Total cost."""
        obj = BatchMinimizationObjective()
        cost = obj.compute_total_cost(
            batch_count=3,
            setup_count=4,
        )
        assert cost == 5.0

    def test_apply(self) -> None:
        """应用目标 / Apply objective."""
        obj = BatchMinimizationObjective()
        data = {"key": "value"}
        assert obj.apply(data) is data


class TestDemandConstraintPipeline:
    """DemandConstraintPipeline 测试 / Tests."""

    def test_is_demand_satisfied(self) -> None:
        """需求满足判断 / Demand satisfied check."""
        p = DemandConstraintPipeline()
        assert p.is_demand_satisfied(supplied=10, demanded=8) is True

    def test_is_demand_not_satisfied(self) -> None:
        """需求不满足 / Demand not satisfied."""
        p = DemandConstraintPipeline()
        assert p.is_demand_satisfied(supplied=5, demanded=8) is False

    def test_compute_shortfall(self) -> None:
        """计算缺口 / Compute shortfall."""
        p = DemandConstraintPipeline()
        assert p.compute_shortfall(supplied=5, demanded=8) == 3

    def test_compute_shortfall_none(self) -> None:
        """无缺口 / No shortfall."""
        p = DemandConstraintPipeline()
        assert p.compute_shortfall(supplied=10, demanded=8) == 0

    def test_compute_shortfall_cost(self) -> None:
        """缺口成本 / Shortfall cost."""
        p = DemandConstraintPipeline(shortfall_penalty=100.0)
        cost = p.compute_shortfall_cost(supplied=5, demanded=8)
        assert cost == 300.0

    def test_apply(self) -> None:
        """应用约束 / Apply constraint."""
        p = DemandConstraintPipeline()
        data = {"key": "value"}
        assert p.apply(data) is data


class TestMachineConstraintPipeline:
    """MachineConstraintPipeline 测试 / Tests."""

    def test_is_within_capacity(self) -> None:
        """产能范围内 / Within capacity."""
        p = MachineConstraintPipeline()
        assert p.is_within_capacity(used=5, capacity=10) is True

    def test_is_over_capacity(self) -> None:
        """超出产能 / Over capacity."""
        p = MachineConstraintPipeline()
        assert p.is_within_capacity(used=15, capacity=10) is False

    def test_no_enforce_capacity(self) -> None:
        """不强制产能 / No enforce capacity."""
        p = MachineConstraintPipeline(enforce_capacity=False)
        assert p.is_within_capacity(used=999, capacity=10) is True

    def test_remaining_capacity(self) -> None:
        """剩余产能 / Remaining capacity."""
        p = MachineConstraintPipeline()
        assert p.remaining_capacity(used=3, capacity=10) == 7

    def test_remaining_capacity_no_enforce(self) -> None:
        """不强制时返回完整产能 / Full capacity when not enforced."""
        p = MachineConstraintPipeline(enforce_capacity=False)
        assert p.remaining_capacity(used=3, capacity=10) == 10

    def test_is_compatible(self) -> None:
        """兼容性检查 / Compatibility check."""
        p = MachineConstraintPipeline()
        compat = frozenset({("m1", "p1"), ("m1", "p2")})
        assert (
            p.is_compatible(
                machine_key="m1",
                product_key="p1",
                compatibility=compat,
            )
            is True
        )

    def test_is_not_compatible(self) -> None:
        """不兼容 / Not compatible."""
        p = MachineConstraintPipeline()
        compat = frozenset({("m1", "p1")})
        assert (
            p.is_compatible(
                machine_key="m1",
                product_key="p2",
                compatibility=compat,
            )
            is False
        )

    def test_no_enforce_compatibility(self) -> None:
        """不强制兼容性 / No enforce compatibility."""
        p = MachineConstraintPipeline(enforce_compatibility=False)
        assert (
            p.is_compatible(
                machine_key="m1",
                product_key="p2",
                compatibility=frozenset(),
            )
            is True
        )


class TestMaterialConstraintPipeline:
    """MaterialConstraintPipeline 测试 / Tests."""

    def test_is_within_inventory(self) -> None:
        """库存范围内 / Within inventory."""
        p = MaterialConstraintPipeline()
        assert p.is_within_inventory(used=5.0, available=10.0) is True

    def test_is_over_inventory(self) -> None:
        """超出库存 / Over inventory."""
        p = MaterialConstraintPipeline()
        assert p.is_within_inventory(used=15.0, available=10.0) is False

    def test_no_enforce_inventory(self) -> None:
        """不强制库存 / No enforce inventory."""
        p = MaterialConstraintPipeline(enforce_inventory=False)
        assert p.is_within_inventory(used=999.0, available=10.0) is True

    def test_remaining_inventory(self) -> None:
        """剩余库存 / Remaining inventory."""
        p = MaterialConstraintPipeline()
        rem = p.remaining_inventory(used=3.0, available=10.0)
        assert rem == 7.0

    def test_can_substitute(self) -> None:
        """允许替代 / Can substitute."""
        p = MaterialConstraintPipeline(allow_substitution=True)
        rules = frozenset({("mat_a", "mat_b")})
        assert (
            p.can_substitute(
                original_material="mat_a",
                substitute_material="mat_b",
                substitution_rules=rules,
            )
            is True
        )

    def test_cannot_substitute_disabled(self) -> None:
        """替代禁用 / Substitution disabled."""
        p = MaterialConstraintPipeline(allow_substitution=False)
        rules = frozenset({("mat_a", "mat_b")})
        assert (
            p.can_substitute(
                original_material="mat_a",
                substitute_material="mat_b",
                substitution_rules=rules,
            )
            is False
        )


# ============================================================
# RenderDto tests
# ============================================================


class TestRenderDto:
    """RenderDto 测试 / Tests."""

    def test_create(self) -> None:
        """创建渲染 DTO / Create render DTO."""
        dto = RenderDto.create(
            plan_id="plan1",
            material_key="mat1",
            material_length=100.0,
            products=(("p1", 20.0, 3), ("p2", 30.0, 2)),
        )
        assert dto.plan_id == "plan1"
        assert dto.used_length == pytest.approx(120.0)

    def test_utilization_ratio(self) -> None:
        """利用率 / Utilization ratio."""
        dto = RenderDto.create(
            plan_id="p1",
            material_key="m1",
            material_length=100.0,
            products=(("p1", 20.0, 4),),
        )
        assert dto.utilization_ratio == pytest.approx(0.8)

    def test_utilization_zero_material(self) -> None:
        """零材料长度利用率 / Zero material utilization."""
        dto = RenderDto(material_length=0.0)
        assert dto.utilization_ratio == pytest.approx(0.0)

    def test_product_count(self) -> None:
        """产品种类数 / Product type count."""
        dto = RenderDto.create(
            plan_id="p1",
            material_key="m1",
            material_length=100.0,
            products=(("a", 10.0, 1), ("b", 20.0, 2)),
        )
        assert dto.product_count == 2

    def test_total_cuts(self) -> None:
        """总切割数 / Total cuts."""
        dto = RenderDto.create(
            plan_id="p1",
            material_key="m1",
            material_length=100.0,
            products=(("a", 10.0, 3), ("b", 20.0, 2)),
        )
        assert dto.total_cuts == 5

    def test_to_dict(self) -> None:
        """转换为字典 / Convert to dict."""
        dto = RenderDto.create(
            plan_id="p1",
            material_key="m1",
            material_length=100.0,
            products=(("a", 10.0, 2),),
        )
        d = dto.to_dict()
        assert d["plan_id"] == "p1"
        assert isinstance(d["products"], list)


# ============================================================
# Supporting model tests
# ============================================================


class TestCsp1dAssignment:
    """Csp1dAssignment 测试 / Tests."""

    def test_create(self) -> None:
        """创建分配 / Create assignment."""
        a = Csp1dAssignment(
            material="m1",
            cutting_plan="p1",
            quantity=5,
            waste=1.5,
        )
        assert a.material == "m1"
        assert a.quantity == 5


class TestCsp1dSolution:
    """Csp1dSolution 测试 / Tests."""

    def test_create(self) -> None:
        """创建解决方案 / Create solution."""
        assignments = (
            Csp1dAssignment("m1", "p1", 3, 0.5),
            Csp1dAssignment("m2", "p2", 2, 0.3),
        )
        sol = Csp1dSolution(
            assignments=assignments,
            total_waste=2.1,
            utilization=0.9,
        )
        assert len(sol.assignments) == 2
        assert sol.utilization == pytest.approx(0.9)


class TestConstraints:
    """Constraints 测试 / Tests."""

    def test_default_values(self) -> None:
        """默认值 / Default values."""
        c = Constraints()
        assert c.max_knife_count == 0
        assert c.allow_waste is True
        assert c.precision == pytest.approx(1e-8)


class TestCuttingPlanCanonicalKey:
    """CuttingPlanCanonicalKey 测试 / Tests."""

    def test_create_sorted(self) -> None:
        """创建排序 / Create sorted."""
        key = CuttingPlanCanonicalKey.create(
            items={"b": 2, "a": 1},
        )
        assert key.pattern == (("a", 1), ("b", 2))

    def test_product_keys(self) -> None:
        """产品键列表 / Product keys."""
        key = CuttingPlanCanonicalKey.create(
            items={"a": 1, "b": 2},
        )
        assert key.product_keys == ("a", "b")

    def test_total_quantity(self) -> None:
        """总数量 / Total quantity."""
        key = CuttingPlanCanonicalKey.create(
            items={"a": 3, "b": 4},
        )
        assert key.total_quantity == 7

    def test_contains_product(self) -> None:
        """包含产品 / Contains product."""
        key = CuttingPlanCanonicalKey.create(items={"a": 1})
        assert key.contains_product("a") is True
        assert key.contains_product("b") is False

    def test_quantity_of(self) -> None:
        """产品数量 / Product quantity."""
        key = CuttingPlanCanonicalKey.create(
            items={"a": 3, "b": 5},
        )
        assert key.quantity_of("a") == 3
        assert key.quantity_of("unknown") == 0

    def test_equality(self) -> None:
        """相同模式相等 / Same pattern equality."""
        k1 = CuttingPlanCanonicalKey.create(
            items={"a": 1, "b": 2},
        )
        k2 = CuttingPlanCanonicalKey.create(
            items={"b": 2, "a": 1},
        )
        assert k1 == k2


class TestCuttingPlanConstraint:
    """CuttingPlanConstraint 测试 / Tests."""

    def test_is_active(self) -> None:
        """活跃判断 / Is active check."""
        c = CuttingPlanConstraint(min_quantity=1)
        assert c.is_active is True

    def test_is_not_active(self) -> None:
        """非活跃 / Not active."""
        c = CuttingPlanConstraint(min_quantity=0)
        assert c.is_active is False

    def test_quantity_range(self) -> None:
        """数量范围 / Quantity range."""
        c = CuttingPlanConstraint(
            min_quantity=2,
            max_quantity=10,
        )
        assert c.quantity_range == (2, 10)

    def test_is_satisfied_by(self) -> None:
        """满足约束 / Satisfied by."""
        c = CuttingPlanConstraint(
            min_quantity=2,
            max_quantity=10,
        )
        assert c.is_satisfied_by(5) is True
        assert c.is_satisfied_by(1) is False
        assert c.is_satisfied_by(15) is False


class TestGenerationCollector:
    """GenerationCollector 测试 / Tests."""

    def test_try_collect_unique(self) -> None:
        """收集唯一方案 / Collect unique plan."""
        c = GenerationCollector()
        assert c.try_collect({"a": 1}) is True
        assert c.count == 1

    def test_try_collect_duplicate(self) -> None:
        """跳过重复方案 / Skip duplicate plan."""
        c = GenerationCollector()
        c.try_collect({"a": 1, "b": 2})
        assert c.try_collect({"b": 2, "a": 1}) is False
        assert c.count == 1

    def test_collect_all(self) -> None:
        """批量收集 / Batch collect."""
        c = GenerationCollector()
        n = c.collect_all(
            [
                {"a": 1},
                {"a": 1},
                {"b": 2},
            ]
        )
        assert n == 2
        assert c.count == 2

    def test_is_empty(self) -> None:
        """空判断 / Is empty check."""
        c = GenerationCollector()
        assert c.is_empty is True

    def test_clear(self) -> None:
        """清空 / Clear."""
        c = GenerationCollector()
        c.try_collect({"a": 1})
        c.clear()
        assert c.is_empty is True


class TestGenerationLengthPruning:
    """GenerationLengthPruning 测试 / Tests."""

    def test_should_prune(self) -> None:
        """应剪枝 / Should prune."""
        p = GenerationLengthPruning(min_waste_length=5.0)
        assert p.should_prune(3.0) is True
        assert p.should_prune(6.0) is False

    def test_can_fit_product(self) -> None:
        """可容纳产品 / Can fit product."""
        p = GenerationLengthPruning()
        assert p.can_fit_product(10.0, 8.0) is True
        assert p.can_fit_product(5.0, 8.0) is False

    def test_remaining_after_cut(self) -> None:
        """切割后剩余 / Remaining after cut."""
        p = GenerationLengthPruning()
        assert p.remaining_after_cut(100.0, 30.0) == 70.0

    def test_utilization_ratio(self) -> None:
        """利用率 / Utilization ratio."""
        p = GenerationLengthPruning(material_length=100.0)
        assert p.utilization_ratio(80.0) == pytest.approx(0.8)

    def test_utilization_zero_material(self) -> None:
        """零材料利用率 / Zero material utilization."""
        p = GenerationLengthPruning(material_length=0.0)
        assert p.utilization_ratio(10.0) == pytest.approx(0.0)


class TestCuttingPlanProductOrder:
    """CuttingPlanProductOrder 测试 / Tests."""

    def test_create(self) -> None:
        """创建产品排序 / Create product order."""
        o = CuttingPlanProductOrder.create(
            product_key="p1",
            order_index=0,
            quantity=3,
            width=10.0,
            length=20.0,
        )
        assert o.product_key == "p1"
        assert o.total_width == pytest.approx(30.0)
        assert o.total_length == pytest.approx(60.0)
