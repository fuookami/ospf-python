"""任务数量最小化 / Task amount minimization.

生成最小化任务数量的目标函数数据，减少任务总数以
降低调度复杂度和管理成本。
Generates objective function data for minimizing the number
of tasks, reducing total task count to lower scheduling
complexity and management costs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskAmountObjectiveTerm:
    """任务数量目标函数项 / Task amount objective term.

    Attributes:
        task_key: 任务标识 / Task identifier.
        weight: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Associated variable name.
    """

    task_key: str
    weight: float
    variable_name: str


@dataclass(frozen=True)
class TaskAmountMinimization:
    """任务数量最小化 / Task amount minimization.

    构建最小化任务使用数量的目标函数项，鼓励调度方案
    使用更少的任务。适用于希望合并小任务、减少任务切换
    次数的场景。
    Builds objective function terms for minimizing the number
    of tasks used, encouraging scheduling plans with fewer
    tasks. Applicable when the goal is to merge small tasks
    and reduce task switching frequency.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "task_amount_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        task_keys: tuple[str, ...],
        weights: dict[str, float] | None = None,
    ) -> tuple[TaskAmountObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all task keys.

        Args:
            task_keys: 任务标识列表。/ Task key list.
            weights: 自定义权重映射。/ Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[TaskAmountObjectiveTerm] = []
        for tk in task_keys:
            weight = effective_weights.get(
                tk,
                self.default_weight,
            )
            if weight > 0.0:
                terms.append(
                    TaskAmountObjectiveTerm(
                        task_key=tk,
                        weight=weight,
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
        return f"task_amt_{task_key}"
