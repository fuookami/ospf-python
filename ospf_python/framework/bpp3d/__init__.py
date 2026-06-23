"""3D Bin Packing framework.

Provides domain-specific framework for 3D bin packing problems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from ospf_python.core.model import ConstraintType, MetaModel, ObjectiveType, Solution
from ospf_python.core.solver import MockSolver, Solver
from ospf_python.core.symbol import LinearTerm
from ospf_python.core.variable import integer
from ospf_python.framework import FrameworkConfig, FrameworkModel, SimpleFrameworkSolver
from ospf_python.quantities import METER, Quantity

if TYPE_CHECKING:
    from ospf_python.utils.result import Result

V = TypeVar("V")


@dataclass(frozen=True, slots=True)
class Item:
    """Item to be packed.

    待装箱物品。
    """

    name: str
    width: Quantity
    height: Quantity
    depth: Quantity
    weight: Quantity

    @property
    def volume(self) -> Quantity:
        """Get item volume."""
        return Quantity(
            self.width.value * self.height.value * self.depth.value,
            METER,
        )


@dataclass(frozen=True, slots=True)
class Bin:
    """Bin container.

    箱子容器。
    """

    name: str
    width: Quantity
    height: Quantity
    depth: Quantity
    max_weight: Quantity

    @property
    def volume(self) -> Quantity:
        """Get bin volume."""
        return Quantity(
            self.width.value * self.height.value * self.depth.value,
            METER,
        )


@dataclass(frozen=True, slots=True)
class PackingResult:
    """Packing result.

    装箱结果。
    """

    bin_name: str
    items: list[str]
    total_volume: float
    utilization: float


@dataclass(frozen=True, slots=True)
class Bpp3dSolution:
    """3D bin packing solution.

    三维装箱解决方案。
    """

    packings: list[PackingResult]
    total_bins: int
    total_volume: float
    objective_value: float


class Bpp3dModel(FrameworkModel):
    """3D bin packing model.

    三维装箱模型。
    """

    def __init__(
        self,
        items: list[Item],
        bins: list[Bin],
        extra_constraints: list[object] | None = None,
    ) -> None:
        """Initialize.

        Args:
            items: Items to pack.
            bins: Available bins.
            extra_constraints: Extra constraints for extension point.
        """
        self._items = items
        self._bins = bins
        self._extra_constraints = extra_constraints or []

    def build_meta_model(self) -> MetaModel:
        """Build the MetaModel."""
        model = MetaModel("bpp3d")

        # Add variables: x[i][j] = 1 if item i is packed in bin j
        for i, _item in enumerate(self._items):
            for j, _bin in enumerate(self._bins):
                model.add_variable(integer(f"x_{i}_{j}", 0, 1))

        # Set objective: minimize number of bins used
        terms = []
        for j, _bin in enumerate(self._bins):
            # y[j] = 1 if bin j is used
            model.add_variable(integer(f"y_{j}", 0, 1))
            terms.append(LinearTerm(1.0, f"y_{j}"))

        from ospf_python.core.symbol import LinearExpression

        obj_expr = LinearExpression(tuple(terms))
        model.set_objective("min_bins", obj_expr, ObjectiveType.MINIMIZE)

        # Add constraints: each item must be packed exactly once
        for i, _item in enumerate(self._items):
            terms = []
            for j, _bin in enumerate(self._bins):
                terms.append(LinearTerm(1.0, f"x_{i}_{j}"))
            expr = LinearExpression(tuple(terms))
            model.add_constraint(f"item_{i}_packed", expr, ConstraintType.EQ, 1.0)

        # Add constraints: item can only be packed in used bin
        for i, _item in enumerate(self._items):
            for j, _bin in enumerate(self._bins):
                # x[i][j] <= y[j]
                terms = [
                    LinearTerm(1.0, f"x_{i}_{j}"),
                    LinearTerm(-1.0, f"y_{j}"),
                ]
                expr = LinearExpression(tuple(terms))
                model.add_constraint(f"item_{i}_bin_{j}", expr, ConstraintType.LE, 0.0)

        return model

    def extract_solution(self, solution: Solution) -> Bpp3dSolution:
        """Extract domain solution from solver solution."""
        packings = []
        for j, bin in enumerate(self._bins):
            items_in_bin = []
            for i, item in enumerate(self._items):
                var_name = f"x_{i}_{j}"
                if solution.variable_values.get(var_name, 0) > 0.5:
                    items_in_bin.append(item.name)

            if items_in_bin:
                total_volume = sum(
                    item.volume.value
                    for item in self._items
                    if item.name in items_in_bin
                )
                utilization = (
                    total_volume / bin.volume.value if bin.volume.value > 0 else 0
                )
                packings.append(
                    PackingResult(
                        bin_name=bin.name,
                        items=items_in_bin,
                        total_volume=total_volume,
                        utilization=utilization,
                    )
                )

        return Bpp3dSolution(
            packings=packings,
            total_bins=len(packings),
            total_volume=sum(p.total_volume for p in packings),
            objective_value=solution.objective_value,
        )


class Bpp3dSolver:
    """3D bin packing solver.

    三维装箱求解器。
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
        items: list[Item],
        bins: list[Bin],
        config: FrameworkConfig | None = None,
        extra_constraints: list[object] | None = None,
    ) -> Result[Bpp3dSolution]:
        """Solve 3D bin packing problem.

        Args:
            items: Items to pack.
            bins: Available bins.
            config: Framework configuration.
            extra_constraints: Extra constraints for extension point.

        Returns:
            Result with packing solution.
        """
        model = Bpp3dModel(items, bins, extra_constraints)
        return self._framework_solver.solve(model, config)
