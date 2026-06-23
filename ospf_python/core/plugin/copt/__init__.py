"""COPT solver adapter.

Provides COPT solver implementation.
"""

from __future__ import annotations

import importlib.util

from ospf_python.core.model import ConstraintType, MetaModel, ObjectiveType
from ospf_python.core.solver import Solver, SolverConfig, SolverOutput, SolverStatus
from ospf_python.utils.error import ErrorCode
from ospf_python.utils.result import Result, failed, ok


class CoptSolver(Solver):
    """COPT solver adapter.

    COPT 求解器适配器。
    """

    def __init__(self) -> None:
        """Initialize COPT solver."""
        self._available = importlib.util.find_spec("coptpy") is not None

    def solve(
        self, model: MetaModel, config: SolverConfig | None = None
    ) -> Result[SolverOutput]:
        """Solve using COPT.

        Args:
            model: Model to solve.
            config: Solver configuration.

        Returns:
            Result with solver output or error.
        """
        if not self._available:
            return failed(ErrorCode.SOLVER_NOT_AVAILABLE, "coptpy not installed")

        try:
            import coptpy
            from coptpy import COPT

            # Create COPT model
            copt_model = coptpy.Model(model.name)
            copt_model.setParam(COPT.Param.Logging, 0)

            # Add variables
            variables = {}
            for var in model.get_variables():
                lb = var.lower_bound if var.lower_bound is not None else -COPT.INFINITY
                ub = var.upper_bound if var.upper_bound is not None else COPT.INFINITY
                vtype = COPT.CONTINUOUS
                if var.variable_type.value == "integer":
                    vtype = COPT.INTEGER
                elif var.variable_type.value == "binary":
                    vtype = COPT.BINARY
                variables[var.name] = copt_model.addVar(
                    lb=lb, ub=ub, vtype=vtype, name=var.name
                )

            copt_model.update()

            # Set objective
            objective = model.get_objective()
            if objective is None:
                return failed(ErrorCode.ILLEGAL_STATE, "No objective set")

            obj_expr = self._build_expression(objective.expression, variables)
            if objective.objective_type == ObjectiveType.MINIMIZE:
                copt_model.setObjective(obj_expr, COPT.MINIMIZE)
            else:
                copt_model.setObjective(obj_expr, COPT.MAXIMIZE)

            # Add constraints
            for constraint in model.get_constraints():
                expr = self._build_expression(constraint.expression, variables)
                if constraint.constraint_type == ConstraintType.LE:
                    copt_model.addConstr(expr <= constraint.rhs, constraint.name)  # type: ignore[operator]
                elif constraint.constraint_type == ConstraintType.GE:
                    copt_model.addConstr(expr >= constraint.rhs, constraint.name)  # type: ignore[operator]
                elif constraint.constraint_type == ConstraintType.EQ:
                    copt_model.addConstr(expr == constraint.rhs, constraint.name)

            # Solve
            copt_model.solve()

            # Extract solution
            if copt_model.status == COPT.OPTIMAL:
                variable_values = {name: v.x for name, v in variables.items()}
                return ok(
                    SolverOutput(
                        status=SolverStatus.OPTIMAL,
                        objective_value=copt_model.objval,
                        variable_values=variable_values,
                    )
                )
            elif copt_model.status == COPT.INFEASIBLE:
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
            return failed(ErrorCode.SOLVER_ERROR, f"COPT error: {e}")

    def _build_expression(self, expr: object, variables: dict[str, object]) -> object:
        """Build COPT expression from symbolic expression."""
        from ospf_python.core.symbol import LinearTerm

        if isinstance(expr, LinearTerm):
            return expr.coefficient * variables[expr.variable]  # type: ignore[operator]
        values = {name: v.x for name, v in variables.items()}  # type: ignore[attr-defined]
        return expr.evaluate(values)  # type: ignore[attr-defined]

    def name(self) -> str:
        """Get solver name."""
        return "COPT"
