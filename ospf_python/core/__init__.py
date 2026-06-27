"""核心优化框架 / Core optimization framework.

提供模型、变量、约束和求解器基础设施。
Provides model, variable, constraint, and solver infrastructure.
"""

from ospf_python.core.model.basic.constraint_sign import (
    ConstraintSign,
)
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.solver.linear_solver import LinearSolver
from ospf_python.core.solver.output.solver_output import (
    SolverOutput,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)
from ospf_python.core.solver.solver import Solver
from ospf_python.core.variable.any_variable import AnyVariable
from ospf_python.core.variable.type import VariableType
from ospf_python.core.variable.variable_range import VariableRange

__all__ = [
    "AnyVariable",
    "ConstraintSign",
    "LinearSolver",
    "MetaModel",
    "Solver",
    "SolverOutput",
    "SolverStatus",
    "VariableRange",
    "VariableType",
]
