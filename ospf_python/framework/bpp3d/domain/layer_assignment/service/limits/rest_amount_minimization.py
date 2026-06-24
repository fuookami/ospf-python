"""剩余量最小化 / Rest amount minimization.

最小化未满足的物品需求量。
Minimizes unmet item demand quantities.
"""

from __future__ import annotations

import abc


class RestAmountMinimization(abc.ABC):
    """剩余量最小化 / Rest amount minimization.

    通过优化减少未满足的需求量。
    Reduces unmet demand through optimization.
    """

    @abc.abstractmethod
    def calculate_penalty(
        self,
        rest_amount: int,
    ) -> float:
        """计算惩罚值 / Calculate penalty.

        Args:
            rest_amount: 剩余量 / The rest amount.

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
