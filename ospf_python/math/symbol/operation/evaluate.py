"""多项式求值。

Evaluate polynomial with variable bindings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol

T = TypeVar("T")
V = TypeVar("V")


@dataclass(frozen=True)
class PolynomialEvaluator(Generic[T, V]):
    """多项式求值器。

    Evaluates a polynomial given variable bindings.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def evaluate(
        self,
        polynomial: T,
        bindings: dict[str, V],
    ) -> V:
        """使用变量绑定求值多项式。

        Evaluate polynomial with variable bindings.

        Args:
            polynomial: 输入多项式。/ Input polynomial.
            bindings: 变量绑定映射。/ Variable bindings.

        Returns:
            求值结果。/ Evaluation result.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            # 将字符串键转换为 Symbol 键
            # Convert string keys to Symbol keys
            symbol_bindings: dict[Symbol, float] = {}
            for symbol in polynomial.symbols:
                name = symbol.display_name
                if name in bindings:
                    symbol_bindings[symbol] = float(bindings[name])  # type: ignore[arg-type]
                elif symbol.name in bindings:
                    symbol_bindings[symbol] = float(bindings[symbol.name])  # type: ignore[arg-type]
            return polynomial.evaluate(symbol_bindings)  # type: ignore[return-value]

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")
