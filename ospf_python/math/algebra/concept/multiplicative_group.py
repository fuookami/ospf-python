"""乘法群协议 / Multiplicative group protocol.

乘法群是每个非零元素都有乘法逆元的乘法幺半群。
A multiplicative group is a multiplicative monoid where
every nonzero element has a multiplicative inverse.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable

from ospf_python.math.algebra.concept.multiplicative_monoid import (
    MultiplicativeMonoid,
)


@runtime_checkable
class MultiplicativeGroup(MultiplicativeMonoid, Protocol):
    """乘法群协议 / Multiplicative group protocol.

    在乘法幺半群基础上增加除法和倒数。
    Extends multiplicative monoid with division and reciprocal.
    """

    def __truediv__(self: Self, other: Self) -> Self:
        """除法 / Division."""

    def __rtruediv__(self: Self, other: Self) -> Self:
        """右除法 / Right division."""

    @property
    def reciprocal(self: Self) -> Self:
        """乘法逆元 / Multiplicative inverse (1/a)."""
