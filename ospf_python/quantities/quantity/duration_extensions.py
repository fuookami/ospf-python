"""时长扩展。/ Duration extensions."""

from __future__ import annotations

from datetime import timedelta as timedelta
from typing import TYPE_CHECKING, Any

# Rust 从当前 globals 读取工厂，不是仅类型导入。 / Rust resolves this factory from live globals.
from ospf_python._binding import quantity_duration as _duration
from ospf_python.quantities.quantity.quantity import Quantity as Quantity  # noqa: TC001
from ospf_python.quantities.unit.time_unit import SECOND as SECOND

if TYPE_CHECKING:
    from decimal import Context

    from ospf_python._binding.result import BindingResult
    from ospf_python.quantities.quantity.numeric_adapter import NumericAdapter


def from_hours[V](
    hours: V,
    *,
    context: Context | None = None,
    exact: bool = True,
    numeric_adapter: NumericAdapter[V] | None = None,
) -> BindingResult[Any]:
    """经 Rust 换算小时到秒，显式返回 Result。 / Convert hours to seconds through Rust, returning Result.

    Args:
        hours: 小时数或开放乘法输入。/ Hours or open multiplication input.
        context: 仅用于最终 Decimal 输出。 / Final Decimal export only.
        exact: 拒绝 Decimal 输出损失。 / Reject Decimal export loss.
        numeric_adapter: 显式数值表示策略。 / Explicit numeric representation strategy.

    Returns:
        秒制 Quantity/当前工厂输出或失败。 / Second quantity/current factory output or failure.
    """
    return _duration.from_value(
        value=hours,
        factor=3600,
        context=context,
        exact=exact,
        numeric_adapter=numeric_adapter,
    )


def from_minutes[V](
    minutes: V,
    *,
    context: Context | None = None,
    exact: bool = True,
    numeric_adapter: NumericAdapter[V] | None = None,
) -> BindingResult[Any]:
    """经 Rust 换算分钟到秒，显式返回 Result。 / Convert minutes to seconds through Rust, returning Result.

    Args:
        minutes: 分钟数或开放乘法输入。/ Minutes or open multiplication input.
        context: 仅用于最终 Decimal 输出。 / Final Decimal export only.
        exact: 拒绝 Decimal 输出损失。 / Reject Decimal export loss.
        numeric_adapter: 显式数值表示策略。 / Explicit numeric representation strategy.

    Returns:
        秒制 Quantity/当前工厂输出或失败。 / Second quantity/current factory output or failure.
    """
    return _duration.from_value(
        value=minutes,
        factor=60,
        context=context,
        exact=exact,
        numeric_adapter=numeric_adapter,
    )


def to_timedelta[V](
    qty: Quantity[V], *, numeric_adapter: NumericAdapter[V] | None = None
) -> BindingResult[Any]:
    """将时间量转为有符号 timedelta，显式返回 Result。 / Convert time quantity to signed timedelta, returning Result.

    Args:
        qty: 时间物理量。/ Time quantity.
        numeric_adapter: 显式精确导入策略，无数值重建。 / Explicit exact import, without numeric reconstruction.

    Returns:
        timedelta/当前工厂输出或失败。 / Timedelta/current factory output or failure.
    """
    return _duration.to_timedelta(owner=qty, numeric_adapter=numeric_adapter)
