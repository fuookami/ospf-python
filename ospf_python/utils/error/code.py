"""错误码枚举定义 / Error code enum definitions."""

from __future__ import annotations

import enum


class ErrorCode(enum.Enum):
    """错误码枚举 / Error code enumeration.

    对应 Kotlin 端 ErrorCode(code: UByte) 枚举。
    Mirrors the Kotlin ErrorCode(code: UByte) enum.

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
