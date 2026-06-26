"""装载约束定义 / Stowage constraint definition.

定义通用的装载约束结构。
Defines the generic stowage constraint structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StowageConstraint:
    """装载约束 / Stowage constraint.

    描述一条装载约束规则，包含约束类型和参数。
    Describes a stowage constraint rule, including type and
    parameters.

    Attributes:
        constraint_type: 约束类型标识 /
            Constraint type identifier.
        parameters: 约束参数映射 /
            Constraint parameter mapping.
    """

    constraint_type: str = ""
    """约束类型标识 / Constraint type identifier."""

    parameters: tuple[tuple[str, Any], ...] = field(
        default_factory=tuple,
    )
    """约束参数键值对 / Constraint parameter key-value pairs."""

    @staticmethod
    def create(
        *,
        constraint_type: str,
        parameters: dict[str, Any] | None = None,
    ) -> StowageConstraint:
        """创建装载约束。

        Create stowage constraint.

        Args:
            constraint_type: 约束类型标识。/
                Constraint type identifier.
            parameters: 约束参数。/ Constraint parameters.

        Returns:
            约束实例。/ Constraint instance.
        """
        params = tuple(
            sorted((parameters or {}).items()),
        )
        return StowageConstraint(
            constraint_type=constraint_type,
            parameters=params,
        )

    def get_parameter(self, key: str) -> Any | None:
        """获取约束参数值。

        Get constraint parameter value.

        Args:
            key: 参数键。/ Parameter key.

        Returns:
            参数值，不存在时返回 None。
            Parameter value, or None if not found.
        """
        for k, v in self.parameters:
            if k == key:
                return v
        return None

    def has_parameter(self, key: str) -> bool:
        """检查是否包含指定参数。

        Check whether a parameter exists.

        Args:
            key: 参数键。/ Parameter key.

        Returns:
            参数存在时返回 True。
            True if the parameter exists.
        """
        return any(k == key for k, _ in self.parameters)

    @property
    def parameter_count(self) -> int:
        """参数数量。

        Number of parameters.

        Returns:
            参数个数。/ Parameter count.
        """
        return len(self.parameters)
