"""迭代控制 / Iteration control.

管理启发式算法的迭代过程。
Manages the iteration process of heuristic algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Iteration:
    """迭代控制 / Iteration control.

    记录和控制启发式算法的迭代状态。
    Records and controls the iteration state of a
    heuristic algorithm.

    Attributes:
        max_iterations: 最大迭代次数 / Maximum iterations.
        current: 当前迭代 / Current iteration.
        improvement_threshold: 改进阈值 /
            Improvement threshold.
    """

    max_iterations: int = 100
    """最大迭代次数 / Maximum iterations."""

    current: int = 0
    """当前迭代 / Current iteration."""

    improvement_threshold: float = 1e-6
    """改进阈值 / Improvement threshold."""

    @property
    def is_finished(self) -> bool:
        """是否已完成 / Whether finished.

        Returns:
            达到最大迭代次数返回 True / True when max
            iterations reached.
        """
        return self.current >= self.max_iterations

    def advance(self) -> None:
        """推进迭代 / Advance iteration."""
        self.current += 1

    def reset(self) -> None:
        """重置迭代 / Reset iteration."""
        self.current = 0
