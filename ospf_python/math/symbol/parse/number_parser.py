"""数值字面量解析器。

Numeric literal parser for polynomial strings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction

from ospf_python.math.symbol.parse.parse_result import (
    ParseResult,
)

# 数值字面量模式 / Numeric literal pattern
_NUMBER_PATTERN = re.compile(r"[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?")


@dataclass(frozen=True)
class NumberParser:
    """数值字面量解析器。

    Parses numeric literals from the beginning of a
    string, supporting integers, floats, and scientific
    notation.

    Attributes:
        input: 待解析的输入字符串。/ Input string.
    """

    input: str

    def parse_int(self) -> ParseResult[int] | None:
        """解析整数字面量。

        Parse an integer literal.

        Returns:
            解析结果或 None。/ Parse result or None.
        """
        trimmed = self.input.lstrip()
        match = _NUMBER_PATTERN.match(trimmed)
        if match is None:
            return None
        text = match.group(0)
        if "." in text or "e" in text.lower():
            return None
        remaining = trimmed[match.end() :]
        return ParseResult.of(int(text), remaining)

    def parse_float(self) -> ParseResult[float] | None:
        """解析浮点字面量。

        Parse a float literal.

        Returns:
            解析结果或 None。/ Parse result or None.
        """
        trimmed = self.input.lstrip()
        match = _NUMBER_PATTERN.match(trimmed)
        if match is None:
            return None
        text = match.group(0)
        remaining = trimmed[match.end() :]
        return ParseResult.of(float(text), remaining)

    def parse_fraction(
        self,
    ) -> ParseResult[Fraction] | None:
        """解析分数或数值字面量为 Fraction。

        Parse a numeric literal as Fraction.

        Returns:
            解析结果或 None。/ Parse result or None.
        """
        trimmed = self.input.lstrip()
        if "/" in trimmed:
            parts = trimmed.split("/", 1)
            num_match = _NUMBER_PATTERN.match(parts[0])
            if num_match is None:
                return None
            den_part = parts[1].lstrip()
            den_match = _NUMBER_PATTERN.match(den_part)
            if den_match is None:
                return None
            frac = Fraction(
                int(num_match.group(0)),
                int(den_match.group(0)),
            )
            remaining = den_part[den_match.end() :]
            return ParseResult.of(frac, remaining)
        float_result = self.parse_float()
        if float_result is None:
            return None
        return ParseResult.of(
            Fraction(float_result.value).limit_denominator(),
            float_result.remaining,
        )
