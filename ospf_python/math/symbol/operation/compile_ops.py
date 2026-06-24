"""编译运算操作。

Compilation operations for polynomials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ospf_python.math.symbol.operation.compile import (
        PolynomialCompiler,
    )

T = TypeVar("T")
V = TypeVar("V")


@dataclass(frozen=True)
class CompileOps(Generic[T, V]):
    """编译运算操作集。

    Collection of compilation operations.

    Attributes:
        compiler: 多项式编译器。/ Polynomial compiler.
    """

    compiler: PolynomialCompiler[T, V]

    def compile_and_evaluate(
        self,
        polynomial: T,
        bindings: dict[str, V],
    ) -> V:
        """编译并立即求值。

        Compile and evaluate immediately.

        Args:
            polynomial: 输入多项式。/ Input polynomial.
            bindings: 变量绑定。/ Variable bindings.

        Returns:
            求值结果。/ Evaluation result.
        """
        compiled = self.compiler.compile(polynomial)
        return compiled.evaluate(bindings)
