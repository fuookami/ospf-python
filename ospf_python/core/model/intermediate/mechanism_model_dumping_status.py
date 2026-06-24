"""机制模型转储状态枚举 / Mechanism model dumping status.

定义机制模型转储过程的状态。
Defines the status of mechanism model dumping processes.
"""

from __future__ import annotations

import enum


class MechanismModelDumpingStatus(enum.Enum):
    """机制模型转储状态 / Mechanism model dumping status.

    表示机制模型导出操作的当前状态。
    Represents the current status of a mechanism model
    export operation.

    Attributes:
        value: 状态整数值 / The integer status value.
    """

    SUCCESS = 0
    """转储成功 / Dump succeeded."""

    FAILED = 1
    """转储失败 / Dump failed."""

    SKIPPED = 2
    """已跳过 / Skipped."""
