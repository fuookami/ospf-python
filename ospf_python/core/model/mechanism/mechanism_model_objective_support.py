"""机制模型目标函数支持 / Mechanism model objective support.

为机制模型提供目标函数管理功能。
Provides objective function management for mechanism models.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MechanismModelObjectiveSupport:
    """机制模型目标函数支持 / Mechanism model objective support.

    管理模型中的目标函数添加和维护。
    Manages the addition and maintenance of objective
    functions in a model.

    Attributes:
        objectives: 目标函数列表 / List of objective functions.
        minimize: 是否为最小化问题 / Whether it is a
            minimization problem.
    """

    objectives: list[object] = field(default_factory=list)
    minimize: bool = True

    def add_objective(self, objective: object) -> None:
        """添加目标函数 / Add an objective function.

        Args:
            objective: 目标函数对象 / The objective function
                object.
        """
        self.objectives.append(objective)

    def clear_objectives(self) -> None:
        """清除所有目标函数 / Clear all objective functions."""
        self.objectives.clear()

    @property
    def objective_count(self) -> int:
        """目标函数数量 / Number of objective functions."""
        return len(self.objectives)
