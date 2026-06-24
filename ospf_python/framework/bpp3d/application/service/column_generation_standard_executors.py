"""列生成标准执行器 / Column generation standard executors.

提供列生成算法的标准执行器实现。
Provides standard executor implementations for column
generation algorithms.
"""

from __future__ import annotations

import abc


class ColumnGenerationStandardExecutor(abc.ABC):
    """列生成标准执行器 / Column generation standard executor.

    定义标准列生成执行器的接口。
    Defines the interface for standard column generation executors.
    """

    @abc.abstractmethod
    def prepare(self) -> None:
        """准备执行环境 / Prepare execution environment.

        初始化求解器和数据结构。
        Initializes solver and data structures.
        """
        ...

    @abc.abstractmethod
    def run_iteration(self) -> bool:
        """运行一次迭代 / Run one iteration.

        执行一次列生成主循环。
        Executes one column generation main loop iteration.

        Returns:
            继续迭代返回 True / True to continue iterating.
        """
        ...

    @abc.abstractmethod
    def finalize(self) -> object:
        """完成求解 / Finalize solving.

        Returns:
            最终求解结果 / The final solution result.
        """
        ...
