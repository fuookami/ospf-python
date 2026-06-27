"""数值字面量解析器。

Numeric literal parser for polynomial strings.
"""

from __future__ import annotations

import re

# 数值字面量模式 / Numeric literal pattern
_FLOAT_PATTERN = re.compile(
    r"[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?",
)
_INT_PATTERN = re.compile(r"[+-]?\d+")


class NumberParser:
    """数值字面量解析器，提供静态工具方法。

    Numeric literal parser providing static utility
    methods for parsing numbers from strings.

    支持整数、浮点数和科学记数法。
    Supports integers, floats, and scientific notation.
    """

    @staticmethod
    def parse(text: str) -> float | None:
        """解析数值字符串为浮点数。

        Parse a numeric string to float.

        Args:
            text: 待解析的数值字符串。/
                Numeric string to parse.

        Returns:
            解析得到的浮点数，失败返回 None。/
            Parsed float, or None on failure.
        """
        trimmed = text.strip()
        if not trimmed:
            return None
        match = _FLOAT_PATTERN.fullmatch(trimmed)
        if match is None:
            return None
        try:
            return float(trimmed)
        except ValueError:
            return None

    @staticmethod
    def parse_int(text: str) -> int | None:
        """解析整数字符串。

        Parse an integer string.

        Args:
            text: 待解析的整数字符串。/
                Integer string to parse.

        Returns:
            解析得到的整数，失败返回 None。/
            Parsed int, or None on failure.
        """
        trimmed = text.strip()
        if not trimmed:
            return None
        match = _INT_PATTERN.fullmatch(trimmed)
        if match is None:
            return None
        try:
            return int(trimmed)
        except ValueError:
            return None

    @staticmethod
    def is_numeric(text: str) -> bool:
        """判断字符串是否为数值。

        Check whether a string is numeric.

        Args:
            text: 待判断的字符串。/ String to check.

        Returns:
            是否为数值。/ Whether numeric.
        """
        return NumberParser.parse(text) is not None
