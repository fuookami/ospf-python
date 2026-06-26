"""Bunch generation 测试 / Bunch generation tests.

覆盖 GenerationStrategy、GreedyGenerator、
BalancedGenerator 和 GenerationSelector。
Covers GenerationStrategy, GreedyGenerator,
BalancedGenerator, and GenerationSelector.
"""

from __future__ import annotations

import pytest

from examples.framework_demo.demo4.domain.bunch_generation.model.generation_aggregation import (
    GenerationAggregation,
)
from examples.framework_demo.demo4.domain.bunch_generation.model.generation_config import (
    GenerationConfig,
)
from examples.framework_demo.demo4.domain.bunch_generation.model.generation_context import (
    GenerationContext,
)
from examples.framework_demo.demo4.domain.bunch_generation.model.generation_result import (
    GenerationResult,
)
from examples.framework_demo.demo4.domain.bunch_generation.model.generation_strategy import (
    GenerationStrategy,
)
from examples.framework_demo.demo4.domain.bunch_generation.service.balanced_generator import (
    BalancedGenerator,
)
from examples.framework_demo.demo4.domain.bunch_generation.service.generation_selector import (
    GenerationSelector,
)
from examples.framework_demo.demo4.domain.bunch_generation.service.greedy_generator import (
    GreedyGenerator,
    TaskSlot,
)


class TestGenerationStrategy:
    """GenerationStrategy 测试 / Strategy tests."""

    def test_description(self) -> None:
        """描述 / Description."""
        assert len(GenerationStrategy.GREEDY.description) > 0

    def test_short_name(self) -> None:
        """简称 / Short name."""
        assert len(GenerationStrategy.BALANCED.short_name) > 0

    def test_all_values(self) -> None:
        """所有值 / All values."""
        values = set(GenerationStrategy)
        assert GenerationStrategy.GREEDY in values
        assert GenerationStrategy.BALANCED in values
        assert GenerationStrategy.PRIORITY in values


class TestGenerationConfig:
    """GenerationConfig 测试 / Config tests."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        c = GenerationConfig()
        assert c.max_bunch_size == 50
        assert c.min_utilization == pytest.approx(0.6)

    def test_is_valid(self) -> None:
        """有效性 / Validity."""
        c = GenerationConfig(max_bunch_size=10, min_utilization=0.5)
        assert c.is_valid is True

    def test_with_max_bunch_size(self) -> None:
        """修改最大任务组大小 / Update max bunch size."""
        c = GenerationConfig()
        c2 = c.with_max_bunch_size(100)
        assert c2.max_bunch_size == 100
        assert c.max_bunch_size == 50

    def test_validate(self) -> None:
        """校验 / Validate."""
        c = GenerationConfig(max_bunch_size=0, min_utilization=-0.1)
        errors = c.validate()
        assert len(errors) > 0


class TestGenerationResult:
    """GenerationResult 测试 / Result tests."""

    def test_bunch_count(self) -> None:
        "Bunch count."
        r = GenerationResult(
            bunches=("B1", "B2", "B3"),
            score=0.85,
            strategy=GenerationStrategy.GREEDY,
        )
        assert r.bunch_count == 3

    def test_is_viable(self) -> None:
        """是否可行 / Is viable."""
        viable = GenerationResult(
            bunches=("B1",),
            score=0.7,
            strategy=GenerationStrategy.GREEDY,
        )
        not_viable = GenerationResult(
            bunches=(),
            score=0.0,
            strategy=GenerationStrategy.GREEDY,
        )
        assert viable.is_viable is True
        assert not_viable.is_viable is False

    def test_is_better_than(self) -> None:
        """比较 / Comparison."""
        r1 = GenerationResult(
            bunches=("B1",),
            score=0.9,
            strategy=GenerationStrategy.GREEDY,
        )
        r2 = GenerationResult(
            bunches=("B1", "B2"),
            score=0.5,
            strategy=GenerationStrategy.BALANCED,
        )
        assert r1.is_better_than(r2) is True


class TestGreedyGenerator:
    """GreedyGenerator 测试 / Greedy generator tests."""

    def test_generate(self) -> None:
        """生成 / Generate."""
        config = GenerationConfig(
            max_bunch_size=5,
            min_utilization=0.5,
        )
        gen = GreedyGenerator(config)
        tasks = (
            TaskSlot("T1", "aircraft", 1.0),
            TaskSlot("T2", "aircraft", 2.0),
            TaskSlot("T3", "aircraft", 1.5),
        )
        result = gen.generate(tasks)
        assert result.strategy == GenerationStrategy.GREEDY
        assert result.bunch_count >= 0

    def test_empty_tasks(self) -> None:
        """空任务 / Empty tasks."""
        gen = GreedyGenerator(GenerationConfig())
        result = gen.generate(())
        assert result.bunch_count == 0


class TestBalancedGenerator:
    """BalancedGenerator 测试 / Balanced generator tests."""

    def test_generate(self) -> None:
        """生成 / Generate."""
        config = GenerationConfig(
            max_bunch_size=5,
            min_utilization=0.5,
        )
        from examples.framework_demo.demo4.domain.bunch_generation.service.balanced_generator import (
            TaskSlot as BTaskSlot,
        )

        gen = BalancedGenerator(config)
        tasks = (
            BTaskSlot("T1", "aircraft", 1.0),
            BTaskSlot("T2", "aircraft", 2.0),
            BTaskSlot("T3", "aircraft", 1.5),
            BTaskSlot("T4", "aircraft", 0.5),
        )
        result = gen.generate(tasks)
        assert result.strategy == GenerationStrategy.BALANCED


class TestGenerationContext:
    """GenerationContext 测试 / Context tests."""

    def test_register_and_get(self) -> None:
        """注册和查询 / Register and get."""
        ctx = GenerationContext()
        gen = GreedyGenerator(GenerationConfig())
        ctx.register(GenerationStrategy.GREEDY, gen)
        assert ctx.size == 1
        assert ctx.get(GenerationStrategy.GREEDY) is gen

    def test_available_strategies(self) -> None:
        """可用策略 / Available strategies."""
        ctx = GenerationContext()
        ctx.register(
            GenerationStrategy.GREEDY,
            GreedyGenerator(GenerationConfig()),
        )
        ctx.register(
            GenerationStrategy.BALANCED,
            BalancedGenerator(GenerationConfig()),
        )
        strategies = ctx.available_strategies()
        assert len(strategies) == 2

    def test_is_registered(self) -> None:
        """是否已注册 / Is registered."""
        ctx = GenerationContext()
        assert ctx.is_registered(GenerationStrategy.GREEDY) is False
        ctx.register(
            GenerationStrategy.GREEDY,
            GreedyGenerator(GenerationConfig()),
        )
        assert ctx.is_registered(GenerationStrategy.GREEDY) is True

    def test_unregister(self) -> None:
        """注销 / Unregister."""
        ctx = GenerationContext()
        ctx.register(
            GenerationStrategy.GREEDY,
            GreedyGenerator(GenerationConfig()),
        )
        assert ctx.unregister(GenerationStrategy.GREEDY) is True
        assert ctx.size == 0


class TestGenerationSelector:
    """GenerationSelector 测试 / Selector tests."""

    def test_select_best(self) -> None:
        """选择最优 / Select best."""
        ctx = GenerationContext()
        ctx.register(
            GenerationStrategy.GREEDY,
            GreedyGenerator(GenerationConfig()),
        )
        ctx.register(
            GenerationStrategy.BALANCED,
            BalancedGenerator(GenerationConfig()),
        )
        selector = GenerationSelector(ctx)
        tasks = (
            TaskSlot("T1", "aircraft", 1.0),
            TaskSlot("T2", "aircraft", 2.0),
        )
        best = selector.select_best(tasks)
        assert best is not None

    def test_evaluate_all(self) -> None:
        """评估所有 / Evaluate all."""
        ctx = GenerationContext()
        ctx.register(
            GenerationStrategy.GREEDY,
            GreedyGenerator(GenerationConfig()),
        )
        selector = GenerationSelector(ctx)
        tasks = (TaskSlot("T1", "aircraft", 1.0),)
        results = selector.evaluate_all(tasks)
        assert len(results) == 1

    def test_select_by_strategy(self) -> None:
        """按策略选择 / Select by strategy."""
        ctx = GenerationContext()
        ctx.register(
            GenerationStrategy.GREEDY,
            GreedyGenerator(GenerationConfig()),
        )
        selector = GenerationSelector(ctx)
        tasks = (TaskSlot("T1", "aircraft", 1.0),)
        result = selector.select_by_strategy(GenerationStrategy.GREEDY, tasks)
        assert result is not None


class TestGenerationAggregation:
    """GenerationAggregation 测试 / Aggregation tests."""

    def test_from_results(self) -> None:
        """从结果构建 / Build from results."""
        r1 = GenerationResult(
            bunches=("B1",),
            score=0.8,
            strategy=GenerationStrategy.GREEDY,
        )
        r2 = GenerationResult(
            bunches=("B2", "B3"),
            score=0.6,
            strategy=GenerationStrategy.BALANCED,
        )
        agg = GenerationAggregation.from_results((r1, r2))
        assert agg.strategy_count == 2
        assert agg.best_strategy == GenerationStrategy.GREEDY

    def test_best_result(self) -> None:
        """最优结果 / Best result."""
        r = GenerationResult(
            bunches=("B1",),
            score=0.9,
            strategy=GenerationStrategy.GREEDY,
        )
        agg = GenerationAggregation.from_results((r,))
        assert agg.best_result is r
