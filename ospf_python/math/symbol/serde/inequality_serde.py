"""不等式序列化与反序列化。

Inequality serialization and deserialization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.math.symbol.inequality.canonical_inequality import (
    CanonicalInequality,
)
from ospf_python.math.symbol.inequality.comparison import (
    Comparison,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.polynomial.canonical_polynomial import (
        CanonicalPolynomial,
    )
    from ospf_python.math.symbol.serde.polynomial_serde import (
        PolynomialSerde,
    )

    pass


# 比较符号到枚举的映射（按长度降序排列以优先匹配双字符符号） /
# Comparison symbol to enum mapping (descending length
# to match two-char symbols first)
_COMPARISON_SYMBOLS: list[tuple[str, Comparison]] = [
    ("<=", Comparison.LE),
    (">=", Comparison.GE),
    ("==", Comparison.EQ),
    ("!=", Comparison.NE),
    ("<", Comparison.LT),
    (">", Comparison.GT),
]


@dataclass(frozen=True)
class InequalitySerde:
    """不等式序列化器。

    Handles serialization and deserialization of
    CanonicalInequality to and from string form.

    序列化格式示例 / Serialization format examples:
        "x + 1 <= 3.0 * y"
        "2.0 * x >= 5.0"
    """

    polynomial_serde: PolynomialSerde

    def serialize(
        self,
        ineq: CanonicalInequality[CanonicalPolynomial],
    ) -> str:
        """将不等式序列化为字符串。

        Serialize an inequality to string.

        Args:
            ineq: 待序列化的不等式。/
                Inequality to serialize.

        Returns:
            序列化后的字符串。/ Serialized string.
        """
        left_str = self.polynomial_serde.serialize(ineq.left)
        right_str = self.polynomial_serde.serialize(ineq.right)
        symbol = ineq.comparison.symbol
        return f"{left_str} {symbol} {right_str}"

    def deserialize(
        self,
        text: str,
    ) -> CanonicalInequality[CanonicalPolynomial]:
        """从字符串反序列化不等式。

        Deserialize an inequality from string.

        Args:
            text: 序列化的字符串。/ Serialized string.

        Returns:
            反序列化后的不等式。/
            Deserialized inequality.
        """
        comp, left_text, right_text = _split_inequality(text)
        left = self.polynomial_serde.deserialize(left_text)
        right = self.polynomial_serde.deserialize(right_text)
        return CanonicalInequality(
            left=left,
            right=right,
            comparison=comp,
        )


def _split_inequality(
    text: str,
) -> tuple[Comparison, str, str]:
    """拆分不等式字符串。

    Split an inequality string into comparison
    operator and left/right parts.

    Args:
        text: 不等式字符串。/ Inequality string.

    Returns:
        (比较运算符, 左侧文本, 右侧文本)。/
        (comparison, left text, right text).
    """
    for symbol, comp in _COMPARISON_SYMBOLS:
        idx = text.find(symbol)
        if idx >= 0:
            left = text[:idx].strip()
            right = text[idx + len(symbol) :].strip()
            return comp, left, right

    # 回退：默认 <= / Fallback: default <=
    return Comparison.LE, text.strip(), "0"
