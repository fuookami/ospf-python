"""Resource rule constraint enforcement.

资源规则约束执行 / Resource rule constraint enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceView:
    """View of a resource for constraint checking.

    用于约束检查的资源视图。
    """

    resource_id: str
    resource_type: str
    capacity: float
    current_usage: float


class ResourceRuleConstraint:
    """Enforces resource usage rules.

    强制执行资源使用规则。
    """

    def __init__(
        self,
        *,
        allow_overcapacity: bool = False,
        compatible_types: frozenset[tuple[str, str]] | None = None,
    ) -> None:
        self._allow_overcapacity = allow_overcapacity
        self._compatible = compatible_types

    def check(
        self,
        resources: tuple[ResourceView, ...],
    ) -> list[str]:
        """Validate resource rules against available resources.

        对可用资源验证资源规则。
        """
        violations: list[str] = []
        if not self._allow_overcapacity:
            violations.extend(
                self._check_capacity(resources),
            )
        if self._compatible is not None:
            violations.extend(
                self._check_compatibility(resources),
            )
        return violations

    def _check_capacity(
        self,
        resources: tuple[ResourceView, ...],
    ) -> list[str]:
        """Check that no resource exceeds its capacity.

        检查没有资源超过其容量。
        """
        violations: list[str] = []
        for res in resources:
            if res.current_usage > res.capacity:
                excess = res.current_usage - res.capacity
                violations.append(
                    f"Resource '{res.resource_id}' "
                    f"exceeds capacity by "
                    f"{excess:.1f} "
                    f"({res.current_usage:.1f}/"
                    f"{res.capacity:.1f})"
                )
        return violations

    def _check_compatibility(
        self,
        resources: tuple[ResourceView, ...],
    ) -> list[str]:
        """Check that resource type assignments are compatible.

        检查资源类型分配是否兼容。
        """
        violations: list[str] = []
        by_id: dict[str, ResourceView] = {r.resource_id: r for r in resources}
        assert self._compatible is not None
        for left_id, right_id in self._compatible:
            left = by_id.get(left_id)
            right = by_id.get(right_id)
            if left and right and left.resource_type != right.resource_type:
                violations.append(
                    f"Incompatible resources "
                    f"'{left_id}' and "
                    f"'{right_id}' "
                    f"({left.resource_type} != "
                    f"{right.resource_type})"
                )
        return violations

    def overcapacity_resources(
        self,
        resources: tuple[ResourceView, ...],
    ) -> tuple[str, ...]:
        """Return IDs of resources exceeding capacity.

        返回超过容量的资源 ID。
        """
        return tuple(r.resource_id for r in resources if r.current_usage > r.capacity)
