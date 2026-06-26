"""多项式合并热路径基准 / Polynomial combine hot path benchmark.

对齐 Kotlin SymbolCombineBenchmark: 多项式创建与合并性能。
Aligned to Kotlin SymbolCombineBenchmark: polynomial creation and
combination performance.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pytest

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)
from ospf_python.math.symbol.symbol import Symbol

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


def _make_symbols(n: int) -> list[Symbol]:
    """创建 n 个符号 / Create n symbols."""
    return [Symbol.create(f"x_{i}", index=i) for i in range(n)]


def _make_random_monomial(
    symbols: list[Symbol],
    max_terms: int,
) -> CanonicalMonomial:
    """创建随机单项式 / Create random monomial.

    Args:
        symbols: 可用符号 / Available symbols.
        max_terms: 最大符号数 / Max symbol count.

    Returns:
        随机单项式 / Random monomial.
    """
    n = random.randint(0, min(max_terms, len(symbols)))
    chosen = random.sample(symbols, n) if n > 0 else []
    coeff = random.uniform(0.1, 10.0)
    powers: dict[Symbol, int] = {s: random.randint(1, 3) for s in chosen}
    return CanonicalMonomial(coefficient=coeff, powers=powers)


def _make_random_polynomial(
    symbols: list[Symbol],
    n_terms: int,
    max_symbol_terms: int,
) -> CanonicalPolynomial:
    """创建随机多项式 / Create random polynomial.

    Args:
        symbols: 可用符号 / Available symbols.
        n_terms: 项数 / Term count.
        max_symbol_terms: 单项式最大符号数 / Max symbols per monomial.

    Returns:
        随机多项式 / Random polynomial.
    """
    terms = [_make_random_monomial(symbols, max_symbol_terms) for _ in range(n_terms)]
    return CanonicalPolynomial(terms=terms)


@pytest.mark.benchmark
class TestSymbolCombine:
    """多项式合并热路径基准。

    Polynomial combine hot path benchmarks.
    """

    def test_polynomial_addition(
        self,
        benchmark: BenchmarkFixture,
        symbol_dataset: dict[str, int],
    ) -> None:
        """多项式加法热路径 / Polynomial addition hot path.

        对齐 Kotlin SymbolCombineBenchmark.polynomialAddition。
        Aligned to Kotlin SymbolCombineBenchmark.polynomialAddition.

        Args:
            benchmark: pytest-benchmark fixture.
            symbol_dataset: 数据集规模 / Dataset scale.
        """
        n_symbols = symbol_dataset["symbols"]
        n_terms = symbol_dataset["terms"]
        n_polys = symbol_dataset["polynomials"]

        symbols = _make_symbols(n_symbols)
        polys = [
            _make_random_polynomial(symbols, n_terms, min(5, n_symbols))
            for _ in range(n_polys)
        ]

        def _run() -> CanonicalPolynomial:
            result = CanonicalPolynomial.zero()
            for p in polys:
                result = result + p
            return result

        benchmark(_run)

    def test_polynomial_evaluation(
        self,
        benchmark: BenchmarkFixture,
        symbol_dataset: dict[str, int],
    ) -> None:
        """多项式求值热路径 / Polynomial evaluation hot path.

        对齐 Kotlin SymbolCombineBenchmark.polynomialEvaluation。
        Aligned to Kotlin SymbolCombineBenchmark.polynomialEvaluation.

        Args:
            benchmark: pytest-benchmark fixture.
            symbol_dataset: 数据集规模 / Dataset scale.
        """
        n_symbols = symbol_dataset["symbols"]
        n_terms = symbol_dataset["terms"]

        symbols = _make_symbols(n_symbols)
        poly = _make_random_polynomial(symbols, n_terms, min(5, n_symbols))
        bindings = {s: 1.5 for s in symbols}

        def _run() -> float:
            return poly.evaluate(bindings)

        benchmark(_run)

    def test_monomial_multiplication(
        self,
        benchmark: BenchmarkFixture,
        symbol_dataset: dict[str, int],
    ) -> None:
        """单项式乘法热路径 / Monomial multiplication hot path.

        对齐 Kotlin SymbolCombineBenchmark.monomialMultiplication。
        Aligned to Kotlin SymbolCombineBenchmark.monomialMultiplication.

        Args:
            benchmark: pytest-benchmark fixture.
            symbol_dataset: 数据集规模 / Dataset scale.
        """
        n_symbols = symbol_dataset["symbols"]
        n_polys = symbol_dataset["polynomials"]

        symbols = _make_symbols(n_symbols)
        monomials = [
            _make_random_monomial(symbols, min(3, n_symbols)) for _ in range(n_polys)
        ]

        def _run() -> CanonicalMonomial:
            result = CanonicalMonomial.constant(1.0)
            for m in monomials:
                result = result * m
            return result

        benchmark(_run)
