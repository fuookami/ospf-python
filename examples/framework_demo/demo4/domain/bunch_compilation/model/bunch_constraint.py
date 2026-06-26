"""Bunch constraint model for validation rules.

任务组约束模型 / Bunch constraint model for validation rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .bunch import Bunch

MAX_TASKS_DEFAULT: int = 50
MIN_UTILIZATION_DEFAULT: float = 0.5


@dataclass(frozen=True)
class BunchConstraint:
    """A constraint that can be checked against a bunch.

    可对任务组进行检查的约束。
    """

    constraint_type: str
    parameters: dict[str, Any]

    def is_satisfied_by(self, bunch: Bunch) -> bool:
        """Check whether the bunch satisfies this constraint.

        检查任务组是否满足此约束。
        """
        check_fn = self._resolve_checker()
        return bool(check_fn(bunch))

    def violation_reason(self, bunch: Bunch) -> str | None:
        """Return a human-readable reason if the constraint is violated.

        如果约束被违反，返回人类可读的原因。
        """
        if self.is_satisfied_by(bunch):
            return None
        return self._describe_violation(bunch)

    def _resolve_checker(self) -> Any:
        """Resolve the checker function for the constraint type.

        解析约束类型的检查函数。
        """
        checkers: dict[str, Any] = {
            "max_tasks": self._check_max_tasks,
            "min_duration": self._check_min_duration,
            "max_duration": self._check_max_duration,
            "resource_allowed": self._check_resource_allowed,
        }
        return checkers.get(
            self.constraint_type,
            self._check_default,
        )

    def _check_max_tasks(self, bunch: Bunch) -> bool:
        """Check task count against max_tasks parameter.

        检查任务数是否超过 max_tasks 参数。
        """
        limit = self.parameters.get(
            "max_tasks",
            MAX_TASKS_DEFAULT,
        )
        return bool(bunch.task_count <= limit)

    def _check_min_duration(self, bunch: Bunch) -> bool:
        """Check duration meets minimum requirement.

        检查持续时间是否满足最低要求。
        """
        minimum = self.parameters.get("min_duration", 0.0)
        return bool(bunch.duration >= minimum)

    def _check_max_duration(self, bunch: Bunch) -> bool:
        """Check duration does not exceed maximum.

        检查持续时间是否未超过最大值。
        """
        maximum = self.parameters.get(
            "max_duration",
            float("inf"),
        )
        return bool(bunch.duration <= maximum)

    def _check_resource_allowed(self, bunch: Bunch) -> bool:
        """Check resource type is in the allowed set.

        检查资源类型是否在允许集合中。
        """
        allowed = self.parameters.get("allowed_resources", ())
        return bunch.resource_type in allowed

    def _check_default(self, bunch: Bunch) -> bool:
        """Default checker that always passes.

        默认检查器，始终通过。
        """
        _ = bunch
        return True

    def _describe_violation(self, bunch: Bunch) -> str:
        """Generate a violation description.

        生成违反描述。
        """
        return f"Bunch {bunch.bunch_id} violates constraint '{self.constraint_type}'"
