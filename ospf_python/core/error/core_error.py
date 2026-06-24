"""核心错误码定义 / Core error code definitions.

扩展 utils.ErrorCode，提供核心模块专用错误码。
Extends utils.ErrorCode with domain-specific error codes for
the core module.
"""

from __future__ import annotations

import enum


class CoreErrorCode(enum.Enum):
    """核心模块错误码枚举 / Core module error code enumeration.

    继承 utils.ErrorCode 的通用错误码模式，提供核心模块
    各子系统的专用错误码。
    Inherits the general error code pattern from utils.ErrorCode
    and provides domain-specific codes for core module subsystems.

    Attributes:
        value: 错误码整数值 / The integer error code value.
    """

    # ---- 通用错误码 / General error codes ----

    SUCCESS = 0
    """成功 / Success."""

    APPLICATION_ERROR = 1
    """应用错误 / Application error."""

    ILLEGAL_ARGUMENT = 2
    """非法参数 / Illegal argument."""

    OUT_OF_RANGE = 3
    """超出范围 / Out of range."""

    NOT_INITIALIZED = 4
    """未初始化 / Not initialized."""

    ALREADY_INITIALIZED = 5
    """已初始化 / Already initialized."""

    NOT_FOUND = 6
    """未找到 / Not found."""

    ALREADY_EXIST = 7
    """已存在 / Already exists."""

    NOT_SUPPORTED = 8
    """不支持 / Not supported."""

    TIMEOUT = 9
    """超时 / Timeout."""

    OVERFLOW = 10
    """上溢 / Overflow."""

    UNDERFLOW = 11
    """下溢 / Underflow."""

    CANCELLED = 12
    """已取消 / Cancelled."""

    DEADLINE_EXCEEDED = 13
    """超过截止时间 / Deadline exceeded."""

    PERMISSION_DENIED = 14
    """权限拒绝 / Permission denied."""

    RESOURCE_EXHAUSTED = 15
    """资源耗尽 / Resource exhausted."""

    FAILED_PRECONDITION = 16
    """前置条件失败 / Failed precondition."""

    ABORTED = 17
    """已中止 / Aborted."""

    UNAVAILABLE = 18
    """不可用 / Unavailable."""

    DATA_LOSS = 19
    """数据丢失 / Data loss."""

    UNAUTHENTICATED = 20
    """未认证 / Unauthenticated."""

    PARSING_FAILED = 30
    """解析失败 / Parsing failed."""

    # ---- 求解器错误码 / Solver error codes ----

    OPTIMIZATION_ERROR = 100
    """优化错误 / Optimization error."""

    SOLVER_NOT_AVAILABLE = 101
    """求解器不可用 / Solver not available."""

    MODEL_BUILD_FAILED = 102
    """模型构建失败 / Model build failed."""

    SOLVE_FAILED = 103
    """求解失败 / Solve failed."""

    NO_SOLUTION = 104
    """无解 / No solution."""

    # ---- 核心领域错误码 / Core domain error codes ----

    MODEL_ERROR = 200
    """模型错误 / Model error."""

    VARIABLE_ERROR = 201
    """变量错误 / Variable error."""

    TOKEN_ERROR = 202
    """令牌错误 / Token error."""

    CONSTRAINT_ERROR = 203
    """约束错误 / Constraint error."""

    SOLVER_ERROR = 204
    """求解器领域错误 / Solver domain error."""

    EXTRACTION_ERROR = 205
    """提取错误 / Extraction error."""
