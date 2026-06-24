"""运行心跳 / Running heartbeat.

记录框架运行时的心跳时间戳。
Records heartbeat timestamps during framework runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RunningHeartBeat:
    """运行心跳 / Running heartbeat.

    用于跟踪框架组件的活跃状态，包含最近一次
    心跳的时间戳。
    Used to track the liveness of framework components,
    containing the timestamp of the most recent heartbeat.

    Attributes:
        timestamp: 心跳时间戳 / The heartbeat timestamp.
    """

    timestamp: datetime
