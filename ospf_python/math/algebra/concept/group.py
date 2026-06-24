"""群协议 / Group protocol.

群是每个元素都有逆元的幺半群。
A group is a monoid where every element has an inverse.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable

from ospf_python.math.algebra.concept.monoid import Monoid


@runtime_checkable
class Group(Monoid, Protocol):
    """群协议 / Group protocol.

    在幺半群基础上增加逆元: a + (-a) == 0。
    Extends monoid with inverse: a + (-a) == 0.
    """

    def __neg__(self: Self) -> Self:
        """加法逆元 / Additive inverse."""

    def __sub__(self: Self, other: Self) -> Self:
        """减法 / Subtraction (a - b == a + (-b))."""
