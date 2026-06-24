"""半群协议 / Semigroup protocol.

半群是具有结合律二元运算的代数结构。
A semigroup is an algebraic structure with an associative binary operation.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class Semigroup(Protocol):
    """半群协议 / Semigroup protocol.

    满足结合律: (a + b) + c == a + (b + c)。
    Satisfies associativity: (a + b) + c == a + (b + c).
    """

    def __add__(self: Self, other: Self) -> Self:
        """二元运算 / Binary operation."""
