"""CSP1D 切割方案生成上下文。

管理切割方案生成的入口与生命周期。
Context for cutting plan generation lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.generation_constraints import (
    GenerationConstraints,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.dfs_generator import (
    DfsGenerator,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.full_sum_generator import (
    FullSumGenerator,
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

# 生成器联合类型 / Generator union type
_Generator = Union[
    FullSumGenerator,
    NSameGenerator,
    NSumGenerator,
    DfsGenerator,
]


@dataclass(frozen=True)
class CuttingPlanGenerationContext:
    """切割方案生成上下文 / Cutting plan generation context.

    管理切割方案生成的完整生命周期，包括注册产品
    信息、选择生成策略并执行方案生成。
    Manages the full lifecycle of cutting plan generation,
    including registering product info, selecting
    generation strategy, and executing plan generation.

    Attributes:
        constraints: 生成约束集。
            Generation constraints.
        parallelism: 并行配置。
            Parallelism configuration.
    """

    constraints: GenerationConstraints = field(
        default_factory=GenerationConstraints,
    )
    """生成约束集 / Generation constraints."""

    parallelism: GenerationParallelism = field(
        default_factory=GenerationParallelism,
    )
    """并行配置 / Parallelism configuration."""

    def register(
        self,
        *,
        material_length: float,
        products: list[tuple[str, float, int]],
    ) -> RegisteredGeneration:
        """注册材料和产品信息，创建注册后的生成任务。

        Register material and product info, creating
        a registered generation task.

        Args:
            material_length: 原材料长度。
                Material length.
            products: 产品列表，每项为
                (产品键, 产品长度, 最大数量)。
                Product list, each item is
                (product_key, product_length, max_qty).

        Returns:
            已注册的生成任务。
            Registered generation task.
        """
        return RegisteredGeneration(
            material_length=material_length,
            products=list(products),
            constraints=self.constraints,
            parallelism=self.parallelism,
        )

    def generate_plans(
        self,
        *,
        material_length: float,
        products: list[tuple[str, float, int]],
        strategy: str = "dfs",
    ) -> list[dict[str, int]]:
        """生成切割方案。

        Generate cutting plans.

        Args:
            material_length: 原材料长度。
                Material length.
            products: 产品列表，每项为
                (产品键, 产品长度, 最大数量)。
                Product list, each item is
                (product_key, product_length, max_qty).
            strategy: 生成策略，可选
                "dfs"、"full_sum"、"n_same"、"n_sum"。
                Generation strategy, one of
                "dfs", "full_sum", "n_same", "n_sum".

        Returns:
            切割方案列表。
            List of cutting plans.
        """
        reg = self.register(
            material_length=material_length,
            products=products,
        )
        return reg.execute(strategy=strategy)


@dataclass
class RegisteredGeneration:
    """已注册的生成任务 / Registered generation task.

    持有材料和产品信息，可选择不同策略执行生成。
    Holds material and product info, allowing execution
    with different strategies.

    Attributes:
        material_length: 原材料长度。
            Material length.
        products: 产品列表。
            Product list.
        constraints: 生成约束集。
            Generation constraints.
        parallelism: 并行配置。
            Parallelism config.
    """

    material_length: float = 0.0
    """原材料长度 / Material length."""

    products: list[tuple[str, float, int]] = field(
        default_factory=list,
    )
    """产品列表 / Product list."""

    constraints: GenerationConstraints = field(
        default_factory=GenerationConstraints,
    )
    """生成约束集 / Generation constraints."""

    parallelism: GenerationParallelism = field(
        default_factory=GenerationParallelism,
    )
    """并行配置 / Parallelism config."""

    def execute(
        self,
        *,
        strategy: str = "dfs",
    ) -> list[dict[str, int]]:
        """使用指定策略执行生成。

        Execute generation with the specified strategy.

        Args:
            strategy: 生成策略。
                Generation strategy.

        Returns:
            切割方案列表。
            List of cutting plans.
        """
        gen: _Generator
        if strategy == "full_sum":
            gen = FullSumGenerator(
                constraints=self.constraints,
            )
        elif strategy == "n_same":
            gen = NSameGenerator(
                constraints=self.constraints,
            )
        elif strategy == "n_sum":
            gen = NSumGenerator(
                constraints=self.constraints,
            )
        else:
            gen = DfsGenerator(
                constraints=self.constraints,
            )
        return gen.generate(
            material_length=self.material_length,
            products=self.products,
        )
