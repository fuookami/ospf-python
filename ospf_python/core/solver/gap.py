"""求解间隙 / Solve gap.

封装求解器的绝对间隙和相对间隙。
Encapsulates solver absolute and relative gaps.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Gap:
    """求解间隙 / Solve gap.

    冻结数据类，记录最优解的绝对间隙和相对间隙。
    Frozen dataclass recording the absolute and relative
    gap from the optimal solution.

    Attributes:
        absolute: 绝对间隙 / Absolute gap.
        relative: 相对间隙 / Relative gap.
    """

    absolute: float = float("inf")
    """绝对间隙 / Absolute gap."""

    relative: float = float("inf")
    """相对间隙 / Relative gap."""

    @staticmethod
    def zero() -> Gap:
        """创建零间隙（已最优）/ Create zero gap (optimal).

        Returns:
            零间隙实例 / Zero gap instance.
        """
        return Gap(absolute=0.0, relative=0.0)

    @staticmethod
    def infinity() -> Gap:
        """创建无穷大间隙 / Create infinity gap.

        Returns:
            无穷大间隙实例 / Infinity gap instance.
        """
        return Gap(
            absolute=float("inf"),
            relative=float("inf"),
        )

    def is_within_tolerance(
        self,
        tolerance: float,
    ) -> bool:
        """相对间隙是否在容差内 / Whether relative gap
        is within tolerance.

        Args:
            tolerance: 容差值 / Tolerance value.

        Returns:
            在容差内返回 True / True if within tolerance.
        """
        return self.relative <= tolerance
