"""Flight task model.

航班任务模型。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .task_priority import TaskPriority
from .task_status import TaskStatus


@dataclass(frozen=True)
class FlightTask:
    """A scheduled flight task with timing and aircraft information.

    包含时间和飞机信息的计划航班任务。
    """

    task_id: str
    """Unique identifier for the task.

    任务的唯一标识符。
    """

    flight_no: str
    """Flight number (e.g. 'CA1234').

    航班号（如 'CA1234'）。
    """

    origin: str
    """Departure airport IATA code.

    出发机场 IATA 代码。
    """

    destination: str
    """Arrival airport IATA code.

    到达机场 IATA 代码。
    """

    departure_time: datetime
    """Scheduled departure datetime.

    计划出发时间。
    """

    arrival_time: datetime
    """Scheduled arrival datetime.

    计划到达时间。
    """

    aircraft_type: str
    """Aircraft type code (e.g. 'A320', 'B737').

    飞机类型代码（如 'A320'、'B737'）。
    """

    status: TaskStatus = TaskStatus.SCHEDULED
    """Current task status, defaults to SCHEDULED.

    当前任务状态，默认为 SCHEDULED。
    """

    priority: TaskPriority = TaskPriority.NORMAL
    """Task priority level, defaults to NORMAL.

    任务优先级，默认为 NORMAL。
    """

    @property
    def duration_minutes(self) -> int:
        """Flight duration in minutes.

        飞行持续时间（分钟）。
        """
        delta = self.arrival_time - self.departure_time
        return int(delta.total_seconds() // 60)

    @property
    def is_long_haul(self) -> bool:
        """Whether this is a long-haul flight (>4 hours).

        是否为长途航班（超过 4 小时）。
        """
        return self.duration_minutes > 240

    @property
    def route_key(self) -> str:
        """Route identifier as 'origin-destination'.

        航线标识，格式为 'origin-destination'。
        """
        return f"{self.origin}-{self.destination}"
