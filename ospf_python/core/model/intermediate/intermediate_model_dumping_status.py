"""中间模型转储状态枚举 / Intermediate model dumping status.

定义中间模型转储过程的状态。
Defines the status of intermediate model dumping processes.
"""

from __future__ import annotations

import enum


class IntermediateModelDumpingStatus(enum.Enum):
    """中间模型转储状态 / Intermediate model dumping status.

    表示中间模型导出操作的当前状态。
    Represents the current status of an intermediate model
    export operation.

    Attributes:
        value: 状态整数值 / The integer status value.
    """

    SUCCESS = 0
    """转储成功 / Dump succeeded."""

    FAILED = 1
    """转储失败 / Dump failed."""

    PARTIAL = 2
    """部分完成 / Partially completed."""

    CANCELLED = 3
    """已取消 / Cancelled."""
