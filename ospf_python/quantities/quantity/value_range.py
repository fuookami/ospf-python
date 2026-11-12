"""物理量值范围。/ Physical quantity value range."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from ospf_python._binding import quantity_ordering as _ordering

if TYPE_CHECKING:
    from ospf_python._binding.result import BindingResult
    from ospf_python.quantities.quantity.numeric_adapter import NumericAdapter
    from ospf_python.quantities.quantity.quantity import Quantity

V = TypeVar("V", default=Any)


@dataclass(frozen=True)
class QuantityValueRange(Generic[V]):
    """物理量值范围，由最小值和最大值界定。

    Physical quantity value range bounded by
    minimum and maximum quantities.

    Attributes:
        min_qty: 最小值。/ Minimum quantity.
        max_qty: 最大值。/ Maximum quantity.
    """

    min_qty: Quantity[V]
    max_qty: Quantity[V]

    def contains(
        self, qty: Quantity[V], *, numeric_adapter: NumericAdapter[V] | None = None
    ) -> BindingResult[bool]:
        """检查物理量是否在范围内。

        Check if quantity is within range.

        内置单位通过 Rust 精确 SI 比较；开放回调保留比较协议。
        Builtin units use Rust exact SI comparisons; open callbacks retain comparisons.

        Args:
            qty: 待检查的物理量。
                Quantity to check.
            numeric_adapter: 自定义数值的显式导入策略。 / Explicit import policy for custom values.

        Returns:
            Ok 中的闭区间判断或保留来源的失败。 / Inclusive containment in Ok or failure retaining provenance.
        """
        return _ordering.contains(
            bounds=self, quantity=qty, numeric_adapter=numeric_adapter
        )
