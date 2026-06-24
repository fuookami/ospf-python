"""CSP1D 产出率上下文。

管理产出率优化的入口与生命周期。
Context for yield optimization lifecycle.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field


def _load_yield_modeling_config():  # type: ignore[no-untyped-def]
    """加载 YieldModelingConfig / Load YieldModelingConfig."""
    mod = importlib.import_module(
        "ospf_python.framework.csp1d.domain.yield.model.yield_modeling_config"
    )
    return mod.YieldModelingConfig


def _load_yield_constraint_pipeline():  # type: ignore[no-untyped-def]
    """加载 YieldConstraintPipeline."""
    mod = importlib.import_module(
        "ospf_python.framework.csp1d.domain"
        ".yield.service.pipeline.yield_constraint_pipeline"
    )
    return mod.YieldConstraintPipeline


def _load_yield_objective_pipeline():  # type: ignore[no-untyped-def]
    """加载 YieldObjectivePipeline."""
    mod = importlib.import_module(
        "ospf_python.framework.csp1d.domain"
        ".yield.service.pipeline.yield_objective_pipeline"
    )
    return mod.YieldObjectivePipeline


def _load_yield_aggregation():  # type: ignore[no-untyped-def]
    """加载 YieldAggregation."""
    mod = importlib.import_module(
        "ospf_python.framework.csp1d.domain.yield.yield_aggregation"
    )
    return mod.YieldAggregation


@dataclass(frozen=True)
class YieldContext:
    """产出率上下文 / Yield context.

    管理产出率优化的完整生命周期，包括注册产品
    产出信息、执行约束和目标管线。
    Manages the full lifecycle of yield optimization,
    including registering product yield info,
    executing constraint and objective pipelines.

    Attributes:
        config: 建模配置。
            Modeling config.
        constraint_pipeline: 产出率约束管线。
            Yield constraint pipeline.
        objective_pipeline: 产出率目标管线。
            Yield objective pipeline.
    """

    config: object = field(
        default_factory=lambda: _load_yield_modeling_config()(),
    )
    """建模配置 / Modeling config."""

    constraint_pipeline: object = field(
        default_factory=lambda: _load_yield_constraint_pipeline()(),
    )
    """约束管线 / Constraint pipeline."""

    objective_pipeline: object = field(
        default_factory=lambda: _load_yield_objective_pipeline()(),
    )
    """目标管线 / Objective pipeline."""

    def register(self) -> object:
        """注册产出率信息。

        Register yield info.

        Returns:
            产出率聚合。
            Yield aggregation.
        """
        yield_agg_cls = _load_yield_aggregation()
        return yield_agg_cls.create(config=self.config)

    def apply_constraints(
        self,
        aggregation: object,
    ) -> object:
        """应用产出率约束管线。

        Apply yield constraint pipeline.

        Args:
            aggregation: 当前聚合。
                Current aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return self.constraint_pipeline.apply(aggregation)

    def apply_objectives(
        self,
        aggregation: object,
    ) -> object:
        """应用产出率目标管线。

        Apply yield objective pipeline.

        Args:
            aggregation: 当前聚合。
                Current aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return self.objective_pipeline.apply(aggregation)
