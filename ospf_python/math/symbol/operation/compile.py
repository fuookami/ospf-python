"""多项式编译。

Compile polynomial to executable form.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Generic, TypeVar

from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol

T = TypeVar("T")
V = TypeVar("V")


@dataclass(frozen=True)
class CompiledPolynomial(Generic[T, V]):
    """编译后的多项式，可直接求值。

    Compiled polynomial that can be evaluated directly.

    Attributes:
        evaluate: 求值函数。/ Evaluation function.
        source: 源多项式。/ Source polynomial.
    """

    evaluate: Callable[[dict[str, V]], V]
    source: T


@dataclass(frozen=True)
class PolynomialCompiler(Generic[T, V]):
    """多项式编译器。

    Compiles a polynomial into an executable form for
    efficient repeated evaluation.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def compile(
        self,
        polynomial: T,
    ) -> CompiledPolynomial[T, V]:
        """编译多项式为可执行形式。

        Compile polynomial to executable form.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            编译后的多项式。/ Compiled polynomial.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            # 预先解析符号映射，避免重复查找
            # Pre-resolve symbol mapping to avoid repeated lookups
            symbols = polynomial.symbols

            def evaluate(bindings: dict[str, V]) -> V:
                symbol_bindings: dict[Symbol, float] = {}
                for symbol in symbols:
                    name = symbol.display_name
                    if name in bindings:
                        symbol_bindings[symbol] = float(bindings[name])  # type: ignore[arg-type]
                    elif symbol.name in bindings:
                        symbol_bindings[symbol] = float(bindings[symbol.name])  # type: ignore[arg-type]
                return polynomial.evaluate(symbol_bindings)  # type: ignore[return-value]

            return CompiledPolynomial(
                evaluate=evaluate,
                source=polynomial,
            )

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")
