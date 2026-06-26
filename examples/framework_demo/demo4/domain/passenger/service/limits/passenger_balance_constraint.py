"""Passenger weight balance constraint.

旅客重量平衡约束。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ZoneLoad:
    """Passenger load in a cabin zone.

    客舱区域的旅客载荷。
    """

    zone_id: str
    """Zone identifier (e.g. 'FWD', 'MID', 'AFT').

    区域标识符（如 'FWD'、'MID'、'AFT'）。
    """

    passenger_count: int
    """Number of passengers in this zone.

    此区域的旅客数量。
    """

    avg_weight_kg: float = 85.0
    """Average passenger weight in kg.

    旅客平均体重（公斤）。
    """

    @property
    def total_weight_kg(self) -> float:
        """Total passenger weight in this zone.

        此区域的旅客总重量。
        """
        return self.passenger_count * self.avg_weight_kg


class PassengerBalanceConstraint:
    """Enforces passenger weight distribution balance.

    执行旅客重量分布平衡。
    """

    def __init__(
        self,
        *,
        max_imbalance_pct: float = 10.0,
        avg_passenger_weight_kg: float = 85.0,
    ) -> None:
        """Initialize balance constraint.

        初始化平衡约束。

        Args:
            max_imbalance_pct: Max allowed imbalance
                percentage between zones.
            avg_passenger_weight_kg: Default average
                passenger weight.
        """
        self._max_imbalance = max_imbalance_pct
        self._avg_weight = avg_passenger_weight_kg

    def validate(
        self,
        zone_loads: Sequence[ZoneLoad],
    ) -> Sequence[str]:
        """Validate weight balance across zones.

        验证跨区域的重量平衡。

        Args:
            zone_loads: Load per cabin zone.

        Returns:
            Violation descriptions (empty if valid).
        """
        if len(zone_loads) < 2:
            return ()

        violations: list[str] = []
        weights = [z.total_weight_kg for z in zone_loads]
        total = sum(weights)

        if total == 0:
            return ()

        avg_per_zone = total / len(zone_loads)

        for zone in zone_loads:
            zone_weight = zone.total_weight_kg
            deviation = abs(zone_weight - avg_per_zone)
            pct = (deviation / avg_per_zone) * 100.0

            if pct > self._max_imbalance:
                violations.append(
                    f"Zone {zone.zone_id}: "
                    f"{pct:.1f}% imbalance > "
                    f"{self._max_imbalance}% limit"
                )

        return tuple(violations)

    def is_balanced(
        self,
        zone_loads: Sequence[ZoneLoad],
    ) -> bool:
        """Check if passenger distribution is balanced.

        检查旅客分布是否平衡。

        Args:
            zone_loads: Load per cabin zone.

        Returns:
            True if distribution is within limits.
        """
        return len(self.validate(zone_loads)) == 0

    def calculate_imbalance_pct(
        self,
        zone_loads: Sequence[ZoneLoad],
    ) -> float:
        """Calculate the maximum imbalance percentage.

        计算最大不平衡百分比。

        Args:
            zone_loads: Load per cabin zone.

        Returns:
            Maximum imbalance percentage.
        """
        if len(zone_loads) < 2:
            return 0.0

        weights = [z.total_weight_kg for z in zone_loads]
        total = sum(weights)
        if total == 0:
            return 0.0

        avg_per_zone = total / len(zone_loads)
        max_deviation = max(abs(w - avg_per_zone) for w in weights)
        return (max_deviation / avg_per_zone) * 100.0

    def suggest_rebalance(
        self,
        zone_loads: Sequence[ZoneLoad],
        *,
        target_zone: str,
    ) -> int:
        """Suggest number of passengers to move.

        建议需要移动的旅客数量。

        Args:
            zone_loads: Current zone loads.
            target_zone: Zone to rebalance.

        Returns:
            Suggested number of passengers to move
            (positive = move in, negative = move out).
        """
        if len(zone_loads) < 2:
            return 0

        total = sum(z.passenger_count for z in zone_loads)
        target = next(
            (z for z in zone_loads if z.zone_id == target_zone),
            None,
        )
        if target is None or total == 0:
            return 0

        ideal = total / len(zone_loads)
        return int(round(ideal - target.passenger_count))
