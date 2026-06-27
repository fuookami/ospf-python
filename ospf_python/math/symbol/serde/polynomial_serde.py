"""多项式序列化与反序列化。

Polynomial serialization and deserialization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.math.symbol.parse.polynomial_parser import (
    PolynomialParser,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.monomial.canonical_monomial import (
        CanonicalMonomial,
    )
    from ospf_python.math.symbol.polynomial.canonical_polynomial import (
        CanonicalPolynomial,
    )


@dataclass(frozen=True)
class PolynomialSerde:
    """多项式序列化器。

    Handles serialization and deserialization of
    CanonicalPolynomial to and from string form.

    序列化格式示例 / Serialization format examples:
        "3.0 * x^2 + 2.0 * x + 1.0"
        "x + y"
        "5.0"
    """

    def serialize(self, poly: CanonicalPolynomial) -> str:
        """将多项式序列化为字符串。

        Serialize a polynomial to string.

        Args:
            poly: 待序列化的多项式。/
                Polynomial to serialize.

        Returns:
            序列化后的字符串。/ Serialized string.
        """
        if poly.is_zero:
            return "0"

        parts: list[str] = []
        for term in poly.terms:
            if term.is_constant:
                parts.append(_format_number(term.coefficient))
            else:
                parts.append(_format_monomial(term))
        return " + ".join(parts)

    def deserialize(self, text: str) -> CanonicalPolynomial:
        """从字符串反序列化多项式。

        Deserialize a polynomial from string.

        Args:
            text: 序列化的字符串。/ Serialized string.

        Returns:
            反序列化后的多项式。/
            Deserialized polynomial.
        """
        parser = PolynomialParser(expr=text)
        return parser.parse()


def _format_number(value: float) -> str:
    """格式化数值。

    Format a numeric value.

    Args:
        value: 数值。/ Numeric value.

    Returns:
        格式化后的字符串。/ Formatted string.
    """
    if value == int(value):
        return str(int(value))
    return str(value)


def _format_monomial(term: CanonicalMonomial) -> str:
    """格式化单项式。

    Format a monomial term.

    Args:
        term: 单项式。/ Monomial term.

    Returns:
        格式化后的字符串。/ Formatted string.
    """
    coeff = term.coefficient
    parts: list[str] = []

    # 处理系数 / Handle coefficient
    if coeff == 1.0:
        pass  # 省略系数 1 / Omit coefficient 1
    elif coeff == -1.0:
        parts.append("-")
    else:
        parts.append(_format_number(coeff))
        parts.append(" * ")

    # 处理变量幂次 / Handle variable powers
    var_parts: list[str] = []
    for symbol, power in term.powers.items():
        if power == 1:
            var_parts.append(str(symbol))
        else:
            var_parts.append(f"{symbol}^{power}")

    parts.append(" * ".join(var_parts))
    return "".join(parts)
