"""批量调度策略枚举 / Batch dispatch policy enumeration.

定义中间模型的批量调度策略。
Defines batch dispatch policies for intermediate models.
"""

from __future__ import annotations

import enum


class BatchDispatchPolicy(enum.Enum):
    """批量调度策略 / Batch dispatch policy.

    控制中间模型在导出时如何分批处理数据。
    Controls how intermediate models batch-process data
    during export.

    Attributes:
        value: 策略整数值 / The integer policy value.
    """

    ALL = 0
    """一次性全部处理 / Process all at once."""

    CHUNKED = 1
    """分块处理 / Process in chunks."""

    STREAMING = 2
    """流式处理 / Process in streaming fashion."""
