"""更优任务最大化 / Better task maximization.

生成最大化任务质量的目标函数数据，优先选择质量更高的
任务配置。
Generates objective function data for maximizing task
quality, preferring higher-quality task configurations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskQualityObjectiveTerm:
    """任务质量目标函数项 / Task quality objective function term.

    Attributes:
        task_key: 任务标识 / Task identifier.
        weight: 权重系数 / Weight coefficient.
        quality_score: 质量得分 / Quality score.
        variable_name: 关联变量名 / Associated variable name.
    """

    task_key: str
    weight: float
    quality_score: float
    variable_name: str


@dataclass(frozen=True)
class BetterTaskMaximization:
    """更优任务最大化 / Better task maximization.

    构建最大化任务质量的目标函数项，鼓励调度方案选择
    质量得分更高的任务配置。适用于存在多种可选任务方案
    且希望优选最佳方案的场景。
    Builds objective function terms for maximizing task quality,
    encouraging scheduling plans that select higher-quality
    task configurations. Applicable when multiple task
    configurations are available and the best one is preferred.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "better_task_max"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        task_keys: tuple[str, ...],
        quality_scores: dict[str, float],
        weights: dict[str, float] | None = None,
    ) -> tuple[TaskQualityObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all task keys.

        Args:
            task_keys: 任务标识列表。/ Task key list.
            quality_scores: 质量得分映射。/ Quality score mapping.
            weights: 自定义权重映射。/ Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[TaskQualityObjectiveTerm] = []
        for tk in task_keys:
            weight = effective_weights.get(
                tk,
                self.default_weight,
            )
            score = quality_scores.get(tk, 0.0)
            if weight > 0.0 and score > 0.0:
                terms.append(
                    TaskQualityObjectiveTerm(
                        task_key=tk,
                        weight=weight,
                        quality_score=score,
                        variable_name=self._var_name(tk),
                    )
                )
        return tuple(terms)

    def objective_name_for(
        self,
        task_key: str,
    ) -> str:
        """生成任务特定的目标函数名称。"""
        return f"{self.objective_name}_{task_key}"

    def _var_name(self, task_key: str) -> str:
        """生成变量名称。"""
        return f"quality_{task_key}"
