"""时长扩展。/ Duration extensions."""

from __future__ import annotations

from datetime import timedelta

from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.time_unit import SECOND


def from_hours(hours: float) -> Quantity[float]:
    """从小时创建时长。/ Create duration from hours.

    Args:
        hours: 小时数。/ Number of hours.

    Returns:
        对应的秒制物理量。/ Corresponding quantity in seconds.
    """
    return Quantity(value=hours * 3600, unit=SECOND)


def from_minutes(minutes: float) -> Quantity[float]:
    """从分钟创建时长。/ Create duration from minutes.

    Args:
        minutes: 分钟数。/ Number of minutes.

    Returns:
        对应的秒制物理量。/ Corresponding quantity in seconds.
    """
    return Quantity(value=minutes * 60, unit=SECOND)


def to_timedelta(qty: Quantity[float]) -> timedelta:
    """将物理量转为 timedelta。/ Convert quantity to timedelta.

    Args:
        qty: 时间物理量。/ Time quantity.

    Returns:
        对应的 timedelta。/ Corresponding timedelta.
    """
    seconds = qty.unit.to_si(float(qty.value))
    return timedelta(seconds=seconds)
