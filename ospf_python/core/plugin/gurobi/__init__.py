"""Gurobi solver adapter.

Provides Gurobi solver implementation.
"""

from __future__ import annotations

import importlib.util
from typing import Any

from ospf_python.core.model import ConstraintType, MetaModel, ObjectiveType
from ospf_python.core.solver import Solver, SolverConfig, SolverOutput, SolverStatus
from ospf_python.utils.error import ErrorCode
from ospf_python.utils.result import Result, failed, ok


class GurobiSolver(Solver):
    """Gurobi solver adapter.

    Gurobi 求解器适配器。
    """

    def __init__(self) -> None:
        """Initialize Gurobi solver."""
        self._available = importlib.util.find_spec("gurobipy") is not None

    def solve(
        self, model: MetaModel, config: SolverConfig | None = None
    ) -> Result[SolverOutput]:
        """Solve using Gurobi.

        Args:
            model: Model to solve.
            config: Solver configuration.

        Returns:
            Result with solver output or error.
        """
        if not self._available:
            return failed(ErrorCode.SOLVER_NOT_AVAILABLE, "gurobipy not installed")

        try:
            import gurobipy as gp
            from gurobipy import GRB

            # Create Gurobi model
            gurobi_model = gp.Model(model.name)
            gurobi_model.setParam("OutputFlag", 0)

            # Add variables
            variables = {}
            for var in model.get_variables():
                lb = var.lower_bound if var.lower_bound is not None else -GRB.INFINITY
                ub = var.upper_bound if var.upper_bound is not None else GRB.INFINITY
                vtype = GRB.CONTINUOUS
                if var.variable_type.value == "integer":
                    vtype = GRB.INTEGER
                elif var.variable_type.value == "binary":
                    vtype = GRB.BINARY
                variables[var.name] = gurobi_model.addVar(
                    lb=lb, ub=ub, vtype=vtype, name=var.name
                )

            gurobi_model.update()

            # Set objective
            objective = model.get_objective()
            if objective is None:
                return failed(ErrorCode.ILLEGAL_STATE, "No objective set")

            obj_expr = self._build_expression(objective.expression, variables)
            if objective.objective_type == ObjectiveType.MINIMIZE:
                gurobi_model.setObjective(obj_expr, GRB.MINIMIZE)  # type: ignore[call-overload]
            else:
                gurobi_model.setObjective(obj_expr, GRB.MAXIMIZE)  # type: ignore[call-overload]

            # Add constraints
            for constraint in model.get_constraints():
                expr = self._build_expression(constraint.expression, variables)
                if constraint.constraint_type == ConstraintType.LE:
                    gurobi_model.addConstr(expr <= constraint.rhs, constraint.name)  # type: ignore[operator,call-overload]
                elif constraint.constraint_type == ConstraintType.GE:
                    gurobi_model.addConstr(expr >= constraint.rhs, constraint.name)  # type: ignore[operator,call-overload]
                elif constraint.constraint_type == ConstraintType.EQ:
                    gurobi_model.addConstr(expr == constraint.rhs, constraint.name)  # type: ignore[call-overload]

            # Solve
            gurobi_model.optimize()

            # Extract solution
            if gurobi_model.status == GRB.OPTIMAL:
                variable_values = {name: v.x for name, v in variables.items()}  # type: ignore[attr-defined]
                return ok(
                    SolverOutput(
                        status=SolverStatus.OPTIMAL,
                        objective_value=gurobi_model.objVal,
                        variable_values=variable_values,
                    )
                )
            elif gurobi_model.status == GRB.INFEASIBLE:
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
            return failed(ErrorCode.SOLVER_ERROR, f"Gurobi error: {e}")

    def _build_expression(self, expr: object, variables: dict[str, Any]) -> object:
        """Build Gurobi expression from symbolic expression."""
        from gurobipy import LinExpr

        from ospf_python.core.symbol import LinearExpression, LinearTerm

        if isinstance(expr, LinearTerm):
            return expr.coefficient * variables[expr.variable]
        elif isinstance(expr, LinearExpression):
            result = LinExpr()
            for term in expr.terms:
                result += term.coefficient * variables[term.variable]
            if expr.constant != 0:
                result += expr.constant
            return result
        # For other expression types, return 0
        return 0.0

    def name(self) -> str:
        """Get solver name."""
        return "Gurobi"
