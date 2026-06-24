"""物料装箱求解器执行器 / Material packing solver executor.

执行物料装箱求解。
Executes material packing solving.
"""

from __future__ import annotations

import abc


class MaterialPackingSolverExecutor(abc.ABC):
    """物料装箱求解器执行器 / Material packing solver executor.

    定义物料装箱求解器的执行接口。
    Defines the execution interface for material packing solvers.
    """

    @abc.abstractmethod
    def prepare(self) -> None:
        """准备求解环境 / Prepare solving environment.

        初始化求解器和数据结构。
        Initializes solver and data structures.
        """
        ...

    @abc.abstractmethod
    def solve(self) -> bool:
        """执行求解 / Execute solving.

        Returns:
            求解成功返回 True / True if solving succeeded.
        """
        ...

    @abc.abstractmethod
    def get_solution(self) -> object:
        """获取方案 / Get solution.

        Returns:
            求解方案 / The solution.
        """
        ...
