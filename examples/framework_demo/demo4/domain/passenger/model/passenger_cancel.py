"""Passenger cancellation model.

旅客取消模型。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


@unique
class CancelReason(Enum):
    """Reasons for passenger cancellation.

    旅客取消原因。
    """

    PASSENGER_REQUEST = "PASSENGER_REQUEST"
    """Cancelled by passenger request.

    旅客主动取消。
    """

    FLIGHT_CANCELLED = "FLIGHT_CANCELLED"
    """Flight was cancelled by airline.

    航班被航空公司取消。
    """

    OVERBOOKING = "OVERBOOKING"
    """Removed due to overbooking.

    因超售被移除。
    """

    CONNECTION_MISSED = "CONNECTION_MISSED"
    """Missed connecting flight.

    错过中转航班。
    """

    WEATHER = "WEATHER"
    """Cancelled due to weather conditions.

    因天气条件取消。
    """


@dataclass(frozen=True)
class PassengerCancel:
    """Record of a passenger cancellation.

    旅客取消记录。
    """

    passenger_id: str
    """ID of the cancelled passenger.

    被取消旅客的 ID。
    """

    reason: CancelReason
    """Cancellation reason.

    取消原因。
    """

    refund_amount: float = 0.0
    """Refund amount in local currency.

    退款金额（当地货币）。
    """

    @property
    def is_airline_fault(self) -> bool:
        """Whether cancellation is airline's fault.

        取消是否为航空公司责任。
        """
        return self.reason in (
            CancelReason.FLIGHT_CANCELLED,
            CancelReason.OVERBOOKING,
        )

    @property
    def is_full_refund(self) -> bool:
        """Whether passenger receives a full refund.

        旅客是否获得全额退款。
        """
        return self.is_airline_fault

    @property
    def has_refund(self) -> bool:
        """Whether any refund is issued.

        是否发放了退款。
        """
        return self.refund_amount > 0.0
