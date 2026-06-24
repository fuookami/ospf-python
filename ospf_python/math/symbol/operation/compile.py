"""多项式编译。

Compile polynomial to executable form.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

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

        def evaluate(bindings: dict[str, V]) -> V:
            # TODO: 实现求值逻辑
            # TODO: implement evaluation logic
            raise NotImplementedError

        return CompiledPolynomial(
            evaluate=evaluate,
            source=polynomial,
        )
