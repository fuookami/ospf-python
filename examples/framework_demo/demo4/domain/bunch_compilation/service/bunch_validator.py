"""Bunch validator for checking bunch feasibility.

任务组验证器：检查任务组可行性。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..model.bunch import Bunch


class BunchValidator:
    """Validates that a bunch meets structural requirements.

    验证任务组是否满足结构性要求。
    """

    def validate(self, bunch: Bunch) -> list[str]:
        """Run all validation checks and return messages.

        运行所有验证检查并返回消息列表。
        """
        messages: list[str] = []
        self._check_time_order(bunch, messages)
        self._check_task_uniqueness(bunch, messages)
        self._check_duration_positive(bunch, messages)
        self._check_non_empty(bunch, messages)
        return messages

    def is_valid(self, bunch: Bunch) -> bool:
        """Return True if the bunch passes all checks.

        如果任务组通过所有检查则返回 True。
        """
        return len(self.validate(bunch)) == 0

    def _check_time_order(
        self,
        bunch: Bunch,
        messages: list[str],
    ) -> None:
        """Verify start_time <= end_time.

        验证 start_time <= end_time。
        """
        if bunch.start_time > bunch.end_time:
            messages.append(
                f"Bunch '{bunch.bunch_id}': "
                f"start_time ({bunch.start_time}) "
                f"> end_time ({bunch.end_time})"
            )

    def _check_task_uniqueness(
        self,
        bunch: Bunch,
        messages: list[str],
    ) -> None:
        """Verify no duplicate task ids in the bunch.

        验证任务组中没有重复的任务 ID。
        """
        seen: set[str] = set()
        for task_id in bunch.tasks:
            if task_id in seen:
                messages.append(f"Bunch '{bunch.bunch_id}': duplicate task '{task_id}'")
            seen.add(task_id)

    def _check_duration_positive(
        self,
        bunch: Bunch,
        messages: list[str],
    ) -> None:
        """Verify the bunch has non-negative duration.

        验证任务组持续时间为非负。
        """
        if bunch.duration < 0:
            messages.append(
                f"Bunch '{bunch.bunch_id}': negative duration {bunch.duration}"
            )

    def _check_non_empty(
        self,
        bunch: Bunch,
        messages: list[str],
    ) -> None:
        """Verify the bunch contains at least one task.

        验证任务组至少包含一个任务。
        """
        if bunch.task_count == 0:
            messages.append(f"Bunch '{bunch.bunch_id}': no tasks")
