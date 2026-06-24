"""交叉操作 / Crossover operation.

实现对个体的交叉策略。
Implements crossover strategies for individuals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.core.solver.heuristic.cross_mode import (
    CrossMode,
)

if TYPE_CHECKING:
    from ospf_python.core.solver.value.solve_value import (
        SolveValue,
    )


@dataclass
class Cross:
    """交叉操作 / Crossover operation.

    根据指定的交叉模式对两个个体进行交叉。
    Crosses two individuals according to the specified
    crossover mode.

    Attributes:
        mode: 交叉模式 / Crossover mode.
        rate: 交叉概率 / Crossover rate.
    """

    mode: CrossMode = CrossMode.SINGLE_POINT
    """交叉模式 / Crossover mode."""

    rate: float = 0.8
    """交叉概率 / Crossover rate."""

    def cross(
        self,
        parent_a: SolveValue,
        parent_b: SolveValue,
    ) -> tuple[SolveValue, SolveValue]:
        """对两个个体执行交叉 / Cross two individuals.

        Args:
            parent_a: 父代 A / Parent A.
            parent_b: 父代 B / Parent B.

        Returns:
            两个子代个体 / Two offspring individuals.
        """
        return parent_a, parent_b
