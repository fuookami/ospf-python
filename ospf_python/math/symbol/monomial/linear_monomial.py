"""线性单项式。

Linear monomial.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol


@dataclass(frozen=True)
class LinearMonomial:
    """线性单项式：单个符号乘以系数。

    Linear monomial: single symbol multiplied by a coefficient.

    表达形式: coefficient * symbol
    Expression form: coefficient * symbol

    Attributes:
        coefficient: 系数。/ Coefficient.
        symbol: 符号。/ Symbol.
    """

    coefficient: float
    symbol: Symbol

    @staticmethod
    def create(
        symbol: Symbol,
        coefficient: float = 1.0,
    ) -> LinearMonomial:
        """创建线性单项式。/ Create a linear monomial.

        Args:
            symbol: 符号。/ The symbol.
            coefficient: 系数，默认 1.0。/ Coefficient, defaults to 1.0.

        Returns:
            线性单项式实例。/ Linear monomial instance.
        """
        return LinearMonomial(coefficient=coefficient, symbol=symbol)

    @property
    def degree(self) -> int:
        """获取次数，线性单项式始终为 1。/ Get degree, always 1 for linear."""
        return 1

    @property
    def name(self) -> str:
        """获取符号名称。/ Get symbol name."""
        return self.symbol.name

    @property
    def index(self) -> int:
        """获取符号索引。/ Get symbol index."""
        return self.symbol.index

    def evaluate(self, value: float) -> float:
        """在给定值下求值。/ Evaluate at given value.

        Args:
            value: 符号绑定值。/ Symbol binding value.

        Returns:
            coefficient * value 的结果。/ Result of coefficient * value.
        """
        return self.coefficient * value

    def negate(self) -> LinearMonomial:
        """取反。/ Negate.

        Returns:
            系数取反的新单项式。/ New monomial with negated coefficient.
        """
        return LinearMonomial(
            coefficient=-self.coefficient,
            symbol=self.symbol,
        )

    def scale(self, factor: float) -> LinearMonomial:
        """缩放。/ Scale.

        Args:
            factor: 缩放因子。/ Scale factor.

        Returns:
            缩放后的新单项式。/ New scaled monomial.
        """
        return LinearMonomial(
            coefficient=self.coefficient * factor,
            symbol=self.symbol,
        )

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        if self.coefficient == 1.0:
            return str(self.symbol)
        if self.coefficient == -1.0:
            return f"-{self.symbol}"
        return f"{self.coefficient} * {self.symbol}"
