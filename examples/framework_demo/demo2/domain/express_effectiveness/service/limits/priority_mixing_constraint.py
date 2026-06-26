"""优先级混装约束。

Priority mixing constraint enforcing segregation of delivery speeds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...model.express_priority import ExpressPriority


@dataclass(frozen=True)
class PriorityMixingShipment:
    """混装快件信息。

    Shipment with priority and assigned batch.

    Attributes:
        shipment_id: 快件标识 / Shipment identifier
        priority: 配送优先级 / Delivery priority
        batch_id: 分拣批次 / Sorting batch identifier
    """

    shipment_id: str
    priority: ExpressPriority
    batch_id: str


@dataclass(frozen=True)
class PriorityMixingConstraint:
    """优先级混装约束。

    Enforces that shipments of different priority levels are not mixed
    in the same sorting batch. Same-day and next-day shipments must
    be processed in dedicated batches.

    Attributes:
        allowed_mixing: 允许混装的优先级对 / Priority pairs allowed to mix
    """

    allowed_mixing: frozenset[tuple[ExpressPriority, ExpressPriority]]

    def evaluate(
        self,
        shipments: tuple[PriorityMixingShipment, ...],
    ) -> tuple[bool, list[str]]:
        """评估优先级混装约束。

        Checks that no batch contains incompatible priority levels.

        Args:
            shipments: 所有快件 / All shipments

        Returns:
            tuple: (是否满足, 违规描述) / (satisfied, violations)
        """
        violations: list[str] = []
        by_batch: dict[str, list[PriorityMixingShipment]] = {}
        for s in shipments:
            by_batch.setdefault(s.batch_id, []).append(s)

        for batch_id, batch_shipments in by_batch.items():
            priorities = {s.priority for s in batch_shipments}
            priority_list = sorted(priorities, key=lambda p: p.value)

            for i in range(len(priority_list)):
                for j in range(i + 1, len(priority_list)):
                    a, b = priority_list[i], priority_list[j]
                    pair_ab = (a, b)
                    pair_ba = (b, a)
                    if (
                        pair_ab not in self.allowed_mixing
                        and pair_ba not in self.allowed_mixing
                    ):
                        count_a = sum(1 for s in batch_shipments if s.priority == a)
                        count_b = sum(1 for s in batch_shipments if s.priority == b)
                        violations.append(
                            f"批次 {batch_id} 混装了 "
                            f"{a.label_zh()}({count_a}件) 和 "
                            f"{b.label_zh()}({count_b}件)"
                        )

        return (len(violations) == 0, violations)

    def suggested_batches(
        self,
        shipments: tuple[PriorityMixingShipment, ...],
    ) -> dict[str, tuple[str, ...]]:
        """建议按优先级分批。

        Args:
            shipments: 所有快件 / All shipments

        Returns:
            dict: 按优先级分批的快件ID / Shipment IDs grouped by priority
        """
        by_priority: dict[str, list[str]] = {}
        for s in shipments:
            key = s.priority.label_zh()
            by_priority.setdefault(key, []).append(s.shipment_id)
        return {k: tuple(v) for k, v in by_priority.items()}
