"""更优批次最大化 / Batch maximization.

生成最大化批次质量的目标函数数据，优先选择质量更高的
批次配置。
Generates objective function data for maximizing batch
quality, preferring higher-quality batch configurations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityObjectiveTerm:
    """质量目标函数项 / Quality objective function term.

    Attributes:
        batch_key: 批次标识 / Batch identifier.
        weight: 权重系数 / Weight coefficient.
        quality_score: 质量得分 / Quality score.
        variable_name: 关联变量名 / Associated variable name.
    """

    batch_key: str
    weight: float
    quality_score: float
    variable_name: str


@dataclass(frozen=True)
class BatchMaximization:
    """更优批次最大化 / Batch maximization.

    构建最大化批次质量的目标函数项，鼓励调度方案选择
    质量得分更高的批次配置。适用于存在多种可选批次方案
    且希望优选最佳方案的场景。
    Builds objective function terms for maximizing batch quality,
    encouraging scheduling plans that select higher-quality
    batch configurations. Applicable when multiple batch
    configurations are available and the best one is preferred.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "batch_quality_max"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        batch_keys: tuple[str, ...],
        quality_scores: dict[str, float],
        weights: dict[str, float] | None = None,
    ) -> tuple[QualityObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all batch keys.

        Args:
            batch_keys: 批次标识列表。/ Batch key list.
            quality_scores: 质量得分映射。/ Quality score mapping.
            weights: 自定义权重映射。/ Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[QualityObjectiveTerm] = []
        for bk in batch_keys:
            weight = effective_weights.get(
                bk,
                self.default_weight,
            )
            score = quality_scores.get(bk, 0.0)
            if weight > 0.0 and score > 0.0:
                terms.append(
                    QualityObjectiveTerm(
                        batch_key=bk,
                        weight=weight,
                        quality_score=score,
                        variable_name=self._var_name(bk),
                    )
                )
        return tuple(terms)

    def objective_name_for(
        self,
        batch_key: str,
    ) -> str:
        """生成批次特定的目标函数名称。"""
        return f"{self.objective_name}_{batch_key}"

    def _var_name(self, batch_key: str) -> str:
        """生成变量名称。"""
        return f"quality_{batch_key}"
