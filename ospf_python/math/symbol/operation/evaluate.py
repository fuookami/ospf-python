"""多项式求值。

Evaluate polynomial with variable bindings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

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
        # TODO: 实现求值逻辑
        # TODO: implement evaluation logic
        raise NotImplementedError
