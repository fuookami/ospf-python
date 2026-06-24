"""浮点数幂运算策略。

Floating-point power strategy.
"""

from __future__ import annotations

import enum


class FltXPowerStrategy(enum.Enum):
    """浮点数幂运算策略枚举。

    Floating-point power strategy enumeration.

    Attributes:
        FAST: 快速模式，使用内置运算符。/
            Fast mode using built-in operator.
        PRECISE: 精确模式，使用 math.pow。/
            Precise mode using math.pow.
    """

    FAST = "fast"
    PRECISE = "precise"
