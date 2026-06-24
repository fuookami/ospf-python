"""时间工具方法 / Time utility methods.

对应 Kotlin 端 Time data object。
Mirrors the Kotlin ``Time`` data object.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

# 默认格式化模式 / Default format pattern
_DEFAULT_FMT: str = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class Time:
    """时间工具类 / Time utility class.

    提供当前时间获取与日期时间格式化方法。
    Provides current-time retrieval and datetime formatting methods.
    """

    @staticmethod
    def now() -> datetime:
        """返回当前日期时间。

        Returns the current datetime.

        Returns:
            当前 datetime 对象。/ Current datetime instance.
        """
        return datetime.now()

    @staticmethod
    def today() -> date:
        """返回当前日期。

        Returns the current date.

        Returns:
            当前 date 对象。/ Current date instance.
        """
        return date.today()

    @staticmethod
    def format_dt(
        dt: datetime,
        *,
        pattern: str = _DEFAULT_FMT,
    ) -> str:
        """按指定模式格式化日期时间。

        Formats a datetime according to the given pattern.

        Args:
            dt: 待格式化的 datetime / The datetime to format.
            pattern: strptime/strftime 格式化模式 /
                strptime/strftime format pattern.

        Returns:
            格式化后的字符串。/ Formatted string.
        """
        return dt.strftime(pattern)

    @staticmethod
    def parse_dt(
        s: str,
        *,
        pattern: str = _DEFAULT_FMT,
    ) -> datetime:
        """按指定模式解析字符串为日期时间。

        Parses a string into a datetime using the given pattern.

        Args:
            s: 待解析的字符串 / The string to parse.
            pattern: strptime 格式化模式 / strptime format pattern.

        Returns:
            解析得到的 datetime 对象。/ Parsed datetime instance.
        """
        return datetime.strptime(s, pattern)
