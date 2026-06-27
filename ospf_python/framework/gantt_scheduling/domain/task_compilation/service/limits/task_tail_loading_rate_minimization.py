"""任务尾部负载率最小化 / Task tail loading rate minimization.

生成最小化任务尾部负载率的目标函数数据，降低任务完成后的
资源占用率。
Generates objective function data for minimizing task tail
loading rate, reducing resource occupation after task
completion.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TailLoadingRateObjectiveTerm:
    """尾部负载率目标函数项 / Tail loading rate objective term.

    Attributes:
        task_key: 任务标识 / Task identifier.
        resource_key: 资源标识 / Resource identifier.
        weight: 权重系数 / Weight coefficient.
        loading_rate: 负载率 / Loading rate.
        variable_name: 关联变量名 / Associated variable name.
    """

    task_key: str
    resource_key: str
    weight: float
    loading_rate: float
    variable_name: str


@dataclass(frozen=True)
class TaskTailLoadingRateMinimization:
    """任务尾部负载率最小化 / Task tail loading rate minimization.

    构建最小化任务尾部负载率的目标函数项，鼓励调度方案降低
    任务完成后的资源占用。适用于希望平衡资源利用、避免尾部
    资源过载的场景。
    Builds objective function terms for minimizing task tail
    loading rate, encouraging scheduling plans that reduce
    resource occupation after task completion. Applicable
    when the goal is to balance resource utilization and avoid
    tail resource overload.

    Attributes:
        objective_name: 目标函数名称 / Objective name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "tail_loading_rate_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        task_keys: tuple[str, ...],
        loading_rates: dict[str, float],
        weights: dict[str, float] | None = None,
    ) -> tuple[TailLoadingRateObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms.

        Args:
            task_keys: 任务标识列表 / Task key list.
            loading_rates: 负载率映射 / Loading rate mapping.
            weights: 自定义权重映射 / Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[TailLoadingRateObjectiveTerm] = []
        for tk in task_keys:
            rate = loading_rates.get(tk, 0.0)
            weight = effective_weights.get(
                tk,
                self.default_weight,
            )
            if weight > 0.0 and rate > 0.0:
                terms.append(
                    TailLoadingRateObjectiveTerm(
                        task_key=tk,
                        resource_key="",
                        weight=weight,
                        loading_rate=rate,
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
        return f"tail_rate_{task_key}"
