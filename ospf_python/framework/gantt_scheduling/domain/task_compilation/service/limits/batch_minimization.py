"""批次数量最小化 / Batch minimization.

生成最小化批次数量的目标函数数据，减少批次总数以
降低切换和管理成本。
Generates objective function data for minimizing the number
of batches, reducing total batch count to lower switching
and management costs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BatchObjectiveTerm:
    """批次目标函数项 / Batch objective function term.

    Attributes:
        batch_key: 批次标识 / Batch identifier.
        weight: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Associated variable name.
    """

    batch_key: str
    weight: float
    variable_name: str


@dataclass(frozen=True)
class BatchMinimization:
    """批次数量最小化 / Batch minimization.

    构建最小化批次使用数量的目标函数项，鼓励调度方案
    使用更少的批次。适用于希望合并小批次、减少批次切换
    次数的场景。
    Builds objective function terms for minimizing the number
    of batches used, encouraging scheduling plans with fewer
    batches. Applicable when the goal is to merge small batches
    and reduce batch switching frequency.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "batch_amount_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        batch_keys: tuple[str, ...],
        weights: dict[str, float] | None = None,
    ) -> tuple[BatchObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all batch keys.

        Args:
            batch_keys: 批次标识列表。/ Batch key list.
            weights: 自定义权重映射。/ Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[BatchObjectiveTerm] = []
        for bk in batch_keys:
            weight = effective_weights.get(
                bk,
                self.default_weight,
            )
            if weight > 0.0:
                terms.append(
                    BatchObjectiveTerm(
                        batch_key=bk,
                        weight=weight,
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
        return f"amount_{batch_key}"
