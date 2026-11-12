"""固定 Rust revision 的任务列生成公共门面 / Public pinned-revision task column-generation facade."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ospf_python._binding.gantt_task import (
    TaskPricingAlgorithm as _NativeTaskPricingAlgorithm,
)
from ospf_python._binding.gantt_task import (
    TaskPricingBatch,
    TaskPricingLpReport,
)

type TaskPricingColumn = tuple[int, int, float]
"""任务、执行器与完整列成本 / Task, executor and complete column cost."""
type TaskPricingPolicy = Callable[[dict[str, Any]], dict[str, Any]]
"""接收认证定价请求并返回共享批次 / Receive a certified request and return a shared batch."""


@dataclass(frozen=True, kw_only=True)
class TaskPricingResult:
    """一次显式无时隙任务定价的结果快照 / Result snapshot of one explicit unslotted task-pricing run."""

    task_keys: tuple[str, ...]
    resource_keys: tuple[str, ...]
    lp_report: TaskPricingLpReport
    batch: TaskPricingBatch
    certified_lower_bound: float | None


class TaskColumnGenerationAlgorithm(_NativeTaskPricingAlgorithm):
    """固定 revision 的任务列生成算法 / Pinned-revision task column-generation algorithm.

    公共门面直接继承私有 PyO3 适配器，不复制上游算法或主问题状态。
    The public facade subclasses the private PyO3 adapter without copying the
    upstream algorithm or master-problem state.

    Attributes:
        _handle: 上游算法句柄，由私有基类持有 / Upstream algorithm handle owned by the private base.
    """


__all__ = [
    "TaskColumnGenerationAlgorithm",
    "TaskPricingBatch",
    "TaskPricingColumn",
    "TaskPricingLpReport",
    "TaskPricingPolicy",
    "TaskPricingResult",
]
