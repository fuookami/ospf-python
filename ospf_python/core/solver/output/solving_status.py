"""求解过程状态枚举 / Solving process status enumeration.

定义求解过程中的中间状态。
Defines intermediate statuses during the solving process.
"""

from __future__ import annotations

import enum


class SolvingStatus(enum.Enum):
    """求解过程状态枚举 / Solving process status enumeration.

    描述求解过程中各阶段的状态。
    Describes the status at each stage of the solving
    process.

    Attributes:
        value: 状态整数值 / The integer status value.
    """

    IDLE = 0
    """空闲 / Idle, not started."""

    PREPROCESSING = 1
    """预处理 / Preprocessing in progress."""

    SOLVING = 2
    """求解中 / Solving in progress."""

    POSTPROCESSING = 3
    """后处理 / Postprocessing in progress."""

    COMPLETED = 4
    """已完成 / Completed."""

    CANCELLED = 5
    """已取消 / Cancelled."""
