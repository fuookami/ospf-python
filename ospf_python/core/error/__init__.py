"""Core error module.

Provides error codes for the core modeling framework.
"""

from __future__ import annotations

from enum import Enum, unique


@unique
class CoreErrorCode(Enum):
    """Core-specific error codes.

    核心模块错误码。
    """

    # Variable errors
    VARIABLE_NOT_FOUND = "VARIABLE_NOT_FOUND"
    VARIABLE_ALREADY_EXISTS = "VARIABLE_ALREADY_EXISTS"
    VARIABLE_INVALID_BOUNDS = "VARIABLE_INVALID_BOUNDS"

    # Model errors
    MODEL_NOT_SOLVED = "MODEL_NOT_SOLVED"
    MODEL_INFEASIBLE = "MODEL_INFEASIBLE"
    MODEL_UNBOUNDED = "MODEL_UNBOUNDED"
    MODEL_ERROR = "MODEL_ERROR"
    ILLEGAL_STATE = "ILLEGAL_STATE"

    # Constraint errors
    CONSTRAINT_NOT_FOUND = "CONSTRAINT_NOT_FOUND"
    CONSTRAINT_INVALID = "CONSTRAINT_INVALID"

    # Objective errors
    OBJECTIVE_NOT_SET = "OBJECTIVE_NOT_SET"
    OBJECTIVE_INVALID = "OBJECTIVE_INVALID"

    # Solver errors
    SOLVER_NOT_AVAILABLE = "SOLVER_NOT_AVAILABLE"
    SOLVER_ERROR = "SOLVER_ERROR"
    SOLVER_TIMEOUT = "SOLVER_TIMEOUT"

    # Token errors
    TOKEN_NOT_FOUND = "TOKEN_NOT_FOUND"
    TOKEN_INVALID = "TOKEN_INVALID"
