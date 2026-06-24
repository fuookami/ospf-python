"""元模型 / Meta model.

轴心模型，负责注册变量、约束和目标函数。
The axis model responsible for registering variables,
constraints, and objectives.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.core.model.basic.registration_status import (
    RegistrationStatus,
)


@dataclass
class MetaModel:
    """元模型 / Meta model.

    优化模型的核心注册中心，管理变量、约束和目标函数的注册。
    The core registry for optimization models, managing
    the registration of variables, constraints, and objectives.

    Attributes:
        name: 模型名称 / The model name.
        variables: 已注册的变量映射 / Registered variable mapping.
        constraints: 已注册的约束映射 / Registered constraint
            mapping.
        objectives: 已注册的目标函数映射 / Registered objective
            mapping.
    """

    name: str = ""
    variables: dict[str, object] = field(default_factory=dict)
    constraints: dict[str, object] = field(default_factory=dict)
    objectives: dict[str, object] = field(default_factory=dict)

    def register_variable(
        self,
        name: str,
        variable: object,
    ) -> RegistrationStatus:
        """注册变量 / Register a variable.

        Args:
            name: 变量名称 / The variable name.
            variable: 变量对象 / The variable object.

        Returns:
            注册状态 / The registration status.
        """
        if name in self.variables:
            return RegistrationStatus.ALREADY_EXISTS
        self.variables[name] = variable
        return RegistrationStatus.REGISTERED

    def register_constraint(
        self,
        name: str,
        constraint: object,
    ) -> RegistrationStatus:
        """注册约束 / Register a constraint.

        Args:
            name: 约束名称 / The constraint name.
            constraint: 约束对象 / The constraint object.

        Returns:
            注册状态 / The registration status.
        """
        if name in self.constraints:
            return RegistrationStatus.ALREADY_EXISTS
        self.constraints[name] = constraint
        return RegistrationStatus.REGISTERED

    def register_objective(
        self,
        name: str,
        objective: object,
    ) -> RegistrationStatus:
        """注册目标函数 / Register an objective.

        Args:
            name: 目标函数名称 / The objective name.
            objective: 目标函数对象 / The objective object.

        Returns:
            注册状态 / The registration status.
        """
        if name in self.objectives:
            return RegistrationStatus.ALREADY_EXISTS
        self.objectives[name] = objective
        return RegistrationStatus.REGISTERED

    def find_variable(self, name: str) -> object | None:
        """查找变量 / Find a variable.

        Args:
            name: 变量名称 / The variable name.

        Returns:
            变量对象或 None / The variable object or None.
        """
        return self.variables.get(name)

    def find_constraint(self, name: str) -> object | None:
        """查找约束 / Find a constraint.

        Args:
            name: 约束名称 / The constraint name.

        Returns:
            约束对象或 None / The constraint object or None.
        """
        return self.constraints.get(name)
