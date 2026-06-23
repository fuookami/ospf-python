"""MindOpt solver adapter.

Provides MindOpt solver implementation.
"""

from __future__ import annotations

import importlib.util

from ospf_python.core.model import ConstraintType, MetaModel, ObjectiveType
from ospf_python.core.solver import Solver, SolverConfig, SolverOutput, SolverStatus
from ospf_python.utils.error import ErrorCode
from ospf_python.utils.result import Result, failed, ok


class MindOptSolver(Solver):
    """MindOpt solver adapter.

    MindOpt 求解器适配器。
    """

    def __init__(self) -> None:
        """Initialize MindOpt solver."""
        self._available = importlib.util.find_spec("mindoptpy") is not None

    def solve(
        self, model: MetaModel, config: SolverConfig | None = None
    ) -> Result[SolverOutput]:
        """Solve using MindOpt.

        Args:
            model: Model to solve.
            config: Solver configuration.

        Returns:
            Result with solver output or error.
        """
        if not self._available:
            return failed(ErrorCode.SOLVER_NOT_AVAILABLE, "mindoptpy not installed")

        try:
            import mindoptpy

            # Create MindOpt model
            mindopt_model = mindoptpy.Model(model.name)
            mindopt_model.setParam("OutputFlag", 0)

            # Add variables
            variables = {}
            for var in model.get_variables():
                lb = var.lower_bound if var.lower_bound is not None else -float("inf")
                ub = var.upper_bound if var.upper_bound is not None else float("inf")
                vtype = "C"
                if var.variable_type.value == "integer":
                    vtype = "I"
                elif var.variable_type.value == "binary":
                    vtype = "B"
                variables[var.name] = mindopt_model.addVar(
                    lb=lb, ub=ub, vtype=vtype, name=var.name
                )

            mindopt_model.update()

            # Set objective
            objective = model.get_objective()
            if objective is None:
                return failed(ErrorCode.ILLEGAL_STATE, "No objective set")

            obj_expr = self._build_expression(objective.expression, variables)
            if objective.objective_type == ObjectiveType.MINIMIZE:
                mindopt_model.setObjective(obj_expr, mindoptpy.MINIMIZE)
            else:
                mindopt_model.setObjective(obj_expr, mindoptpy.MAXIMIZE)

            # Add constraints
            for constraint in model.get_constraints():
                expr = self._build_expression(constraint.expression, variables)
                if constraint.constraint_type == ConstraintType.LE:
                    mindopt_model.addConstr(expr <= constraint.rhs, constraint.name)  # type: ignore[operator]
                elif constraint.constraint_type == ConstraintType.GE:
                    mindopt_model.addConstr(expr >= constraint.rhs, constraint.name)  # type: ignore[operator]
                elif constraint.constraint_type == ConstraintType.EQ:
                    mindopt_model.addConstr(expr == constraint.rhs, constraint.name)

            # Solve
            mindopt_model.optimize()

            # Extract solution
            if mindopt_model.status == mindoptpy.OPTIMAL:
                variable_values = {name: v.x for name, v in variables.items()}
                return ok(
                    SolverOutput(
                        status=SolverStatus.OPTIMAL,
                        objective_value=mindopt_model.objVal,
                        variable_values=variable_values,
                    )
                )
            elif mindopt_model.status == mindoptpy.INFEASIBLE:
                return ok(
                    SolverOutput(
                        status=SolverStatus.INFEASIBLE,
                        objective_value=0.0,
                        variable_values={},
                    )
                )
            else:
                return ok(
                    SolverOutput(
                        status=SolverStatus.ERROR,
                        objective_value=0.0,
                        variable_values={},
                    )
                )

        except Exception as e:
            return failed(ErrorCode.SOLVER_ERROR, f"MindOpt error: {e}")

    def _build_expression(self, expr: object, variables: dict[str, object]) -> object:
        """Build MindOpt expression from symbolic expression."""
        from ospf_python.core.symbol import LinearTerm

        if isinstance(expr, LinearTerm):
            return expr.coefficient * variables[expr.variable]  # type: ignore[operator]
        values = {name: v.x for name, v in variables.items()}  # type: ignore[attr-defined]
        return expr.evaluate(values)  # type: ignore[attr-defined]

    def name(self) -> str:
        """Get solver name."""
        return "MindOpt"
