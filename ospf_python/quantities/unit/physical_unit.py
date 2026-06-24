"""物理单位协议。/ Physical unit protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PhysicalUnit(Protocol):
    """物理单位协议，定义单位转换接口。/

    Physical unit protocol defining conversion interface.
    """

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        ...

    def to_si(self, value: float) -> float:
        """将值转换为 SI 单位。/ Convert value to SI unit."""
        ...

    def from_si(self, value: float) -> float:
        """从 SI 单位转换值。/ Convert value from SI unit."""
        ...
