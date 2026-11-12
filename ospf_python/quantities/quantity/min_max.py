"""物理量极值工具。/ Quantity min/max utilities."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from ospf_python._binding import quantity_ordering as _ordering

if TYPE_CHECKING:
    from ospf_python._binding.result import BindingResult
    from ospf_python.quantities.quantity.numeric_adapter import NumericAdapter
    from ospf_python.quantities.quantity.quantity import Quantity


def min_quantity[V](
    items: Iterable[Quantity[V]], *, numeric_adapter: NumericAdapter[V] | None = None
) -> BindingResult[Quantity[V]]:
    """返回最小物理量。/ Return minimum quantity.

    内置单位通过 Rust 精确 SI 比较；开放回调保持其比较协议。
    Builtin units use Rust exact SI comparisons; open callbacks retain their comparison protocol.

    Args:
        items: 物理量集合。/ Quantity collection.
        numeric_adapter: 自定义数值的显式导入策略。 / Explicit import policy for custom values.

    Returns:
        Ok 中的原最小对象，平局保留首次；失败显式返回 Result。
        Original minimum in Ok, first on ties; failures return Result explicitly.
    """
    return _ordering.select(items=items, maximum=False, numeric_adapter=numeric_adapter)


def max_quantity[V](
    items: Iterable[Quantity[V]], *, numeric_adapter: NumericAdapter[V] | None = None
) -> BindingResult[Quantity[V]]:
    """返回最大物理量。/ Return maximum quantity.

    内置单位通过 Rust 精确 SI 比较；开放回调保持其比较协议。
    Builtin units use Rust exact SI comparisons; open callbacks retain their comparison protocol.

    Args:
        items: 物理量集合。/ Quantity collection.
        numeric_adapter: 自定义数值的显式导入策略。 / Explicit import policy for custom values.

    Returns:
        Ok 中的原最大对象，平局保留首次；失败显式返回 Result。
        Original maximum in Ok, first on ties; failures return Result explicitly.
    """
    return _ordering.select(items=items, maximum=True, numeric_adapter=numeric_adapter)
