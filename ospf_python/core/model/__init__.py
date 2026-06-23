"""Core model module.

Provides MetaModel for optimization modeling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
from typing import TYPE_CHECKING, TypeVar

from ospf_python.utils.error import ErrorCode
from ospf_python.utils.result import Result, failed, ok

if TYPE_CHECKING:
    from ospf_python.core.symbol import SymbolicFunction
    from ospf_python.core.variable import Variable

V = TypeVar("V")


@unique
class ObjectiveType(Enum):
    """Objective type.

    目标类型。
    """

    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


@unique
class ConstraintType(Enum):
    """Constraint type.

    约束类型。
    """

    LE = "<="
    GE = ">="
    EQ = "=="


@dataclass(frozen=True, slots=True)
class Constraint:
    """Constraint.

    约束。
    """

    name: str
    expression: SymbolicFunction
    constraint_type: ConstraintType
    rhs: float

    def __repr__(self) -> str:
        return f"{self.name}: {self.expression} {self.constraint_type.value} {self.rhs}"


@dataclass(frozen=True, slots=True)
class Objective:
    """Objective.

    目标。
    """

    name: str
    expression: SymbolicFunction
    objective_type: ObjectiveType

    def __repr__(self) -> str:
        return f"{self.name}: {self.objective_type.value} {self.expression}"


@dataclass(frozen=True, slots=True)
class Solution:
    """Solution.

    解。
    """

    objective_value: float
    variable_values: dict[str, float]
    status: str = "optimal"

    def __repr__(self) -> str:
        return f"Solution(status={self.status}, obj={self.objective_value})"


class MetaModel:
    """MetaModel for optimization.

    优化 MetaModel。
    """

    def __init__(self, name: str) -> None:
        """Initialize MetaModel.

        Args:
            name: Model name.
        """
        self._name = name
        self._variables: dict[str, Variable] = {}
        self._constraints: list[Constraint] = []
        self._objective: Objective | None = None

    @property
    def name(self) -> str:
        """Get model name."""
        return self._name

    def add_variable(self, variable: Variable) -> Variable:
        """Add a variable to the model.

        Args:
            variable: Variable to add.

        Returns:
            The added variable.
        """
        self._variables[variable.name] = variable
        return variable

    def add_constraint(
        self,
        name: str,
        expression: SymbolicFunction,
        constraint_type: ConstraintType,
        rhs: float,
    ) -> Constraint:
        """Add a constraint to the model.

        Args:
            name: Constraint name.
            expression: Constraint expression.
            constraint_type: Constraint type.
            rhs: Right-hand side value.

        Returns:
            The added constraint.
        """
        constraint = Constraint(name, expression, constraint_type, rhs)
        self._constraints.append(constraint)
        return constraint

    def set_objective(
        self,
        name: str,
        expression: SymbolicFunction,
        objective_type: ObjectiveType,
    ) -> Objective:
        """Set the objective.

        Args:
            name: Objective name.
            expression: Objective expression.
            objective_type: Objective type.

        Returns:
            The objective.
        """
        objective = Objective(name, expression, objective_type)
        self._objective = objective
        return objective

    def get_variable(self, name: str) -> Result[Variable]:
        """Get a variable by name.

        Args:
            name: Variable name.

        Returns:
            Result with variable or error.
        """
        if name not in self._variables:
            return failed(ErrorCode.NOT_FOUND, f"Variable {name} not found")
        return ok(self._variables[name])

    def get_variables(self) -> list[Variable]:
        """Get all variables."""
        return list(self._variables.values())

    def get_constraints(self) -> list[Constraint]:
        """Get all constraints."""
        return self._constraints.copy()

    def get_objective(self) -> Objective | None:
        """Get the objective."""
        return self._objective

    def solve(self, values: dict[str, float] | None = None) -> Result[Solution]:
        """Solve the model (simple evaluation for now).

        Args:
            values: Variable values to evaluate.

        Returns:
            Result with solution or error.
        """
        if self._objective is None:
            return failed(ErrorCode.ILLEGAL_STATE, "No objective set")

        if values is None:
            values = {}

        # Check all variables have values
        for var in self._variables.values():
            if var.name not in values:
                return failed(
                    ErrorCode.ILLEGAL_ARGUMENT, f"Missing value for variable {var.name}"
                )

        # Evaluate constraints
        for constraint in self._constraints:
            expr_val = constraint.expression.evaluate(values)
            if (
                constraint.constraint_type == ConstraintType.LE
                and expr_val > constraint.rhs + 1e-10
                or constraint.constraint_type == ConstraintType.GE
                and expr_val < constraint.rhs - 1e-10
                or constraint.constraint_type == ConstraintType.EQ
                and abs(expr_val - constraint.rhs) > 1e-10
            ):
                return failed(
                    ErrorCode.ILLEGAL_STATE, f"Constraint {constraint.name} violated"
                )

        # Evaluate objective
        obj_value = self._objective.expression.evaluate(values)

        return ok(Solution(obj_value, values))

    def __repr__(self) -> str:
        return f"MetaModel({self._name}, vars={len(self._variables)}, constraints={len(self._constraints)})"
