"""Connecting flight model.

中转航班模型。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class ConnectingFlight:
    """A connecting flight pairing with layover time.

    包含中转时间的中转航班配对。
    """

    from_flight: str
    """Arriving flight number.

    到达航班号。
    """

    to_flight: str
    """Departing flight number.

    出发航班号。
    """

    layover_time: timedelta
    """Time between flights.

    航班间隔时间。
    """

    @property
    def layover_minutes(self) -> int:
        """Layover duration in minutes.

        中转持续时间（分钟）。
        """
        return int(self.layover_time.total_seconds() // 60)

    @property
    def layover_hours(self) -> float:
        """Layover duration in hours.

        中转持续时间（小时）。
        """
        return self.layover_time.total_seconds() / 3600.0

    @property
    def is_minimum_connection(self) -> bool:
        """Whether layover meets minimum 45-min connection.

        中转是否满足最低 45 分钟连接时间。
        """
        return self.layover_minutes >= 45

    @property
    def is_long_layover(self) -> bool:
        """Whether layover exceeds 4 hours.

        中转是否超过 4 小时。
        """
        return self.layover_hours > 4.0

    @property
    def is_same_day(self) -> bool:
        """Whether connection is within same calendar day.

        连接是否在同一日历日内。
        """
        return self.layover_hours < 24.0

    @property
    def connection_key(self) -> str:
        """Unique key for this connection pair.

        此连接对的唯一键。
        """
        return f"{self.from_flight}->{self.to_flight}"
