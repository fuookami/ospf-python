"""基本量纲枚举。/ Fundamental quantity dimensions."""

from __future__ import annotations

from enum import Enum, unique


@unique
class FundamentalQuantity(Enum):
    """七个基本物理量纲。/ Seven fundamental physical quantities.

    对应 SI 国际单位制的七个基本量。
    Corresponds to the seven base quantities of the SI system.
    """

    MASS = "mass"
    LENGTH = "length"
    TIME = "time"
    CURRENT = "current"
    TEMPERATURE = "temperature"
    AMOUNT = "amount"
    LUMINOUS_INTENSITY = "luminous_intensity"
