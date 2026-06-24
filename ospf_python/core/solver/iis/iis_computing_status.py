"""IIS 计算状态枚举 / IIS computing status enumeration.

定义 IIS 计算过程中的状态。
Defines statuses during IIS computation.
"""

from __future__ import annotations

import enum


class IISComputingStatus(enum.Enum):
    """IIS 计算状态枚举 / IIS computing status enumeration.

    描述 IIS 计算完成后的状态。
    Describes the status after IIS computation.

    Attributes:
        value: 状态整数值 / The integer status value.
    """

    NOT_STARTED = 0
    """未开始 / Not started."""

    COMPUTING = 1
    """计算中 / Computing."""

    FOUND = 2
    """已找到 / IIS found."""

    NOT_FOUND = 3
    """未找到 / IIS not found."""

    TIMEOUT = 4
    """超时 / Time limit reached."""

    ERROR = 5
    """错误 / Error during computation."""
