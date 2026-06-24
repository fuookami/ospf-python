"""排序协议 / Ordering protocols.

Order / PartialOrd / Ord 协议，对应 Kotlin 接口。
Order / PartialOrd / Ord protocols, corresponding to Kotlin interfaces.
"""

from __future__ import annotations

import enum
from typing import Protocol, Self, runtime_checkable

from ospf_python.utils.functional.eq import Eq, PartialEq


class Order(enum.Enum):
    """排序结果枚举 / Ordering result enum.

    对应 Kotlin `sealed interface Order`。
    Corresponds to Kotlin `sealed interface Order`.
    """

    LT = "lt"
    EQ = "eq"
    GT = "gt"


@runtime_checkable
class PartialOrd(PartialEq, Protocol):
    """部分有序协议 / Partial ordering protocol.

    对应 Kotlin `interface PartialOrd<in Self> : PartialEq<Self>`。
    Corresponds to Kotlin `interface PartialOrd<in Self> : PartialEq<Self>`.
    """

    def partial_cmp(self, other: Self) -> Order | None:
        """部分比较 / Partial comparison.

        Returns:
            Order | None: 比较结果，不可比较时返回 None。
            Comparison result, None if not comparable.
        """


@runtime_checkable
class Ord(PartialOrd, Eq, Protocol):
    """全序协议 / Total ordering protocol.

    对应 Kotlin `interface Ord<in Self> : PartialOrd<Self>, Eq<Self>, Comparable<Self>`。
    Corresponds to Kotlin `interface Ord<in Self> : PartialOrd<Self>, Eq<Self>, Comparable<Self>`.
    """

    def cmp(self, other: Self) -> Order:
        """全序比较 / Total comparison.

        Returns:
            Order: 比较结果。
            Comparison result.
        """
