"""物理单位协议。/ Physical unit protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PhysicalUnit[Input = Any, Standard = Any, Output = Any](Protocol):
    """物理单位协议，定义单位转换接口。/

    Physical unit protocol defining conversion interface.

    Input/Standard/Output 分别描述开放回调的输入、SI 中间值和输出，默认 Any。
    Input/Standard/Output describe open callback input, SI intermediate and output,
    defaulting to Any. Native builtin-unit conversion has its own domain policy.
    """

    @property
    def symbol(self) -> str:
        """单位符号。/ Unit symbol."""
        ...

    def to_si(self, value: Input) -> Standard:
        """将值转换为 SI 单位。/ Convert value to SI unit."""
        ...

    def from_si(self, value: Standard) -> Output:
        """从 SI 单位转换值。/ Convert value from SI unit."""
        ...
