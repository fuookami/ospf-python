"""尾箱装载率最小化 / Tail bin loading rate minimization.

最小化尾箱的低装载率。
Minimizes low loading rate of tail bins.
"""

from __future__ import annotations

import abc


class TailBinLoadingRateMinimization(abc.ABC):
    """尾箱装载率最小化 / Tail bin loading rate minimization.

    通过优化提高尾箱装载率。
    Improves tail bin loading rate through optimization.
    """

    @abc.abstractmethod
    def calculate_penalty(
        self,
        loading_rate: float,
    ) -> float:
        """计算惩罚值 / Calculate penalty.

        Args:
            loading_rate: 装载率 / The loading rate.

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
