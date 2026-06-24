"""变异模式枚举 / Mutation mode enumeration.

定义种群变异的策略模式。
Defines strategy modes for population mutation.
"""

from __future__ import annotations

import enum


class MutationMode(enum.Enum):
    """变异模式枚举 / Mutation mode enumeration.

    描述对个体进行变异操作的策略。
    Describes strategies for mutating individuals.

    Attributes:
        value: 模式整数值 / The integer mode value.
    """

    UNIFORM = 0
    """均匀变异 / Uniform mutation."""

    GAUSSIAN = 1
    """高斯变异 / Gaussian mutation."""

    POLYNOMIAL = 2
    """多项式变异 / Polynomial mutation."""
