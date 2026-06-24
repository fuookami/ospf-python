"""float64 值转换协议 / Float64 value converter protocol.

将值转换为 float64 表示的协议。
Protocol for converting values to float64 representation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Flt64ValueConverter(Protocol):
    """float64 值转换协议 / Float64 value converter protocol.

    将值转换为 Python float (IEEE 754 float64)。
    Converts values to Python float (IEEE 754 float64).
    """

    def to_flt64(self) -> float:
        """转换为 float64 / Convert to float64."""
