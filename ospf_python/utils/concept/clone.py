"""克隆与移动协议 / Clone and move protocols.

Copyable / Movable 协议，对应 Kotlin 接口。
Copyable / Movable protocols, corresponding to Kotlin interfaces.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class Copyable(Protocol):
    """可复制协议 / Copyable protocol.

    对应 Kotlin `interface Copyable<Self> : Movable<Self>`。
    Shallow copy.
    """

    def copy(self) -> Self:
        """浅复制 / Shallow copy."""


@runtime_checkable
class Movable(Copyable, Protocol):
    """可移动协议 / Movable protocol.

    对应 Kotlin `interface Movable<Self>`。
    Deep copy.
    """

    def move(self) -> Self:
        """深复制（移动）/ Deep copy (move)."""
