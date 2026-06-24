"""穷举物料装箱求解器执行器 / Exhaustive material packing solver executor.

使用穷举法求解物料装箱问题。
Solves material packing problems using exhaustive search.
"""

from __future__ import annotations

import abc


class ExhaustiveMaterialPackingSolverExecutor(abc.ABC):
    """穷举物料装箱求解器执行器 / Exhaustive material packing solver executor.

    遍历所有可能的装箱组合。
    Iterates through all possible packing combinations.
    """

    @abc.abstractmethod
    def execute(
        self,
        materials: tuple[object, ...],
        container: object,
    ) -> object:
        """执行穷举求解 / Execute exhaustive solving.

        Args:
            materials: 物料列表 / The material list.
            container: 目标容器 / The target container.

        Returns:
            最优装箱方案 / The optimal packing solution.
        """
        ...

    @abc.abstractmethod
    def get_best_solution(self) -> object | None:
        """获取最优方案 / Get best solution.

        Returns:
            当前最优方案或 None / Current best solution or None.
        """
        ...
