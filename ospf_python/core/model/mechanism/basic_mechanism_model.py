"""基础机制模型 / Basic mechanism model.

定义机制模型的基础功能。
Defines base functionality for mechanism models.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BasicMechanismModel:
    """基础机制模型 / Basic mechanism model.

    提供机制模型的基本结构，包括约束和变量的注册。
    Provides the basic structure for mechanism models,
    including registration of constraints and variables.

    Attributes:
        name: 模型名称 / The model name.
        registered_constraints: 已注册的约束列表 / List of
            registered constraints.
        registered_variables: 已注册的变量名集合 / Set of
            registered variable names.
    """

    name: str = ""
    registered_constraints: list[object] = field(
        default_factory=list,
    )
    registered_variables: set[str] = field(default_factory=set)

    def register_variable(self, name: str) -> None:
        """注册变量 / Register a variable.

        Args:
            name: 变量名称 / The variable name.
        """
        self.registered_variables.add(name)

    def register_constraint(self, constraint: object) -> None:
        """注册约束 / Register a constraint.

        Args:
            constraint: 约束对象 / The constraint object.
        """
        self.registered_constraints.append(constraint)
