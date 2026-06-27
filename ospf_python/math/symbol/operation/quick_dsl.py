"""快速 DSL。

Quick DSL for building polynomial expressions.
"""

from __future__ import annotations

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

# 全局符号索引计数器 / Global symbol index counter
_symbol_counter: int = 0


def _reset_counter() -> None:
    """重置符号计数器。/ Reset symbol counter."""
    global _symbol_counter
    _symbol_counter = 0


def _next_symbol(name: str) -> Symbol:
    """创建下一个符号。/ Create next symbol.

    Args:
        name: 符号名称。/ Symbol name.

    Returns:
        新符号。/ New symbol.
    """
    global _symbol_counter
    symbol = Symbol.create(name=name, index=_symbol_counter)
    _symbol_counter += 1
    return symbol


def _multiply_polynomials(
    left: CanonicalPolynomial,
    right: CanonicalPolynomial,
) -> CanonicalPolynomial:
    """多项式乘法（分配律）。

    Polynomial multiplication via distributive property.

    Args:
        left: 左多项式。/ Left polynomial.
        right: 右多项式。/ Right polynomial.

    Returns:
        乘积多项式。/ Product polynomial.
    """
    result_terms: list[CanonicalMonomial] = []
    for lt in left.terms:
        for rt in right.terms:
            result_terms.append(lt * rt)
    return CanonicalPolynomial(terms=result_terms)


@dataclass(frozen=True)
class QuickDsl(Generic[T]):
    """快速 DSL 入口。

    Quick DSL entry point for building polynomial
    expressions with concise syntax.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def var(self, name: str) -> T:
        """创建变量项。/ Create variable term.

        Args:
            name: 变量名。/ Variable name.

        Returns:
            变量多项式。/ Variable polynomial.
        """
        if self.factory is CanonicalPolynomial:
            symbol = _next_symbol(name)
            return CanonicalPolynomial(
                terms=[CanonicalMonomial.single(symbol)]
            )  # type: ignore[return-value]
        raise TypeError(f"Unsupported factory type: {self.factory}")

    def constant(self, value: float) -> T:
        """创建常数项。/ Create constant term.

        Args:
            value: 常数值。/ Constant value.

        Returns:
            常数多项式。/ Constant polynomial.
        """
        if self.factory is CanonicalPolynomial:
            return CanonicalPolynomial.constant(value)  # type: ignore[return-value]
        raise TypeError(f"Unsupported factory type: {self.factory}")

    def sum(self, *polynomials: T) -> T:
        """多项式求和。/ Sum polynomials.

        Args:
            *polynomials: 多项式序列。/ Polynomial sequence.

        Returns:
            求和结果。/ Sum result.
        """
        if not polynomials:
            if self.factory is CanonicalPolynomial:
                return CanonicalPolynomial.zero()  # type: ignore[return-value]
            raise TypeError(f"Unsupported factory type: {self.factory}")

        if self.factory is CanonicalPolynomial:
            result = CanonicalPolynomial.zero()
            for poly in polynomials:
                result = result + poly  # type: ignore[operator]
            return result  # type: ignore[return-value]
        raise TypeError(f"Unsupported factory type: {self.factory}")

    def product(self, *polynomials: T) -> T:
        """多项式求积。/ Product of polynomials.

        Args:
            *polynomials: 多项式序列。/ Polynomial sequence.

        Returns:
            求积结果。/ Product result.
        """
        if not polynomials:
            if self.factory is CanonicalPolynomial:
                return CanonicalPolynomial.constant(1.0)  # type: ignore[return-value]
            raise TypeError(f"Unsupported factory type: {self.factory}")

        if self.factory is CanonicalPolynomial:
            result = CanonicalPolynomial.constant(1.0)
            for poly in polynomials:
                result = _multiply_polynomials(result, poly)  # type: ignore[arg-type]
            return result  # type: ignore[return-value]
        raise TypeError(f"Unsupported factory type: {self.factory}")
