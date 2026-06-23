"""Core variable module.

Provides variable types for optimization modeling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


@unique
class VariableType(Enum):
    """Variable type.

    变量类型。
    """

    CONTINUOUS = "continuous"
    INTEGER = "integer"
    BINARY = "binary"


@dataclass(frozen=True, slots=True)
class Variable:
    """Base variable class.

    变量基类。
    """

    name: str
    variable_type: VariableType = VariableType.CONTINUOUS
    lower_bound: float | None = None
    upper_bound: float | None = None

    def __repr__(self) -> str:
        """String representation."""
        bounds = ""
        if self.lower_bound is not None or self.upper_bound is not None:
            lb = str(self.lower_bound) if self.lower_bound is not None else "-inf"
            ub = str(self.upper_bound) if self.upper_bound is not None else "+inf"
            bounds = f" [{lb}, {ub}]"
        return f"{self.name}: {self.variable_type.value}{bounds}"


@dataclass(frozen=True, slots=True)
class LinearVariable(Variable):
    """Linear variable for linear programming.

    线性规划变量。
    """

    coefficient: float = 0.0

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.coefficient} * {self.name}"


@dataclass(frozen=True, slots=True)
class IntegerVariable(Variable):
    """Integer variable for integer programming.

    整数规划变量。
    """

    variable_type: VariableType = VariableType.INTEGER


@dataclass(frozen=True, slots=True)
class BinaryVariable(Variable):
    """Binary variable (0 or 1).

    二元变量。
    """

    variable_type: VariableType = VariableType.BINARY
    lower_bound: float | None = 0.0
    upper_bound: float | None = 1.0


def continuous(
    name: str, lower: float | None = None, upper: float | None = None
) -> Variable:
    """Create a continuous variable."""
    return Variable(name, VariableType.CONTINUOUS, lower, upper)


def integer(
    name: str, lower: float | None = None, upper: float | None = None
) -> IntegerVariable:
    """Create an integer variable."""
    return IntegerVariable(name, VariableType.INTEGER, lower, upper)


def binary(name: str) -> BinaryVariable:
    """Create a binary variable."""
    return BinaryVariable(name)
