"""Task result model.

任务结果模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .task_status import TaskStatus


@dataclass(frozen=True)
class TaskResult:
    """Result of executing a flight task.

    执行航班任务的结果。
    """

    task_id: str
    """ID of the completed task.

    已完成任务的 ID。
    """

    status: TaskStatus
    """Final status of the task.

    任务的最终状态。
    """

    metrics: dict[str, float] = field(default_factory=dict)
    """Performance metrics collected during execution.

    执行期间收集的性能指标。
    """

    @property
    def is_success(self) -> bool:
        """Whether the task completed successfully.

        任务是否成功完成。
        """
        return self.status == TaskStatus.COMPLETED

    @property
    def on_time_performance(self) -> float:
        """On-time performance score (0.0 to 1.0).

        准时绩效得分（0.0 到 1.0）。
        """
        return self.metrics.get("otp_score", 0.0)

    @property
    def fuel_efficiency(self) -> float:
        """Fuel efficiency metric.

        燃油效率指标。
        """
        return self.metrics.get("fuel_efficiency", 0.0)
