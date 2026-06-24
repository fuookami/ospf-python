"""基础模型 / Basic model.

提供优化模型的基础实现。
Provides a basic implementation of an optimization model.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BasicModel:
    """基础模型 / Basic model.

    作为具体模型类型的基类，提供名称管理和基本操作。
    Serves as a base class for concrete model types,
    providing name management and basic operations.

    Attributes:
        name: 模型名称 / The model name.
        constraints: 约束列表 / List of constraints.
        objectives: 目标函数列表 / List of objectives.
    """

    name: str = ""
    constraints: list[object] = field(default_factory=list)
    objectives: list[object] = field(default_factory=list)

    def add_constraint(self, constraint: object) -> None:
        """添加约束 / Add a constraint.

        Args:
            constraint: 约束对象 / The constraint object.
        """
        self.constraints.append(constraint)

    def add_objective(self, objective: object) -> None:
        """添加目标函数 / Add an objective.

        Args:
            objective: 目标函数对象 / The objective object.
        """
        self.objectives.append(objective)
