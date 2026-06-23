"""1D Cutting Stock framework.

Provides domain-specific framework for 1D cutting stock problems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from ospf_python.core.model import ConstraintType, MetaModel, ObjectiveType, Solution
from ospf_python.core.solver import MockSolver, Solver
from ospf_python.core.symbol import LinearExpression, LinearTerm
from ospf_python.core.variable import integer
from ospf_python.framework import FrameworkConfig, FrameworkModel, SimpleFrameworkSolver
from ospf_python.utils.result import Ok  # noqa: F401

if TYPE_CHECKING:
    from ospf_python.quantities import Quantity
    from ospf_python.utils.result import Result

V = TypeVar("V")


@dataclass(frozen=True, slots=True)
class Demand:
    """Demand for a specific length.

    特定长度的需求。
    """

    name: str
    length: Quantity
    quantity: int


@dataclass(frozen=True, slots=True)
class Stock:
    """Stock material.

    原材料。
    """

    name: str
    length: Quantity
    cost: float


@dataclass(frozen=True, slots=True)
class CuttingPattern:
    """Cutting pattern.

    下料方案。
    """

    stock_name: str
    cuts: list[str]
    total_length: float
    waste: float


@dataclass(frozen=True, slots=True)
class Csp1dSolution:
    """1D cutting stock solution.

    一维下料解决方案。
    """

    patterns: list[CuttingPattern]
    total_stock: int
    total_waste: float
    utilization: float
    objective_value: float


class Csp1dModel(FrameworkModel):
    """1D cutting stock model.

    一维下料模型。
    """

    def __init__(
        self,
        demands: list[Demand],
        stocks: list[Stock],
        extra_constraints: list[object] | None = None,
    ) -> None:
        """Initialize.

        Args:
            demands: Demands to fulfill.
            stocks: Available stocks.
            extra_constraints: Extra constraints for extension point.
        """
        self._demands = demands
        self._stocks = stocks
        self._extra_constraints = extra_constraints or []

    def build_meta_model(self) -> MetaModel:
        """Build the MetaModel."""
        model = MetaModel("csp1d")

        # Add variables: x[j] = number of times pattern j is used
        for j, _stock in enumerate(self._stocks):
            model.add_variable(integer(f"x_{j}", 0))

        # Set objective: minimize total cost
        terms = []
        for j, stock in enumerate(self._stocks):
            terms.append(LinearTerm(stock.cost, f"x_{j}"))

        obj_expr = LinearExpression(tuple(terms))
        model.set_objective("min_cost", obj_expr, ObjectiveType.MINIMIZE)

        # Add constraints: each demand must be satisfied
        for i, demand in enumerate(self._demands):
            terms = []
            for j, stock in enumerate(self._stocks):
                # How many times demand i fits in stock j
                cuts_per_stock = int(stock.length.value // demand.length.value)
                if cuts_per_stock > 0:
                    terms.append(LinearTerm(float(cuts_per_stock), f"x_{j}"))

            if terms:
                expr = LinearExpression(tuple(terms))
                model.add_constraint(
                    f"demand_{i}", expr, ConstraintType.GE, float(demand.quantity)
                )

        return model

    def extract_solution(self, solution: Solution) -> Csp1dSolution:
        """Extract domain solution from solver solution."""
        patterns = []
        total_stock = 0
        total_waste = 0.0

        for j, stock in enumerate(self._stocks):
            var_name = f"x_{j}"
            count = int(solution.variable_values.get(var_name, 0))
            if count > 0:
                # Calculate cuts for this pattern
                cuts = []
                remaining_length = stock.length.value
                for demand in self._demands:
                    cuts_per_stock = int(stock.length.value // demand.length.value)
                    if cuts_per_stock > 0:
                        for _ in range(cuts_per_stock):
                            if remaining_length >= demand.length.value:
                                cuts.append(demand.name)
                                remaining_length -= demand.length.value

                waste = remaining_length
                total_length = stock.length.value - waste

                patterns.append(
                    CuttingPattern(
                        stock_name=stock.name,
                        cuts=cuts,
                        total_length=total_length,
                        waste=waste,
                    )
                )

                total_stock += count
                total_waste += waste * count

        total_used_length = sum(p.total_length for p in patterns) * total_stock
        total_stock_length = sum(s.length.value for s in self._stocks) * total_stock
        utilization = (
            total_used_length / total_stock_length if total_stock_length > 0 else 0
        )

        return Csp1dSolution(
            patterns=patterns,
            total_stock=total_stock,
            total_waste=total_waste,
            utilization=utilization,
            objective_value=solution.objective_value,
        )


class Csp1dSolver:
    """1D cutting stock solver.

    一维下料求解器。
    """

    def __init__(self, solver: Solver | None = None) -> None:
        """Initialize.

        Args:
            solver: Core solver (defaults to MockSolver).
        """
        self._solver = solver or MockSolver()
        self._framework_solver = SimpleFrameworkSolver(self._solver)

    def solve(
        self,
        demands: list[Demand],
        stocks: list[Stock],
        config: FrameworkConfig | None = None,
        extra_constraints: list[object] | None = None,
    ) -> Result[Csp1dSolution]:
        """Solve 1D cutting stock problem.

        Args:
            demands: Demands to fulfill.
            stocks: Available stocks.
            config: Framework configuration.
            extra_constraints: Extra constraints for extension point.

        Returns:
            Result with cutting solution.
        """
        model = Csp1dModel(demands, stocks, extra_constraints)
        return self._framework_solver.solve(model, config)
