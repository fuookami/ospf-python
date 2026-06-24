"""乘法半群协议 / Multiplicative semigroup protocol.

乘法半群是具有乘法运算的半群。
A multiplicative semigroup is a semigroup with multiplication.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class MultiplicativeSemigroup(Protocol):
    """乘法半群协议 / Multiplicative semigroup protocol.

    满足乘法结合律: (a * b) * c == a * (b * c)。
    Satisfies multiplicative associativity:
    (a * b) * c == a * (b * c).
    """

    def __mul__(self: Self, other: Self) -> Self:
        """乘法 / Multiplication."""
