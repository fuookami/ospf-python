"""求解器状态支持 / Solver status support.

提供求解器状态查询和转换功能。
Provides solver status querying and transition
functionality.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.solver.output.solver_status import (
        SolverStatus,
    )


class SolverStatusSupport(abc.ABC):
    """求解器状态支持 / Solver status support.

    所有需要状态查询的求解器应实现此接口。
    All solvers requiring status queries should implement
    this interface.
    """

    @abc.abstractmethod
    def get_status(self) -> SolverStatus:
        """获取当前求解状态 / Get current solve status.

        Returns:
            求解器状态 / The solver status.
        """
        ...

    @abc.abstractmethod
    def is_terminated(self) -> bool:
        """检查是否已终止 / Check whether terminated.

        Returns:
            已终止返回 True / True when terminated.
        """
        ...

    @abc.abstractmethod
    def is_feasible(self) -> bool:
        """检查当前解是否可行 / Check whether current
        solution is feasible.

        Returns:
            可行返回 True / True when feasible.
        """
        ...
