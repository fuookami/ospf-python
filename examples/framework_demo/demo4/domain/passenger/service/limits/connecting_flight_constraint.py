"""Connecting flight constraint.

中转航班约束。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ...model.connecting_flight import ConnectingFlight


class ConnectingFlightConstraint:
    """Enforces minimum connection time requirements.

    执行最低中转时间要求。
    """

    def __init__(
        self,
        *,
        min_connection_minutes: int = 45,
        max_layover_hours: float = 24.0,
        min_international_minutes: int = 90,
    ) -> None:
        """Initialize connecting flight constraint.

        初始化中转航班约束。

        Args:
            min_connection_minutes: Min domestic
                connection time in minutes.
            max_layover_hours: Max allowed layover.
            min_international_minutes: Min international
                connection time.
        """
        self._min_domestic = min_connection_minutes
        self._max_layover = max_layover_hours
        self._min_international = min_international_minutes

    def validate(
        self,
        connections: Sequence[ConnectingFlight],
    ) -> Sequence[str]:
        """Validate connecting flights meet requirements.

        验证中转航班满足要求。

        Args:
            connections: Connecting flights to validate.

        Returns:
            Violation descriptions (empty if valid).
        """
        violations: list[str] = []

        for conn in connections:
            if conn.layover_minutes < self._min_domestic:
                violations.append(
                    f"{conn.connection_key}: layover "
                    f"{conn.layover_minutes}min < "
                    f"{self._min_domestic}min minimum"
                )

            if conn.layover_hours > self._max_layover:
                violations.append(
                    f"{conn.connection_key}: layover "
                    f"{conn.layover_hours:.1f}h > "
                    f"{self._max_layover}h maximum"
                )

        return tuple(violations)

    def is_valid(
        self,
        connections: Sequence[ConnectingFlight],
    ) -> bool:
        """Check if all connections meet requirements.

        检查所有连接是否满足要求。

        Args:
            connections: Connecting flights to check.

        Returns:
            True if all connections are valid.
        """
        return len(self.validate(connections)) == 0

    def filter_valid_connections(
        self,
        connections: Sequence[ConnectingFlight],
    ) -> Sequence[ConnectingFlight]:
        """Return only connections that meet requirements.

        返回仅满足要求的连接。

        Args:
            connections: Connections to filter.

        Returns:
            Valid connecting flights.
        """
        return tuple(
            c
            for c in connections
            if c.is_minimum_connection and c.layover_hours <= self._max_layover
        )
