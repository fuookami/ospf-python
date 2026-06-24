"""二次求解器抽象基类 / Quadratic solver abstract base class.

定义二次规划和混合整数二次规划求解器的接口。
Defines the interface for QP and MIQP solvers.
"""

from __future__ import annotations

import abc

from ospf_python.core.solver.solver import Solver


class QuadraticSolver(Solver, abc.ABC):
    """二次求解器抽象基类 / Abstract base class for quadratic solvers.

    所有支持二次规划(QP)和混合整数二次规划(MIQP)的
    求解器必须实现此接口。
    All solvers supporting quadratic programming (QP) and
    mixed-integer quadratic programming (MIQP) must implement
    this interface.
    """

    @abc.abstractmethod
    def supports_quadratic_objective(self) -> bool:
        """是否支持二次目标函数 / Whether quadratic objectives
        are supported.

        Returns:
            支持二次目标函数时返回 True / True when quadratic
            objectives are supported.
        """
        ...

    @abc.abstractmethod
    def supports_quadratic_constraint(self) -> bool:
        """是否支持二次约束 / Whether quadratic constraints
        are supported.

        Returns:
            支持二次约束时返回 True / True when quadratic
            constraints are supported.
        """
        ...
