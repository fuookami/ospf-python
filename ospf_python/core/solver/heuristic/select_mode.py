"""选择模式枚举 / Selection mode enumeration.

定义种群选择的策略模式。
Defines strategy modes for population selection.
"""

from __future__ import annotations

import enum


class SelectMode(enum.Enum):
    """选择模式枚举 / Selection mode enumeration.

    描述从种群中选择个体的策略。
    Describes strategies for selecting individuals
    from a population.

    Attributes:
        value: 模式整数值 / The integer mode value.
    """

    ROULETTE = 0
    """轮盘赌选择 / Roulette wheel selection."""

    TOURNAMENT = 1
    """锦标赛选择 / Tournament selection."""

    RANK = 2
    """排名选择 / Rank-based selection."""
