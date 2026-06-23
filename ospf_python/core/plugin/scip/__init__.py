"""SCIP solver adapter.

Provides SCIP solver implementation.
"""

from __future__ import annotations

import importlib.util

from ospf_python.core.model import ConstraintType, MetaModel, ObjectiveType
from ospf_python.core.solver import Solver, SolverConfig, SolverOutput, SolverStatus
from ospf_python.utils.error import ErrorCode
from ospf_python.utils.result import Result, failed, ok


class ScipSolver(Solver):
    """SCIP solver adapter.

    SCIP 求解器适配器。
    """

    def __init__(self) -> None:
        """Initialize SCIP solver."""
        self._available = importlib.util.find_spec("pyscipopt") is not None

    def solve(
        self, model: MetaModel, config: SolverConfig | None = None
    ) -> Result[SolverOutput]:
        """Solve using SCIP.

        Args:
            model: Model to solve.
            config: Solver configuration.

        Returns:
            Result with solver output or error.
        """
        if not self._available:
            return failed(ErrorCode.SOLVER_NOT_AVAILABLE, "pyscipopt not installed")

        try:
            from pyscipopt import Model as ScipModel

            # Create SCIP model
            scip_model = ScipModel(model.name)
            scip_model.hideOutput()

            # Add variables
            variables = {}
            for var in model.get_variables():
                lb = var.lower_bound if var.lower_bound is not None else None
                ub = var.upper_bound if var.upper_bound is not None else None
                vtype = "CONTINUOUS"
                if var.variable_type.value == "integer":
                    vtype = "INTEGER"
                elif var.variable_type.value == "binary":
                    vtype = "BINARY"
                variables[var.name] = scip_model.addVar(var.name, vtype, lb=lb, ub=ub)

            # Set objective
            objective = model.get_objective()
            if objective is None:
                return failed(ErrorCode.ILLEGAL_STATE, "No objective set")

            obj_expr = self._build_expression(objective.expression, variables)
            if objective.objective_type == ObjectiveType.MINIMIZE:
                scip_model.setObjective(obj_expr, "minimize")
            else:
                scip_model.setObjective(obj_expr, "maximize")

            # Add constraints
            for constraint in model.get_constraints():
                expr = self._build_expression(constraint.expression, variables)
                if constraint.constraint_type == ConstraintType.LE:
                    scip_model.addCons(expr <= constraint.rhs, constraint.name)  # type: ignore[operator]
                elif constraint.constraint_type == ConstraintType.GE:
                    scip_model.addCons(expr >= constraint.rhs, constraint.name)  # type: ignore[operator]
                elif constraint.constraint_type == ConstraintType.EQ:
                    scip_model.addCons(expr == constraint.rhs, constraint.name)

            # Solve
            scip_model.optimize()

            # Extract solution
            status = scip_model.getStatus()
            if status == "optimal":
                variable_values = {
                    name: scip_model.getVal(v) for name, v in variables.items()
                }
                return ok(
                    SolverOutput(
                        status=SolverStatus.OPTIMAL,
                        objective_value=scip_model.getObjVal(),
                        variable_values=variable_values,
                    )
                )
            elif status == "infeasible":
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
            return failed(ErrorCode.SOLVER_ERROR, f"SCIP error: {e}")

    def _build_expression(self, expr: object, variables: dict[str, object]) -> object:
        """Build SCIP expression from symbolic expression."""
        from ospf_python.core.symbol import LinearExpression, LinearTerm

        if isinstance(expr, LinearTerm):
            return expr.coefficient * variables[expr.variable]  # type: ignore[operator]
        elif isinstance(expr, LinearExpression):
            # Build sum of terms
            result = None
            for term in expr.terms:
                term_expr = term.coefficient * variables[term.variable]  # type: ignore[operator]
                result = term_expr if result is None else result + term_expr
            if expr.constant != 0:
                result = expr.constant if result is None else result + expr.constant
            return result if result is not None else 0.0
        # For other expression types, return 0
        return 0.0

    def name(self) -> str:
        """Get solver name."""
        return "SCIP"
