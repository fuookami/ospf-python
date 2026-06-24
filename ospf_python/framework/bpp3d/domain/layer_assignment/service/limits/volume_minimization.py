"""体积最小化 / Volume minimization.

最小化使用的总体积。
Minimizes the total volume used.
"""

from __future__ import annotations

import abc


class VolumeMinimization(abc.ABC):
    """体积最小化 / Volume minimization.

    通过优化减少使用的容器总体积。
    Reduces total container volume used through optimization.
    """

    @abc.abstractmethod
    def calculate_volume(
        self,
        solution: object,
    ) -> float:
        """计算体积 / Calculate volume.

        Args:
            solution: 装箱方案 / The packing solution.

        Returns:
            总体积 / The total volume.
        """
        ...

    @abc.abstractmethod
    def get_objective_coefficient(self) -> float:
        """获取目标系数 / Get objective coefficient.

        Returns:
            目标函数系数 / The objective function coefficient.
        """
        ...
