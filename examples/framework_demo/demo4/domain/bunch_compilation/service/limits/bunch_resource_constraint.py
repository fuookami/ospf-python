"""Bunch resource constraint enforcement.

任务组资源约束执行 / Bunch resource constraint enforcement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...model.bunch import Bunch


class BunchResourceConstraint:
    """Enforces resource compatibility within bunches.

    强制任务组内的资源兼容性。
    """

    def __init__(
        self,
        allowed_resources: frozenset[str],
    ) -> None:
        self._allowed = allowed_resources

    def check(self, bunch: Bunch) -> bool:
        """Return True if the bunch uses an allowed resource.

        如果任务组使用了允许的资源则返回 True。
        """
        return bunch.resource_type in self._allowed

    def violations(self, bunch: Bunch) -> list[str]:
        """Return violation messages for resource issues.

        返回资源违规消息。
        """
        if self.check(bunch):
            return []
        return [
            f"Bunch '{bunch.bunch_id}' uses "
            f"disallowed resource "
            f"'{bunch.resource_type}' "
            f"(allowed: {sorted(self._allowed)})",
        ]

    def filter_compliant(
        self,
        bunches: tuple[Bunch, ...],
    ) -> tuple[Bunch, ...]:
        """Return only bunches with allowed resources.

        仅返回使用允许资源的任务组。
        """
        return tuple(bunch for bunch in bunches if self.check(bunch))

    def group_by_resource(
        self,
        bunches: tuple[Bunch, ...],
    ) -> dict[str, tuple[Bunch, ...]]:
        """Group compliant bunches by their resource type.

        按资源类型对合规任务组进行分组。
        """
        groups: dict[str, list[Bunch]] = {}
        for bunch in self.filter_compliant(bunches):
            groups.setdefault(
                bunch.resource_type,
                [],
            ).append(bunch)
        return {res: tuple(items) for res, items in groups.items()}

    @property
    def allowed_resources(self) -> frozenset[str]:
        """The set of allowed resource types.

        允许的资源类型集合。
        """
        return self._allowed
