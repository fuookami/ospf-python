"""多项式字符串解析。

Parse polynomial from string representation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Generic, TypeVar

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)
from ospf_python.math.symbol.symbol import Symbol

T = TypeVar("T")

# 符号索引计数器 / Symbol index counter
_parse_counter: int = 0


def _next_parse_symbol(name: str) -> Symbol:
    """创建解析用符号。/ Create symbol for parsing."""
    global _parse_counter
    symbol = Symbol.create(name=name, index=_parse_counter)
    _parse_counter += 1
    return symbol


# 匹配单项式：[系数][*]变量[^幂次]
# Match monomial: [coeff][*]variable[^power]
_MONOMIAL_RE = re.compile(
    r"([+-]?\s*\d+(?:\.\d+)?)\s*\*?\s*(\w+)(?:\s*\^\s*(\d+))?",
)
# 匹配纯变量项：变量[^幂次]
# Match pure variable term: variable[^power]
_VAR_RE = re.compile(
    r"([+-]?)\s*(\w+)(?:\s*\^\s*(\d+))?",
)


@dataclass(frozen=True)
class PolynomialStringParser(Generic[T]):
    """多项式字符串解析器。

    Parses polynomial expressions from string form.

    支持格式：
    - "x + 1"
    - "2*x + 3*y - 5"
    - "x^2 + 2*x*y + y^2"

    Supported formats:
    - "x + 1"
    - "2*x + 3*y - 5"
    - "x^2 + 2*x*y + y^2"

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def parse(self, input: str) -> T | None:
        """从字符串解析多项式。

        Parse polynomial from string.

        Args:
            input: 多项式字符串。/ Polynomial string.

        Returns:
            解析结果或 None。/ Parsed polynomial or None.
        """
        if self.factory is CanonicalPolynomial:
            return self._parse_canonical(input)  # type: ignore[return-value]
        raise TypeError(f"Unsupported factory type: {self.factory}")

    def _parse_canonical(self, input: str) -> CanonicalPolynomial | None:
        """解析为 CanonicalPolynomial。

        Parse to CanonicalPolynomial.

        Args:
            input: 多项式字符串。/ Polynomial string.

        Returns:
            解析结果或 None。/ Parsed polynomial or None.
        """
        global _parse_counter
        _parse_counter = 0  # 重置计数器 / Reset counter

        trimmed = input.strip()
        if not trimmed:
            return None  # justified: empty input cannot be parsed

        # 符号缓存：同名变量共享同一 Symbol
        # Symbol cache: same-name variables share same Symbol
        symbol_cache: dict[str, Symbol] = {}

        terms: list[CanonicalMonomial] = []
        # 按加减号分割项（保留符号）
        # Split by +/- signs (keeping signs)
        # 简单策略：逐项解析
        # Simple strategy: parse term by term
        remaining = trimmed

        # 处理开头的隐式正号
        # Handle leading implicit positive sign
        if remaining and remaining[0] not in "+-":
            remaining = "+" + remaining

        # 匹配每个项
        # Match each term
        term_pattern = re.compile(
            r"([+-])\s*(\d+(?:\.\d+)?)?\s*\*?\s*(\w+)?(?:\s*\^\s*(\d+))?",
        )

        pos = 0
        while pos < len(remaining):
            match = term_pattern.match(remaining, pos)
            if not match:
                break

            sign_str = match.group(1)
            coeff_str = match.group(2)
            var_str = match.group(3)
            power_str = match.group(4)

            # 计算系数 / Compute coefficient
            coeff = 1.0
            if coeff_str:
                coeff = float(coeff_str)
            if sign_str == "-":
                coeff = -coeff

            # 构建幂次映射 / Build powers mapping
            powers: dict[Symbol, int] = {}
            if var_str:
                if var_str not in symbol_cache:
                    symbol_cache[var_str] = _next_parse_symbol(var_str)
                sym = symbol_cache[var_str]
                power = int(power_str) if power_str else 1
                powers[sym] = power

            terms.append(CanonicalMonomial(coefficient=coeff, powers=powers))
            pos = match.end()

            # 跳过空白和连接符 / Skip whitespace and connectors
            while pos < len(remaining) and remaining[pos] in " +-*":
                pos += 1

        # 处理纯常数项（如 "+ 5" 或 "- 5"）
        # Handle pure constant terms
        if not terms:
            # 尝试解析为纯数字 / Try parsing as pure number
            try:
                val = float(trimmed)
                return CanonicalPolynomial.constant(val)
            except ValueError:
                return None  # justified: input is not a valid number

        return CanonicalPolynomial(terms=terms)
