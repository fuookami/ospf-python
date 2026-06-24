"""四元组 / Quadruple.

Quadruple[A, B, C, D] 四元组类型。
Quadruple[A, B, C, D] four-element tuple type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")


@dataclass(frozen=True)
class Quadruple(Generic[A, B, C, D]):
    """四元组 / Four-element tuple.

    对应 Kotlin `data class Quadruple<A, B, C, D>`。
    Corresponds to Kotlin `data class Quadruple<A, B, C, D>`.

    Args:
        first: 第一个元素 / First element.
        second: 第二个元素 / Second element.
        third: 第三个元素 / Third element.
        fourth: 第四个元素 / Fourth element.
    """

    first: A
    second: B
    third: C
    fourth: D
