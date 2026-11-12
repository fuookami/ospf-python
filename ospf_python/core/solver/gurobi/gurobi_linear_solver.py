"""Gurobi 线性求解器 / Gurobi linear solver.

基于 gurobipy 的 LP/MILP 求解器实现。
LP/MILP solver implementation based on gurobipy.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)
from ospf_python.core.solver.gurobi.gurobi_solver import (
    GurobiSolver,
)
from ospf_python.core.solver.linear_solver import (
    LinearSolver,
)
from ospf_python.core.solver.output.solver_output import (
    SolverOutput,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)

if TYPE_CHECKING:
    import gurobipy as gp

    from ospf_python.core.solver.config.gurobi_solver_config import (
        GurobiSolverConfig,
    )
    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )


@dataclass(frozen=True)
class GurobiLinearSolver(GurobiSolver, LinearSolver):
    """Gurobi 线性求解器 / Gurobi linear solver.

    冻结数据类，实现 LinearSolver 接口，使用 gurobipy
    求解 LP 和 MILP 问题。
    Frozen dataclass implementing the LinearSolver interface,
    using gurobipy to solve LP and MILP problems.

    Attributes:
        config: Gurobi 求解器配置 / Gurobi solver config.
        _model: 底层 gurobipy 模型 / Underlying model.
        _cleaned: 是否已清理 / Whether cleaned.
        _supports_int: 是否支持整数 / Whether integer
            variables are supported.
    """

    config: GurobiSolverConfig = field(
        default_factory=lambda: __import__(
            "ospf_python.core.solver.config.gurobi_solver_config",
            fromlist=["GurobiSolverConfig"],
        ).GurobiSolverConfig(),
    )
    """Gurobi 求解器配置 / Gurobi solver config."""

    _supports_int: bool = field(
        default=True,
        repr=False,
    )
    """是否支持整数变量 / Whether integer variables are
    supported."""

    def supports_integer(self) -> bool:
        """是否支持整数变量 / Whether integer variables
        are supported.

        Returns:
            支持整数变量时返回 True / True when integer
            variables are supported.
        """
        return self._supports_int

    @staticmethod
    def _ordered_triad_variables(
        model: LinearTriadModel,
    ) -> list[str]:
        """收集物化变量顺序 / Collect materialization variable order."""
        names: list[str] = []
        seen: set[str] = set()

        def append(name: str) -> None:
            if not isinstance(name, str) or not name:
                raise ValueError("variable names must be non-empty strings")
            if name in seen:
                return
            seen.add(name)
            names.append(name)

        for name in model.variables:
            if not isinstance(name, str) or not name:
                raise ValueError("variable names must be non-empty strings")
            if name in seen:
                raise ValueError(f"duplicate variable name: {name}")
            seen.add(name)
            names.append(name)

        for name in model.objective:
            append(name)
        for name in model.lower_bounds:
            append(name)
        for name in model.upper_bounds:
            append(name)
        for coefficients in model.constraints.values():
            for name in coefficients:
                append(name)
        return names

    @staticmethod
    def _finite_number(
        value: float,
        *,
        label: str,
    ) -> float:
        """转换有限数值 / Convert a finite numeric value."""
        try:
            number = float(value)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(f"{label} must be numeric") from exc
        if not math.isfinite(number):
            raise ValueError(f"{label} must be finite")
        return number

    @staticmethod
    def _bound_number(
        value: float,
        *,
        label: str,
    ) -> float:
        """转换变量边界 / Convert a variable bound."""
        try:
            number = float(value)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(f"{label} must be numeric") from exc
        if math.isnan(number):
            raise ValueError(f"{label} must not be NaN")
        return number

    @staticmethod
    def _variable_type(
        value: object,
    ) -> str:
        """规范化 Gurobi 变量类型 / Normalize a Gurobi variable type."""
        raw = getattr(value, "value", value)
        if not isinstance(raw, str):
            raise ValueError(f"unsupported variable type: {value!r}")
        normalized = raw.strip().lower()
        if normalized not in {"continuous", "integer", "binary"}:
            raise ValueError(f"unsupported variable type: {value!r}")
        return normalized

    @staticmethod
    def _constraint_sense(
        sense: object,
    ) -> str:
        """规范化约束方向 / Normalize a constraint sense."""
        aliases: Mapping[object, str] = {
            "<": "<=",
            "<=": "<=",
            "=<": "<=",
            ">": ">=",
            ">=": ">=",
            "=>": ">=",
            "=": "==",
            "==": "==",
        }
        try:
            return aliases[sense]
        except KeyError as exc:
            raise ValueError(f"unsupported constraint sense: {sense!r}") from exc

    def _replace_model(
        self,
        model: gp.Model,
    ) -> None:
        """替换并释放旧模型 / Replace and release the previous model."""
        previous = self._model
        if previous is not None and previous is not model:
            previous.dispose()
        object.__setattr__(self, "_model", model)
        object.__setattr__(self, "_cleaned", False)

    def _materialize_triad_model(
        self,
        model: LinearTriadModel,
    ) -> gp.Model:
        """将线性三元组模型物化为 gurobipy 模型。

        Materialize a linear triad model into a gurobipy model.
        """
        import gurobipy as gp
        from gurobipy import GRB

        variable_names = self._ordered_triad_variables(model)
        if not variable_names:
            raise ValueError("linear triad model has no variables")
        unknown_type_names = sorted(set(model.variable_types) - set(variable_names))
        if unknown_type_names:
            raise ValueError(
                "variable types reference unknown variables: "
                + ", ".join(unknown_type_names)
            )

        materialized = gp.Model(model.name or "ospf_gurobi")
        try:
            variables: dict[str, gp.Var] = {}
            for name in variable_names:
                variable_type = self._variable_type(
                    model.variable_types.get(name, "continuous"),
                )
                lower = self._bound_number(
                    model.lower_bounds.get(name, 0.0),
                    label=f"lower bound for {name}",
                )
                upper = self._bound_number(
                    model.upper_bounds.get(
                        name,
                        1.0 if variable_type == "binary" else float("inf"),
                    ),
                    label=f"upper bound for {name}",
                )
                if lower > upper:
                    raise ValueError(f"lower bound exceeds upper bound for {name}")
                if variable_type == "binary" and not (
                    math.isfinite(lower)
                    and math.isfinite(upper)
                    and 0.0 <= lower <= upper <= 1.0
                ):
                    raise ValueError(f"binary bounds must be within [0, 1] for {name}")
                variables[name] = materialized.addVar(
                    lb=lower,
                    ub=upper,
                    vtype={
                        "continuous": GRB.CONTINUOUS,
                        "integer": GRB.INTEGER,
                        "binary": GRB.BINARY,
                    }[variable_type],
                    name=name,
                )

            objective = gp.LinExpr()
            for name, coefficient in model.objective.items():
                objective.add(
                    variables[name],
                    self._finite_number(
                        coefficient,
                        label=f"objective coefficient for {name}",
                    ),
                )
            materialized.setObjective(objective, GRB.MINIMIZE)

            for constraint_name, coefficients in model.constraints.items():
                if not isinstance(constraint_name, str) or not constraint_name:
                    raise ValueError("constraint names must be non-empty strings")
                expression = gp.LinExpr()
                for name, coefficient in coefficients.items():
                    expression.add(
                        variables[name],
                        self._finite_number(
                            coefficient,
                            label=f"coefficient for {constraint_name}.{name}",
                        ),
                    )
                rhs = self._finite_number(
                    model.rhs.get(constraint_name, 0.0),
                    label=f"right-hand side for {constraint_name}",
                )
                sense = self._constraint_sense(
                    model.sense.get(constraint_name, "<="),
                )
                if sense == "<=":
                    materialized.addConstr(
                        expression <= rhs,
                        name=constraint_name,
                    )
                elif sense == ">=":
                    materialized.addConstr(
                        expression >= rhs,
                        name=constraint_name,
                    )
                else:
                    materialized.addConstr(
                        expression == rhs,
                        name=constraint_name,
                    )

            materialized.update()
        except Exception:
            materialized.dispose()
            raise
        self._replace_model(materialized)
        return materialized

    def solve(
        self,
        model: object,
        *,
        options: SolveOptions | None = None,
    ) -> SolverOutput:
        """求解线性模型 / Solve a linear model.

        使用 gurobipy 求解 LP/MILP 问题。
        Uses gurobipy to solve LP/MILP problems.

        Args:
            model: 要求解的优化模型 / The optimization
                model.
            options: 求解选项 / Solve options.

        Returns:
            求解输出结果 / The solver output.
        """
        import gurobipy as gp
        from gurobipy import GRB

        try:
            # 显式标注为 Optional：分支 3 可能取到尚未建好的持有模型。 / Explicitly
            # optional: the third branch may read a retained model that is not built yet.
            m: gp.Model | None
            if isinstance(model, LinearTriadModel):
                m = self._materialize_triad_model(model)
            elif isinstance(model, gp.Model):
                self._replace_model(model)
                m = model
            else:
                # 调用方可能已用 _get_or_create_model() 建好模型，只传一个带
                # objective_sense 的包装对象；此时求解持有的模型而不是丢弃它。
                # Callers may have built the model via _get_or_create_model() and
                # pass only a wrapper carrying objective_sense; solve the retained
                # model instead of discarding it.
                m = self._model
                if m is None:
                    return SolverOutput(
                        status=SolverStatus.ERROR,
                    )

            self._apply_config(m, options=options)

            if hasattr(model, "objective_sense"):
                if model.objective_sense == "min":
                    m.ModelSense = GRB.MINIMIZE
                else:
                    m.ModelSense = GRB.MAXIMIZE

            m.optimize()

            return self._build_output(m)

        except (gp.GurobiError, AttributeError, KeyError, TypeError, ValueError):
            return SolverOutput(
                status=SolverStatus.ERROR,
            )
