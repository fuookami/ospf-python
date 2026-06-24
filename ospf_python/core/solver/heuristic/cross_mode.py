"""交叉模式枚举 / Crossover mode enumeration.

定义种群交叉的策略模式。
Defines strategy modes for population crossover.
"""

from __future__ import annotations

import enum


class CrossMode(enum.Enum):
    """交叉模式枚举 / Crossover mode enumeration.

    描述对个体进行交叉操作的策略。
    Describes strategies for crossing individuals.

    Attributes:
        value: 模式整数值 / The integer mode value.
    """

    SINGLE_POINT = 0
    """单点交叉 / Single-point crossover."""

    TWO_POINT = 1
    """两点交叉 / Two-point crossover."""

    UNIFORM = 2
    """均匀交叉 / Uniform crossover."""

    ARITHMETIC = 3
    """算术交叉 / Arithmetic crossover."""
