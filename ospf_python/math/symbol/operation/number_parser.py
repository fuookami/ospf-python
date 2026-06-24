"""数值解析器。

Number parser for polynomial coefficient parsing.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class NumberParser:
    """数值解析器。

    Parses numeric values from strings, supporting
    integers, floats, and fractions.

    Attributes:
        input: 待解析的输入字符串。/ Input string.
    """

    input: str

    def parse(self) -> int | float | Fraction | None:
        """解析数值。

        Parse a numeric value.

        Returns:
            解析结果或 None。/ Parsed value or None.
        """
        trimmed = self.input.strip()
        if not trimmed:
            return None
        if "/" in trimmed:
            return self._parse_fraction(trimmed)
        if "." in trimmed or "e" in trimmed.lower():
            return self._parse_float(trimmed)
        return self._parse_int(trimmed)

    def _parse_int(self, text: str) -> int | None:
        """解析整数。/ Parse integer."""
        try:
            return int(text)
        except ValueError:
            return None

    def _parse_float(self, text: str) -> float | None:
        """解析浮点数。/ Parse float."""
        try:
            return float(text)
        except ValueError:
            return None

    def _parse_fraction(self, text: str) -> Fraction | None:
        """解析分数。/ Parse fraction."""
        parts = text.split("/", 1)
        if len(parts) != 2:
            return None
        try:
            return Fraction(int(parts[0]), int(parts[1]))
        except (ValueError, ZeroDivisionError):
            return None
