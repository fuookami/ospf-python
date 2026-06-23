"""Symbolic expression DSL module.

Provides Expression base class with operator overloading and fluent builder.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class Expression(ABC):
    """Base class for symbolic expressions.

    符号表达式基类，支持运算符重载。
    """

    @abstractmethod
    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate expression.

        Args:
            values: Variable values.

        Returns:
            Evaluated value.
        """
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation.
        """
        ...

    @abstractmethod
    def __repr__(self) -> str:
        """String representation."""
        ...

    def __add__(self, other: Expression | float) -> AddExpr:
        """Add expressions."""
        right = other if isinstance(other, Expression) else Constant(other)
        return AddExpr(self, right)

    def __radd__(self, other: float) -> AddExpr:
        """Reverse add."""
        return AddExpr(Constant(other), self)

    def __sub__(self, other: Expression | float) -> SubExpr:
        """Subtract expressions."""
        right = other if isinstance(other, Expression) else Constant(other)
        return SubExpr(self, right)

    def __rsub__(self, other: float) -> SubExpr:
        """Reverse subtract."""
        return SubExpr(Constant(other), self)

    def __mul__(self, other: Expression | float) -> MulExpr:
        """Multiply expressions."""
        right = other if isinstance(other, Expression) else Constant(other)
        return MulExpr(self, right)

    def __rmul__(self, other: float) -> MulExpr:
        """Reverse multiply."""
        return MulExpr(Constant(other), self)

    def __truediv__(self, other: Expression | float) -> DivExpr:
        """Divide expressions."""
        right = other if isinstance(other, Expression) else Constant(other)
        return DivExpr(self, right)

    def __rtruediv__(self, other: float) -> DivExpr:
        """Reverse divide."""
        return DivExpr(Constant(other), self)

    def __pow__(self, other: Expression | float) -> PowExpr:
        """Power expressions."""
        right = other if isinstance(other, Expression) else Constant(other)
        return PowExpr(self, right)

    def __rpow__(self, other: float) -> PowExpr:
        """Reverse power."""
        return PowExpr(Constant(other), self)

    def __neg__(self) -> NegExpr:
        """Negate expression."""
        return NegExpr(self)

    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        if not isinstance(other, Expression):
            return NotImplemented
        return repr(self) == repr(other)

    def __hash__(self) -> int:
        """Hash."""
        return hash(repr(self))


@dataclass(frozen=True, slots=True)
class Constant(Expression):
    """Constant expression.

    常量表达式。
    """

    value: float

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate constant."""
        return self.value

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary."""
        return {"type": "Constant", "value": self.value}

    def __repr__(self) -> str:
        """String representation."""
        return str(self.value)


@dataclass(frozen=True, slots=True)
class Variable(Expression):
    """Variable expression.

    变量表达式。
    """

    name: str

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate variable."""
        return values[self.name]

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary."""
        return {"type": "Variable", "name": self.name}

    def __repr__(self) -> str:
        """String representation."""
        return self.name


@dataclass(frozen=True, slots=True)
class AddExpr(Expression):
    """Addition expression.

    加法表达式。
    """

    left: Expression
    right: Expression

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate addition."""
        return self.left.evaluate(values) + self.right.evaluate(values)

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary."""
        return {
            "type": "Add",
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"({self.left} + {self.right})"


@dataclass(frozen=True, slots=True)
class SubExpr(Expression):
    """Subtraction expression.

    减法表达式。
    """

    left: Expression
    right: Expression

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate subtraction."""
        return self.left.evaluate(values) - self.right.evaluate(values)

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary."""
        return {
            "type": "Sub",
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"({self.left} - {self.right})"


@dataclass(frozen=True, slots=True)
class MulExpr(Expression):
    """Multiplication expression.

    乘法表达式。
    """

    left: Expression
    right: Expression

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate multiplication."""
        return self.left.evaluate(values) * self.right.evaluate(values)

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary."""
        return {
            "type": "Mul",
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"({self.left} * {self.right})"


@dataclass(frozen=True, slots=True)
class DivExpr(Expression):
    """Division expression.

    除法表达式。
    """

    left: Expression
    right: Expression

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate division."""
        return self.left.evaluate(values) / self.right.evaluate(values)

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary."""
        return {
            "type": "Div",
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"({self.left} / {self.right})"


@dataclass(frozen=True, slots=True)
class PowExpr(Expression):
    """Power expression.

    幂表达式。
    """

    base: Expression
    exponent: Expression

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate power."""
        result: float = self.base.evaluate(values) ** self.exponent.evaluate(values)
        return result

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary."""
        return {
            "type": "Pow",
            "base": self.base.to_dict(),
            "exponent": self.exponent.to_dict(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"({self.base} ** {self.exponent})"


@dataclass(frozen=True, slots=True)
class NegExpr(Expression):
    """Negation expression.

    取反表达式。
    """

    operand: Expression

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate negation."""
        return -self.operand.evaluate(values)

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary."""
        return {
            "type": "Neg",
            "operand": self.operand.to_dict(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"(-{self.operand})"


@dataclass(frozen=True, slots=True)
class FunctionExpr(Expression):
    """Function call expression.

    函数调用表达式。
    """

    name: str
    args: tuple[Expression, ...]

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate function."""
        import math

        evaluated_args = [arg.evaluate(values) for arg in self.args]
        func = getattr(math, self.name, None)
        if func is None:
            raise ValueError(f"Unknown function: {self.name}")
        result: float = func(*evaluated_args)
        return result

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary."""
        return {
            "type": "Function",
            "name": self.name,
            "args": [arg.to_dict() for arg in self.args],
        }

    def __repr__(self) -> str:
        """String representation."""
        args_str = ", ".join(repr(arg) for arg in self.args)
        return f"{self.name}({args_str})"


def var(name: str) -> Variable:
    """Create a variable expression.

    Args:
        name: Variable name.

    Returns:
        Variable expression.
    """
    return Variable(name)


def const(value: float) -> Constant:
    """Create a constant expression.

    Args:
        value: Constant value.

    Returns:
        Constant expression.
    """
    return Constant(value)


def func(name: str, *args: Expression | float) -> FunctionExpr:
    """Create a function expression.

    Args:
        name: Function name.
        *args: Arguments.

    Returns:
        Function expression.
    """
    expr_args = tuple(
        arg if isinstance(arg, Expression) else Constant(arg) for arg in args
    )
    return FunctionExpr(name, expr_args)


def sin(expr: Expression | float) -> FunctionExpr:
    """Create sin expression."""
    return func("sin", expr)


def cos(expr: Expression | float) -> FunctionExpr:
    """Create cos expression."""
    return func("cos", expr)


def tan(expr: Expression | float) -> FunctionExpr:
    """Create tan expression."""
    return func("tan", expr)


def exp(expr: Expression | float) -> FunctionExpr:
    """Create exp expression."""
    return func("exp", expr)


def log(expr: Expression | float) -> FunctionExpr:
    """Create log expression."""
    return func("log", expr)


def sqrt(expr: Expression | float) -> FunctionExpr:
    """Create sqrt expression."""
    return func("sqrt", expr)
