"""约束上下文 / Constraint context.

管理 BPP2D 约束的注册与查询。
Manages registration and lookup of BPP2D constraints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.framework.bpp2d.domain.item.error.bpp2d_errors import (
    Bpp2dErrors,
)
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python.framework.bpp2d.domain.constraint.model.constraint_base import (
        ConstraintBase,
    )


class ConstraintContext:
    """约束上下文 / Constraint context.

    维护约束注册表，提供约束的注册、查询和管理功能。
    在二维装箱中充当约束的中央仓库。
    Maintains the constraint registry, providing
    registration, query, and management functions. Acts
    as the central repository for constraints in 2D BPP.

    Attributes:
        _constraints: 内部约束字典 /
            Internal constraint dictionary.
    """

    def __init__(self) -> None:
        """初始化空约束上下文 /
        Initialize empty constraint context."""
        self._constraints: dict[str, ConstraintBase] = {}

    def register(
        self,
        constraint: ConstraintBase,
    ) -> Result[None, str, Err[str]]:
        """注册约束 / Register a constraint.

        如果约束键已存在，返回失败结果。
        Returns a failure result if the key exists.

        Args:
            constraint: 要注册的约束 / Constraint to register.

        Returns:
            注册结果 / Registration result.
        """
        key = constraint.constraint_key
        if key in self._constraints:
            return Failed(
                Err(
                    _code=(Bpp2dErrors.CONSTRAINT_NOT_FOUND.value),
                    _message=(
                        f"约束键已存在: {key} / Constraint key already exists: {key}"
                    ),
                )
            )
        self._constraints[key] = constraint
        return Ok(None)

    def unregister(
        self,
        constraint_key: str,
    ) -> Result[None, str, Err[str]]:
        """注销约束 / Unregister a constraint.

        Args:
            constraint_key: 约束键 / Constraint key.

        Returns:
            注销结果 / Unregistration result.
        """
        if constraint_key not in self._constraints:
            return Failed(
                Err(
                    _code=(Bpp2dErrors.CONSTRAINT_NOT_FOUND.value),
                    _message=(
                        f"约束未找到: {constraint_key} / "
                        f"Constraint not found: "
                        f"{constraint_key}"
                    ),
                )
            )
        del self._constraints[constraint_key]
        return Ok(None)

    def get(self, key: str) -> ConstraintBase | None:
        """获取约束 / Get a constraint.

        Args:
            key: 约束键 / Constraint key.

        Returns:
            约束实例或 None / Constraint instance or None.
        """
        return self._constraints.get(key)

    def get_or_error(
        self,
        key: str,
    ) -> Result[ConstraintBase, str, Err[str]]:
        """获取约束或返回错误 / Get constraint or error.

        Args:
            key: 约束键 / Constraint key.

        Returns:
            包含约束的成功结果或失败结果。
            Success result with constraint or failure.
        """
        constraint = self._constraints.get(key)
        if constraint is None:
            return Failed(
                Err(
                    _code=(Bpp2dErrors.CONSTRAINT_NOT_FOUND.value),
                    _message=(f"约束未找到: {key} / Constraint not found: {key}"),
                )
            )
        return Ok(constraint)

    def constraints(self) -> tuple[ConstraintBase, ...]:
        """获取所有已注册约束 / Get all registered constraints.

        Returns:
            约束元组 / Constraint tuple.
        """
        return tuple(self._constraints.values())

    def constraint_keys(self) -> tuple[str, ...]:
        """获取所有约束键 / Get all constraint keys.

        Returns:
            约束键元组 / Constraint key tuple.
        """
        return tuple(self._constraints.keys())

    def get_for_item(
        self,
        item_key: str,
    ) -> tuple[ConstraintBase, ...]:
        """获取适用于指定物品的约束 /
        Get constraints applicable to an item.

        Args:
            item_key: 物品键 / Item key.

        Returns:
            适用于该物品的约束元组。
            Constraint tuple applicable to the item.
        """
        return tuple(c for c in self._constraints.values() if c.applies_to(item_key))

    def contains(self, key: str) -> bool:
        """检查约束是否存在 / Check if constraint exists.

        Args:
            key: 约束键 / Constraint key.

        Returns:
            是否存在 / Whether exists.
        """
        return key in self._constraints

    @property
    def size(self) -> int:
        """获取约束数量 / Get constraint count.

        Returns:
            已注册约束数量 / Number of registered constraints.
        """
        return len(self._constraints)

    @property
    def is_empty(self) -> bool:
        """是否为空 / Whether empty.

        Returns:
            无注册约束时返回 True。
            True when no constraints registered.
        """
        return len(self._constraints) == 0

    def clear(self) -> None:
        """清空所有约束 / Clear all constraints."""
        self._constraints.clear()
