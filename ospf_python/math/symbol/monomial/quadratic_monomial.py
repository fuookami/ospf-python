"""二次单项式。

Quadratic monomial.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol


@dataclass(frozen=True)
class QuadraticMonomial:
    """二次单项式：两个符号与系数的乘积。

    Quadratic monomial: product of two symbols and a coefficient.

    表达形式: coefficient * lhs * rhs
    Expression form: coefficient * lhs * rhs

    Attributes:
        coefficient: 系数。/ Coefficient.
        lhs: 左符号。/ Left symbol.
        rhs: 右符号。/ Right symbol.
    """

    coefficient: float
    lhs: Symbol
    rhs: Symbol

    @staticmethod
    def create(
        *,
        coefficient: float = 1.0,
        lhs: Symbol,
        rhs: Symbol,
    ) -> QuadraticMonomial:
        """创建二次单项式。/ Create a quadratic monomial.

        Args:
            coefficient: 系数，默认 1.0。/ Coefficient, defaults to 1.0.
            lhs: 左符号。/ Left symbol.
            rhs: 右符号。/ Right symbol.

        Returns:
            二次单项式实例。/ Quadratic monomial instance.
        """
        return QuadraticMonomial(
            coefficient=coefficient,
            lhs=lhs,
            rhs=rhs,
        )

    @property
    def degree(self) -> int:
        """获取次数，二次单项式始终为 2。/ Get degree, always 2 for quadratic."""
        return 2

    @property
    def is_square(self) -> bool:
        """是否为平方项（两个符号相同）。/ Whether it is a square term."""
        return self.lhs == self.rhs

    @property
    def symbols(self) -> list[Symbol]:
        """获取符号列表。/ Get symbol list.

        Returns:
            去重后的符号列表。/ Deduplicated symbol list.
        """
        if self.lhs == self.rhs:
            return [self.lhs]
        return [self.lhs, self.rhs]

    def evaluate(self, lhs_value: float, rhs_value: float) -> float:
        """在给定值下求值。/ Evaluate at given values.

        Args:
            lhs_value: 左符号绑定值。/ Left symbol binding value.
            rhs_value: 右符号绑定值。/ Right symbol binding value.

        Returns:
            求值结果。/ Evaluation result.
        """
        return self.coefficient * lhs_value * rhs_value

    def negate(self) -> QuadraticMonomial:
        """取反。/ Negate.

        Returns:
            系数取反的新单项式。/ New monomial with negated coefficient.
        """
        return QuadraticMonomial(
            coefficient=-self.coefficient,
            lhs=self.lhs,
            rhs=self.rhs,
        )

    def scale(self, factor: float) -> QuadraticMonomial:
        """缩放。/ Scale.

        Args:
            factor: 缩放因子。/ Scale factor.

        Returns:
            缩放后的新单项式。/ New scaled monomial.
        """
        return QuadraticMonomial(
            coefficient=self.coefficient * factor,
            lhs=self.lhs,
            rhs=self.rhs,
        )

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        if self.coefficient == 1.0:
            return f"{self.lhs} * {self.rhs}"
        if self.coefficient == -1.0:
            return f"-{self.lhs} * {self.rhs}"
        return f"{self.coefficient} * {self.lhs} * {self.rhs}"
