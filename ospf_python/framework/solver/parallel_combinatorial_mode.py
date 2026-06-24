"""并行组合模式 / Parallel combinatorial mode.

定义并行求解的组合模式枚举。
Defines the combinatorial mode enumeration for parallel solving.
"""

from __future__ import annotations

import enum


class ParallelCombinatorialMode(enum.Enum):
    """并行组合模式 / Parallel combinatorial mode.

    控制并行求解器的并行策略。
    Controls the parallelism strategy of parallel solvers.

    Attributes:
        value: 模式值 / The mode value.
    """

    FULL = 0
    """完全并行 / Fully parallel.

    所有子问题同时求解。
    All sub problems solved simultaneously.
    """

    PARTIAL = 1
    """部分并行 / Partially parallel.

    按批次并行求解子问题。
    Sub problems solved in parallel batches.
    """

    PIPELINE = 2
    """流水线并行 / Pipeline parallel.

    子问题按流水线方式执行。
    Sub problems executed in pipeline fashion.
    """
