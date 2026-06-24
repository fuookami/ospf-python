"""箱数量最小化 / Bin amount minimization.

最小化使用的容器数量。
Minimizes the number of containers used.
"""

from __future__ import annotations

import abc


class BinAmountMinimization(abc.ABC):
    """箱数量最小化 / Bin amount minimization.

    通过优化层分配减少容器使用量。
    Reduces container usage by optimizing layer assignment.
    """

    @abc.abstractmethod
    def calculate_penalty(
        self,
        bin_count: int,
        target_count: int,
    ) -> float:
        """计算惩罚值 / Calculate penalty.

        Args:
            bin_count: 当前箱数 / Current bin count.
            target_count: 目标箱数 / Target bin count.

        Returns:
            惩罚值 / The penalty value.
        """
        ...

    @abc.abstractmethod
    def get_objective_coefficient(self) -> float:
        """获取目标系数 / Get objective coefficient.

        Returns:
            目标函数系数 / The objective function coefficient.
        """
        ...
