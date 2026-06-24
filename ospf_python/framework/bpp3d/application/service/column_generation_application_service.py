"""列生成应用服务 / Column generation application service.

协调列生成算法的执行流程。
Coordinates the execution flow of column generation algorithms.
"""

from __future__ import annotations

import abc


class ColumnGenerationApplicationService(abc.ABC):
    """列生成应用服务 / Column generation application service.

    提供列生成算法的高层执行接口。
    Provides a high-level execution interface for column
    generation algorithms.
    """

    @abc.abstractmethod
    def execute(self) -> bool:
        """执行列生成算法 / Execute column generation algorithm.

        运行完整的列生成迭代流程。
        Runs the complete column generation iteration loop.

        Returns:
            执行成功返回 True / True if execution succeeded.
        """
        ...

    @abc.abstractmethod
    def get_solution(self) -> object:
        """获取求解结果 / Get solution result.

        Returns:
            当前最优解 / The current best solution.
        """
        ...
