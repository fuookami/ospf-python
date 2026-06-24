"""相等性协议 / Equality protocols.

PartialEq / Eq 协议，对应 Kotlin 接口。
PartialEq / Eq protocols, corresponding to Kotlin interfaces.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PartialEq(Protocol):
    """部分相等协议 / Partial equality protocol.

    对应 Kotlin `interface PartialEq<in Self>`。
    Corresponds to Kotlin `interface PartialEq<in Self>`.
    """

    def __eq__(self, other: object) -> bool:
        """判断是否相等 / Check equality."""

    def __ne__(self, other: object) -> bool:
        """判断是否不等 / Check inequality."""


@runtime_checkable
class Eq(PartialEq, Protocol):
    """完全相等协议 / Full equality protocol.

    对应 Kotlin `interface Eq<in Self> : PartialEq<Self>`。
    Corresponds to Kotlin `interface Eq<in Self> : PartialEq<Self>`.
    """
