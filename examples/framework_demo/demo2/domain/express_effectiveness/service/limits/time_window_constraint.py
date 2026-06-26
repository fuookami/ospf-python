"""配送时间窗约束。

Time window constraint enforcing delivery deadlines.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeWindowShipment:
    """时间窗快件信息。

    Shipment with delivery time window requirements.

    Attributes:
        shipment_id: 快件标识 / Shipment identifier
        earliest_delivery: 最早配送时间（小时偏移）/ Earliest delivery time (hour offset)
        latest_delivery: 最晚配送时间（小时偏移）/ Latest delivery time (hour offset)
        estimated_time: 预计配送时间（小时偏移）/ Estimated delivery time (hour offset)
    """

    shipment_id: str
    earliest_delivery: float
    latest_delivery: float
    estimated_time: float


@dataclass(frozen=True)
class TimeWindowConstraint:
    """配送时间窗约束。

    Enforces that all shipments are delivered within their specified
    time windows. Checks both early and late delivery violations.

    Attributes:
        early_buffer: 提前缓冲时间（小时）/ Early delivery buffer (hours)
        late_tolerance: 延迟容忍时间（小时）/ Late delivery tolerance (hours)
    """

    early_buffer: float
    late_tolerance: float

    def evaluate(
        self,
        shipments: tuple[TimeWindowShipment, ...],
    ) -> tuple[bool, list[str]]:
        """评估时间窗约束。

        Checks that all shipments meet their delivery time windows.

        Args:
            shipments: 所有快件 / All shipments

        Returns:
            tuple: (是否全部满足, 违规描述) / (all satisfied, violations)
        """
        violations: list[str] = []
        for s in shipments:
            effective_earliest = s.earliest_delivery - self.early_buffer
            effective_latest = s.latest_delivery + self.late_tolerance

            if s.estimated_time < effective_earliest:
                violations.append(
                    f"快件 {s.shipment_id} 预计送达时间 "
                    f"{s.estimated_time:.1f}h 早于窗口 "
                    f"[{s.earliest_delivery:.1f}h]"
                )
            elif s.estimated_time > effective_latest:
                violations.append(
                    f"快件 {s.shipment_id} 预计送达时间 "
                    f"{s.estimated_time:.1f}h 晚于窗口 "
                    f"[{s.latest_delivery:.1f}h]"
                )

        return (len(violations) == 0, violations)

    def on_time_rate(
        self,
        shipments: tuple[TimeWindowShipment, ...],
    ) -> float:
        """计算准时送达率。

        Args:
            shipments: 所有快件 / All shipments

        Returns:
            float: 准时率 / On-time delivery rate
        """
        if not shipments:
            return 1.0
        on_time = sum(
            1
            for s in shipments
            if s.earliest_delivery <= s.estimated_time <= s.latest_delivery
        )
        return on_time / len(shipments)

    def worst_violations(
        self,
        shipments: tuple[TimeWindowShipment, ...],
        top_n: int = 5,
    ) -> tuple[TimeWindowShipment, ...]:
        """获取延迟最严重的快件。

        Args:
            shipments: 所有快件 / All shipments
            top_n: 返回数量 / Number of results

        Returns:
            tuple: 延迟最严重的快件 / Most delayed shipments
        """

        def delay(s: TimeWindowShipment) -> float:
            return max(s.estimated_time - s.latest_delivery, 0.0)

        return tuple(
            sorted(
                [s for s in shipments if delay(s) > 0],
                key=delay,
                reverse=True,
            )[:top_n]
        )
