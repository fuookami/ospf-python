"""乘法幺半群协议 / Multiplicative monoid protocol.

乘法幺半群是具有单位元的乘法半群。
A multiplicative monoid is a multiplicative semigroup
with a multiplicative identity.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable

from ospf_python.math.algebra.concept.multiplicative_semigroup import (
    MultiplicativeSemigroup,
)


@runtime_checkable
class MultiplicativeMonoid(MultiplicativeSemigroup, Protocol):
    """乘法幺半群协议 / Multiplicative monoid protocol.

    在乘法半群基础上增加单位元: a * 1 == 1 * a == a。
    Extends multiplicative semigroup with identity:
    a * 1 == 1 * a == a.
    """

    @property
    def one(self: Self) -> Self:
        """单位元（乘法单位元）/ One (multiplicative identity)."""
