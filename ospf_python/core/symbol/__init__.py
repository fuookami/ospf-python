"""Core symbol module.

Provides symbolic functions and flatten operations for optimization modeling.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar

from ospf_python.core.token import Token, variable_token

T = TypeVar("T")


class SymbolicFunction(ABC):
    """Base class for symbolic functions.

    符号函数基类。
    """

    @abstractmethod
    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate the function."""
        ...

    @abstractmethod
    def flatten(self) -> list[Token]:
        """Flatten to token sequence."""
        ...

    @abstractmethod
    def __repr__(self) -> str:
        """String representation."""
        ...

    def __add__(self, other: SymbolicFunction) -> AddSymbol:
        """Add two symbolic functions."""
        return AddSymbol(self, other)

    def __radd__(self, other: SymbolicFunction) -> AddSymbol:
        """Reverse add."""
        return AddSymbol(other, self)

    def __sub__(self, other: SymbolicFunction) -> SubSymbol:
        """Subtract two symbolic functions."""
        return SubSymbol(self, other)

    def __rsub__(self, other: SymbolicFunction) -> SubSymbol:
        """Reverse subtract."""
        return SubSymbol(other, self)

    def __mul__(self, other: SymbolicFunction) -> MulSymbol:
        """Multiply two symbolic functions."""
        return MulSymbol(self, other)

    def __rmul__(self, other: SymbolicFunction) -> MulSymbol:
        """Reverse multiply."""
        return MulSymbol(other, self)

    def __truediv__(self, other: SymbolicFunction) -> DivSymbol:
        """Divide two symbolic functions."""
        return DivSymbol(self, other)

    def __rtruediv__(self, other: SymbolicFunction) -> DivSymbol:
        """Reverse divide."""
        return DivSymbol(other, self)

    def __neg__(self) -> NegSymbol:
        """Negate symbolic function."""
        return NegSymbol(self)


@dataclass(frozen=True, slots=True)
class VariableSymbol(SymbolicFunction):
    """Variable symbol.

    变量符号。
    """

    name: str

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate variable."""
        return values[self.name]

    def flatten(self) -> list[Token]:
        """Flatten to token sequence."""
        return [variable_token(self.name)]

    def __repr__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class ConstantSymbol(SymbolicFunction):
    """Constant symbol.

    常量符号。
    """

    value: float

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate constant."""
        return self.value

    def flatten(self) -> list[Token]:
        """Flatten to token sequence."""
        return []  # Constants don't produce tokens

    def __repr__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class AddSymbol(SymbolicFunction):
    """Addition symbol.

    加法符号。
    """

    left: SymbolicFunction
    right: SymbolicFunction

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate addition."""
        return self.left.evaluate(values) + self.right.evaluate(values)

    def flatten(self) -> list[Token]:
        """Flatten to token sequence."""
        return self.left.flatten() + self.right.flatten()

    def __repr__(self) -> str:
        return f"({self.left} + {self.right})"


@dataclass(frozen=True, slots=True)
class MulSymbol(SymbolicFunction):
    """Multiplication symbol.

    乘法符号。
    """

    left: SymbolicFunction
    right: SymbolicFunction

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate multiplication."""
        return self.left.evaluate(values) * self.right.evaluate(values)

    def flatten(self) -> list[Token]:
        """Flatten to token sequence."""
        return self.left.flatten() + self.right.flatten()

    def __repr__(self) -> str:
        return f"({self.left} * {self.right})"


@dataclass(frozen=True, slots=True)
class SubSymbol(SymbolicFunction):
    """Subtraction symbol.

    减法符号。
    """

    left: SymbolicFunction
    right: SymbolicFunction

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate subtraction."""
        return self.left.evaluate(values) - self.right.evaluate(values)

    def flatten(self) -> list[Token]:
        """Flatten to token sequence."""
        return self.left.flatten() + self.right.flatten()

    def __repr__(self) -> str:
        return f"({self.left} - {self.right})"


@dataclass(frozen=True, slots=True)
class DivSymbol(SymbolicFunction):
    """Division symbol.

    除法符号。
    """

    left: SymbolicFunction
    right: SymbolicFunction

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate division."""
        return self.left.evaluate(values) / self.right.evaluate(values)

    def flatten(self) -> list[Token]:
        """Flatten to token sequence."""
        return self.left.flatten() + self.right.flatten()

    def __repr__(self) -> str:
        return f"({self.left} / {self.right})"


@dataclass(frozen=True, slots=True)
class NegSymbol(SymbolicFunction):
    """Negation symbol.

    取反符号。
    """

    operand: SymbolicFunction

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate negation."""
        return -self.operand.evaluate(values)

    def flatten(self) -> list[Token]:
        """Flatten to token sequence."""
        return self.operand.flatten()

    def __repr__(self) -> str:
        return f"(-{self.operand})"


@dataclass(frozen=True, slots=True)
class LinearTerm(SymbolicFunction):
    """Linear term: coefficient * variable.

    线性项：系数 * 变量。
    """

    coefficient: float
    variable: str

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate linear term."""
        return self.coefficient * values[self.variable]

    def flatten(self) -> list[Token]:
        """Flatten to token sequence."""
        return [variable_token(self.variable)]

    def __repr__(self) -> str:
        if self.coefficient == 1.0:
            return self.variable
        return f"{self.coefficient} * {self.variable}"


@dataclass(frozen=True, slots=True)
class LinearExpression(SymbolicFunction):
    """Linear expression: sum of linear terms + constant.

    线性表达式：线性项之和 + 常数。
    """

    terms: tuple[LinearTerm, ...]
    constant: float = 0.0

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate linear expression."""
        return sum(t.evaluate(values) for t in self.terms) + self.constant

    def flatten(self) -> list[Token]:
        """Flatten to token sequence."""
        tokens = []
        for term in self.terms:
            tokens.extend(term.flatten())
        return tokens

    def __repr__(self) -> str:
        parts = [repr(t) for t in self.terms]
        if self.constant != 0:
            parts.append(str(self.constant))
        return " + ".join(parts) if parts else "0"


def flatten(expr: SymbolicFunction) -> list[Token]:
    """Flatten a symbolic expression to token sequence.

    Args:
        expr: Symbolic expression.

    Returns:
        List of tokens.
    """
    return expr.flatten()


def var(name: str) -> VariableSymbol:
    """Create a variable symbol."""
    return VariableSymbol(name)


def const(value: float) -> ConstantSymbol:
    """Create a constant symbol."""
    return ConstantSymbol(value)


def linear_term(coefficient: float, variable: str) -> LinearTerm:
    """Create a linear term."""
    return LinearTerm(coefficient, variable)


def linear_expr(terms: list[LinearTerm], constant: float = 0.0) -> LinearExpression:
    """Create a linear expression."""
    return LinearExpression(tuple(terms), constant)
