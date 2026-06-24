"""内存清理策略枚举 / Memory cleanup policy enumeration.

定义中间模型的内存清理策略。
Defines memory cleanup policies for intermediate models.
"""

from __future__ import annotations

import enum


class MemoryCleanupPolicy(enum.Enum):
    """内存清理策略 / Memory cleanup policy.

    控制中间模型在转储后如何清理内存。
    Controls how intermediate models clean up memory
    after dumping.

    Attributes:
        value: 策略整数值 / The integer policy value.
    """

    NONE = 0
    """不清理 / No cleanup."""

    AFTER_DUMP = 1
    """转储后清理 / Cleanup after dump."""

    AGGRESSIVE = 2
    """积极清理 / Aggressive cleanup."""
