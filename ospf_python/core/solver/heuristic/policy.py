"""启发式策略 / Heuristic policy.

封装启发式算法的全局策略参数。
Encapsulates global strategy parameters for heuristic
algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.core.solver.heuristic.cross import Cross
from ospf_python.core.solver.heuristic.iteration import (
    Iteration,
)
from ospf_python.core.solver.heuristic.migration import (
    Migration,
)
from ospf_python.core.solver.heuristic.mutation import (
    Mutation,
)
from ospf_python.core.solver.heuristic.normalization import (
    Normalization,
)
from ospf_python.core.solver.heuristic.selection import (
    Selection,
)


@dataclass
class Policy:
    """启发式策略 / Heuristic policy.

    聚合选择、变异、交叉、迁移、迭代和归一化策略。
    Aggregates selection, mutation, crossover, migration,
    iteration, and normalization policies.

    Attributes:
        selection: 选择策略 / Selection policy.
        mutation: 变异策略 / Mutation policy.
        cross: 交叉策略 / Crossover policy.
        migration: 迁移策略 / Migration policy.
        iteration: 迭代控制 / Iteration control.
        normalization: 归一化 / Normalization.
        population_size: 种群大小 / Population size.
    """

    selection: Selection = field(
        default_factory=Selection,
    )
    """选择策略 / Selection policy."""

    mutation: Mutation = field(
        default_factory=Mutation,
    )
    """变异策略 / Mutation policy."""

    cross: Cross = field(default_factory=Cross)
    """交叉策略 / Crossover policy."""

    migration: Migration = field(
        default_factory=Migration,
    )
    """迁移策略 / Migration policy."""

    iteration: Iteration = field(
        default_factory=Iteration,
    )
    """迭代控制 / Iteration control."""

    normalization: Normalization = field(
        default_factory=Normalization,
    )
    """归一化 / Normalization."""

    population_size: int = 50
    """种群大小 / Population size."""
