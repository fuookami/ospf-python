"""求解器内存清理支持 / Solver memory cleanup support.

提供求解器资源释放和内存清理功能。
Provides solver resource release and memory cleanup
functionality.
"""

from __future__ import annotations

import abc


class SolverMemoryCleanupSupport(abc.ABC):
    """求解器内存清理支持 / Solver memory cleanup support.

    所有需要显式释放资源的求解器应实现此接口。
    All solvers requiring explicit resource release
    should implement this interface.
    """

    @abc.abstractmethod
    def cleanup(self) -> None:
        """清理求解器资源 / Clean up solver resources.

        释放求解器持有的内存和外部资源。
        Releases memory and external resources held by
        the solver.
        """
        ...

    @abc.abstractmethod
    def is_cleaned_up(self) -> bool:
        """检查是否已清理 / Check whether already cleaned up.

        Returns:
            已清理返回 True / True when already cleaned up.
        """
        ...
