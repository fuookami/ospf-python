"""物理量极值工具。/ Quantity min/max utilities."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.quantities.quantity.quantity import Quantity


def min_quantity(
    items: Iterable[Quantity[float]],
) -> Quantity[float]:
    """返回最小物理量。/ Return minimum quantity.

    通过 SI 值进行比较。/ Compares via SI values.

    Args:
        items: 物理量集合。/ Quantity collection.

    Returns:
        最小的物理量。/ Minimum quantity.
    """
    return min(items, key=lambda q: q.unit.to_si(float(q.value)))


def max_quantity(
    items: Iterable[Quantity[float]],
) -> Quantity[float]:
    """返回最大物理量。/ Return maximum quantity.

    通过 SI 值进行比较。/ Compares via SI values.

    Args:
        items: 物理量集合。/ Quantity collection.

    Returns:
        最大的物理量。/ Maximum quantity.
    """
    return max(items, key=lambda q: q.unit.to_si(float(q.value)))
