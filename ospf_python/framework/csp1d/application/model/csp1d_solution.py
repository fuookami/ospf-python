"""CSP1D 解决方案模型 / CSP1D solution model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.application.model.csp1d_assignment import (
        Csp1dAssignment,
    )


@dataclass(frozen=True)
class Csp1dSolution:
    """一维切割股问题解决方案 / 1D cutting stock problem solution.

    包含所有切割分配、总余料量和材料利用率。
    Contains all cutting assignments, total waste, and
    material utilization rate.

    Attributes:
        assignments: 切割分配元组 / Tuple of cutting assignments.
        total_waste: 总余料量 / Total waste produced.
        utilization: 材料利用率（0.0~1.0） / Material utilization
            rate (0.0~1.0).
    """

    assignments: tuple[Csp1dAssignment, ...]
    total_waste: float
    utilization: float
