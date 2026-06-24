"""标准单项式。

Canonical monomial.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol


@dataclass(frozen=True)
class CanonicalMonomial:
    """标准单项式：系数与符号幂次的乘积。

    Canonical monomial: product of coefficient and symbol powers.

    表达形式: coefficient * x1^p1 * x2^p2 * ...
    Expression form: coefficient * x1^p1 * x2^p2 * ...

    Attributes:
        coefficient: 系数。/ Coefficient.
        powers: 符号到幂次的映射。/ Symbol-to-power mapping.
    """

    coefficient: float
    powers: dict[Symbol, int]

    @staticmethod
    def constant(value: float) -> CanonicalMonomial:
        """创建常数单项式。/ Create a constant monomial.

        Args:
            value: 常数值。/ Constant value.

        Returns:
            常数单项式。/ Constant monomial.
        """
        return CanonicalMonomial(coefficient=value, powers={})

    @staticmethod
    def single(
        symbol: Symbol,
        coefficient: float = 1.0,
        power: int = 1,
    ) -> CanonicalMonomial:
        """创建单符号单项式。/ Create a single-symbol monomial.

        Args:
            symbol: 符号。/ The symbol.
            coefficient: 系数，默认 1.0。/ Coefficient, defaults to 1.0.
            power: 幂次，默认 1。/ Power, defaults to 1.

        Returns:
            单符号单项式。/ Single-symbol monomial.
        """
        return CanonicalMonomial(
            coefficient=coefficient,
            powers={symbol: power},
        )

    @property
    def degree(self) -> int:
        """获取总次数。/ Get total degree.

        Returns:
            所有符号幂次之和。/ Sum of all symbol powers.
        """
        return sum(self.powers.values())

    @property
    def is_constant(self) -> bool:
        """是否为常数项。/ Whether it is a constant term."""
        return len(self.powers) == 0

    @property
    def symbols(self) -> list[Symbol]:
        """获取所有符号。/ Get all symbols.

        Returns:
            符号列表。/ List of symbols.
        """
        return list(self.powers.keys())

    def evaluate(self, bindings: dict[Symbol, float]) -> float:
        """在给定绑定下求值。/ Evaluate under given bindings.

        Args:
            bindings: 符号到值的绑定。/ Symbol-to-value bindings.

        Returns:
            求值结果。/ Evaluation result.
        """
        result = self.coefficient
        for symbol, power in self.powers.items():
            value = bindings.get(symbol, 0.0)
            result *= value**power
        return result

    def __mul__(self, other: CanonicalMonomial) -> CanonicalMonomial:
        """两个单项式相乘。/ Multiply two monomials.

        Args:
            other: 另一个单项式。/ Another monomial.

        Returns:
            相乘结果。/ Multiplication result.
        """
        new_coeff = self.coefficient * other.coefficient
        new_powers: dict[Symbol, int] = dict(self.powers)
        for sym, pow in other.powers.items():
            new_powers[sym] = new_powers.get(sym, 0) + pow
        return CanonicalMonomial(coefficient=new_coeff, powers=new_powers)

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        if self.is_constant:
            return str(self.coefficient)
        parts: list[str] = []
        if self.coefficient != 1.0:
            parts.append(str(self.coefficient))
        for symbol, power in self.powers.items():
            if power == 1:
                parts.append(str(symbol))
            else:
                parts.append(f"{symbol}^{power}")
        return " * ".join(parts)
