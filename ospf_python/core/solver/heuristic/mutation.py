"""变异操作 / Mutation operation.

实现对个体的变异策略。
Implements mutation strategies for individuals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.core.solver.heuristic.mutation_mode import (
    MutationMode,
)

if TYPE_CHECKING:
    from ospf_python.core.solver.value.solve_value import (
        SolveValue,
    )


@dataclass
class Mutation:
    """变异操作 / Mutation operation.

    根据指定的变异模式对个体进行变异。
    Mutates individuals according to the specified
    mutation mode.

    Attributes:
        mode: 变异模式 / Mutation mode.
        rate: 变异概率 / Mutation rate.
        strength: 变异强度 / Mutation strength.
    """

    mode: MutationMode = MutationMode.UNIFORM
    """变异模式 / Mutation mode."""

    rate: float = 0.1
    """变异概率 / Mutation rate."""

    strength: float = 0.1
    """变异强度 / Mutation strength."""

    def mutate(
        self,
        individual: SolveValue,
    ) -> SolveValue:
        """对个体执行变异 / Mutate an individual.

        Args:
            individual: 待变异个体 / Individual to mutate.

        Returns:
            变异后的新个体 / New mutated individual.
        """
        return individual
