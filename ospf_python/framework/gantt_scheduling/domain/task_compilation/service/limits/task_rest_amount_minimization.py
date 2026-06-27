"""任务剩余数量最小化 / Task rest amount minimization.

生成最小化任务剩余数量的目标函数数据，减少未完成的
任务积压。
Generates objective function data for minimizing the number
of remaining (rest) tasks, reducing unfinished task backlog.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RestAmountObjectiveTerm:
    """剩余数量目标函数项 / Rest amount objective term.

    Attributes:
        task_key: 任务标识 / Task identifier.
        weight: 权重系数 / Weight coefficient.
        rest_amount: 剩余量 / Rest amount.
        variable_name: 关联变量名 / Associated variable name.
    """

    task_key: str
    weight: float
    rest_amount: float
    variable_name: str


@dataclass(frozen=True)
class TaskRestAmountMinimization:
    """任务剩余数量最小化 / Task rest amount minimization.

    构建最小化任务剩余数量的目标函数项，鼓励调度方案
    完成更多任务、减少未完成的任务积压。适用于希望最大化
    任务完成率的场景。
    Builds objective function terms for minimizing the number
    of remaining tasks, encouraging scheduling plans that
    complete more tasks and reduce unfinished backlog.
    Applicable when maximizing task completion rate is desired.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "task_rest_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        task_keys: tuple[str, ...],
        rest_amounts: dict[str, float],
        weights: dict[str, float] | None = None,
    ) -> tuple[RestAmountObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms.

        Args:
            task_keys: 任务标识列表 / Task key list.
            rest_amounts: 剩余量映射 / Rest amount mapping.
            weights: 自定义权重映射 / Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[RestAmountObjectiveTerm] = []
        for tk in task_keys:
            rest = rest_amounts.get(tk, 0.0)
            weight = effective_weights.get(
                tk,
                self.default_weight,
            )
            if weight > 0.0 and rest > 0.0:
                terms.append(
                    RestAmountObjectiveTerm(
                        task_key=tk,
                        weight=weight,
                        rest_amount=rest,
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
        return f"rest_{task_key}"
