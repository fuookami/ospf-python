"""Bunch compilation result model.

任务组编译结果模型 / Bunch compilation result model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bunch_status import BunchStatus

EFFICIENCY_THRESHOLD: float = 0.8


@dataclass(frozen=True)
class BunchResult:
    """Result of compiling or evaluating a single bunch.

    编译或评估单个任务组的结果。
    """

    bunch_id: str
    status: BunchStatus
    utilization: float

    @property
    def is_efficient(self) -> bool:
        """Whether the bunch meets the efficiency threshold.

        任务组是否达到效率阈值。
        """
        return self.utilization >= EFFICIENCY_THRESHOLD

    @property
    def utilization_pct(self) -> str:
        """Utilization as a formatted percentage string.

        利用率的百分比格式字符串。
        """
        return f"{self.utilization * 100:.1f}%"

    def is_better_than(self, other: BunchResult) -> bool:
        """Compare this result against another by utilization.

        按利用率与此结果与另一个进行比较。
        """
        if self.status.is_terminal and not other.status.is_terminal:
            return False
        if not self.status.is_terminal and other.status.is_terminal:
            return True
        return self.utilization > other.utilization
