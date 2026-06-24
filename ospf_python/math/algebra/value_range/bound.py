"""边界类型定义。

Bound type definitions for value ranges.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


class BoundType(enum.Enum):
    """边界类型枚举。

    Bound type enumeration.

    Attributes:
        CLOSED: 闭区间边界 [。/ Closed bound [.
        OPEN: 开区间边界 (。/ Open bound (.
        UNBOUNDED: 无界。/ Unbounded.
    """

    CLOSED = "closed"
    OPEN = "open"
    UNBOUNDED = "unbounded"


@dataclass(frozen=True)
class Bound(Generic[T]):
    """区间边界值。

    A boundary value for an interval.

    Attributes:
        value: 边界值。/ Boundary value.
        bound_type: 边界类型。/ Bound type.
    """

    value: T | None
    bound_type: BoundType

    @staticmethod
    def closed(value: T) -> Bound[T]:
        """创建闭区间边界。/ Create a closed bound.

        Args:
            value: 边界值。/ Boundary value.

        Returns:
            闭区间边界。/ Closed bound.
        """
        return Bound(value=value, bound_type=BoundType.CLOSED)

    @staticmethod
    def open(value: T) -> Bound[T]:
        """创建开区间边界。/ Create an open bound.

        Args:
            value: 边界值。/ Boundary value.

        Returns:
            开区间边界。/ Open bound.
        """
        return Bound(value=value, bound_type=BoundType.OPEN)

    @staticmethod
    def unbounded() -> Bound[T]:
        """创建无界边界。/ Create an unbounded bound.

        Returns:
            无界边界。/ Unbounded bound.
        """
        return Bound(value=None, bound_type=BoundType.UNBOUNDED)

    @property
    def is_closed(self) -> bool:
        """是否为闭区间。/ Whether closed."""
        return self.bound_type == BoundType.CLOSED

    @property
    def is_open(self) -> bool:
        """是否为开区间。/ Whether open."""
        return self.bound_type == BoundType.OPEN

    @property
    def is_unbounded(self) -> bool:
        """是否无界。/ Whether unbounded."""
        return self.bound_type == BoundType.UNBOUNDED
