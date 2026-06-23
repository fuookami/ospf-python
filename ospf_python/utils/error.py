"""Error types for the ospf-python framework.

Provides ErrorCode enumeration and Error hierarchy for Result-based error handling.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum, unique
from typing import Any


@unique
class ErrorCode(Enum):
    """Standard error codes for the ospf framework.

    错误码枚举，定义所有标准错误码。
    """

    # General errors
    ILLEGAL_ARGUMENT = "ILLEGAL_ARGUMENT"
    ILLEGAL_STATE = "ILLEGAL_STATE"
    NOT_FOUND = "NOT_FOUND"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"

    # Application errors
    APPLICATION_FAILED = "APPLICATION_FAILED"
    APPLICATION_ERROR = "APPLICATION_ERROR"

    # Data errors
    DATA_CORRUPTED = "DATA_CORRUPTED"
    DATA_CONFLICT = "DATA_CONFLICT"
    DATA_MISSING = "DATA_MISSING"

    # IO errors
    IO_ERROR = "IO_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT = "TIMEOUT"

    # Solver errors
    SOLVER_NOT_AVAILABLE = "SOLVER_NOT_AVAILABLE"
    SOLVER_ERROR = "SOLVER_ERROR"
    SOLVER_INFEASIBLE = "SOLVER_INFEASIBLE"
    SOLVER_UNBOUNDED = "SOLVER_UNBOUNDED"
    SOLVER_TIMEOUT = "SOLVER_TIMEOUT"

    # Other
    OTHER = "OTHER"


class Error:
    """Base error class with code and message.

    错误基类，包含 code 和 message。
    """

    __slots__ = ("_code", "_message")

    def __init__(self, code: ErrorCode, message: str) -> None:
        self._code = code
        self._message = message

    @property
    def code(self) -> ErrorCode:
        """Get the error code."""
        return self._code

    @property
    def message(self) -> str:
        """Get the error message."""
        return self._message

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Error):
            return NotImplemented
        return self._code == other._code and self._message == other._message

    def __hash__(self) -> int:
        return hash((self._code, self._message))

    def __repr__(self) -> str:
        return f"Error(code={self._code!r}, message={self._message!r})"

    def __str__(self) -> str:
        return f"[{self._code.value}] {self._message}"


class Err(Error):
    """Basic error.

    基本错误。
    """

    __slots__ = ()

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(code, message)


class LazyErr(Error):
    """Lazy message error - defers message construction.

    惰性消息错误，延迟消息构造。
    """

    __slots__ = ("_message_fn",)

    def __init__(self, code: ErrorCode, message_fn: Callable[[], str]) -> None:
        self._code = code
        self._message_fn = message_fn
        self._message = ""

    @property
    def message(self) -> str:
        """Get the error message, computing it lazily if needed."""
        if not self._message:
            self._message = self._message_fn()
        return self._message


class ExErr(Error):
    """Error with an associated value.

    带关联值的错误。
    """

    __slots__ = ("_value",)

    def __init__(self, code: ErrorCode, message: str, value: Any = None) -> None:
        super().__init__(code, message)
        self._value = value

    @property
    def value(self) -> Any:
        """Get the associated value."""
        return self._value

    def __repr__(self) -> str:
        return f"ExErr(code={self._code!r}, message={self._message!r}, value={self._value!r})"

    def __str__(self) -> str:
        return f"[{self._code.value}] {self._message} (value={self._value})"
