"""值特征协议 / Value traits protocol.

ValueTraits 组合零值、单位值和边界值。
ValueTraits combines zero, one, and boundary values.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ospf_python.math.algebra.concept.constant_providers import (
    HasBounds,
    HasOne,
    HasZero,
)


@runtime_checkable
class ValueTraits(HasZero, HasOne, HasBounds, Protocol):
    """值特征协议 / Value traits protocol.

    组合零值、单位值和上下边界。
    Combines zero, one, and min/max bounds.
    """
