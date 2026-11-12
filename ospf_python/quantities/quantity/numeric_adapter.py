"""自定义精确数值的显式换算边界。 / Explicit conversion boundary for custom exact numeric values."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from ospf_python.utils.functional.result import Result


class NumericAdapter[V](Protocol):
    """以分数快照连接开放数值与 Rust 单位内核。 / Connect open values to the Rust unit kernel through fraction snapshots.

    适配器负责自身表示的导入/输出策略，不替代原生单位算术。
    The adapter owns its representation policy, not native unit arithmetic.
    """

    def to_fraction(self, value: V) -> Result[Fraction, Any, Any]:
        """导入一次值快照，不要求 __float__。 / Import one value snapshot without requiring __float__.

        Args:
            value: 原始输入或开放源的 SI 输出。 / Original input or an open source's SI output.

        Returns:
            Ok 中的内置 Fraction，或保留在外层错误中的 Result。
            A builtin Fraction in Ok, or a Result retained in the outer failure.
        """
        ...

    def from_fraction(self, value: Fraction) -> Result[V, Any, Any]:
        """在实际输出边界恢复自定义表示。 / Restore the custom representation at an actual export boundary.

        Args:
            value: Rust 换算后的精确分数快照。 / Exact fraction snapshot after Rust conversion.

        Returns:
            Ok 中的自定义值；失败或未支持的 Result 不被静默丢弃。
            Custom value in Ok; failed or unsupported Results are not silently discarded.
        """
        ...
