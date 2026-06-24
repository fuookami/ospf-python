"""线性求解器抽象基类 / Linear solver abstract base class.

定义线性规划和混合整数线性规划求解器的接口。
Defines the interface for LP and MILP solvers.
"""

from __future__ import annotations

import abc

from ospf_python.core.solver.solver import Solver


class LinearSolver(Solver, abc.ABC):
    """线性求解器抽象基类 / Abstract base class for linear solvers.

    所有支持线性规划(LP)和混合整数线性规划(MILP)的
    求解器必须实现此接口。
    All solvers supporting linear programming (LP) and mixed-integer
    linear programming (MILP) must implement this interface.
    """

    @abc.abstractmethod
    def supports_integer(self) -> bool:
        """是否支持整数变量 / Whether integer variables are supported.

        Returns:
            支持整数变量时返回 True / True when integer
            variables are supported.
        """
        ...
