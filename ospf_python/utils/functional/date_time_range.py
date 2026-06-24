"""日期时间范围工具。

DateTime range utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DateTimeRange:
    """不可变的日期时间范围。

    An immutable date-time range with a start and end.

    Attributes:
        start: 起始时间。/ Start of the range.
        end: 结束时间。/ End of the range.
    """

    start: datetime
    end: datetime


def contains(range_: DateTimeRange, dt: datetime) -> bool:
    """检查给定时间是否在范围内（闭区间）。

    Checks whether the given datetime falls within the range (inclusive).

    Args:
        range_: 日期时间范围。/ The date-time range.
        dt: 待检查的时间。/ Datetime to check.

    Returns:
        若 dt 在 [start, end] 区间内则返回 True。
        True if dt is in [start, end].
    """
    return range_.start <= dt <= range_.end


def overlaps(r1: DateTimeRange, r2: DateTimeRange) -> bool:
    """检查两个范围是否重叠。

    Checks whether two date-time ranges overlap.

    Args:
        r1: 第一个范围。/ First range.
        r2: 第二个范围。/ Second range.

    Returns:
        若两个范围有交集则返回 True。
        True if the two ranges intersect.
    """
    return r1.start <= r2.end and r2.start <= r1.end
