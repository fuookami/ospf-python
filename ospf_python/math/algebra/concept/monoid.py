"""幺半群协议 / Monoid protocol.

幺半群是具有单位元的半群。
A monoid is a semigroup with an identity element.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable

from ospf_python.math.algebra.concept.semigroup import Semigroup


@runtime_checkable
class Monoid(Semigroup, Protocol):
    """幺半群协议 / Monoid protocol.

    在半群基础上增加零元（单位元）: a + 0 == 0 + a == a。
    Extends semigroup with zero (identity): a + 0 == 0 + a == a.
    """

    @property
    def zero(self: Self) -> Self:
        """零元（加法单位元）/ Zero (additive identity)."""
