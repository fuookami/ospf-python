"""Result type for error handling without exceptions.

Provides Result[T] and its variants for the ospf-python framework.
All operations return Result instead of raising exceptions.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, Union

from ospf_python.utils.error import Err, Error, ErrorCode, ExErr

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """Successful result containing a value.

    成功结果，包含值。
    """

    value: T

    def is_ok(self) -> bool:
        """Check if this is an Ok result."""
        return True

    def is_failed(self) -> bool:
        """Check if this is a Failed result."""
        return False

    def map(self, fn: Callable[[T], U]) -> Ok[U] | Failed | Fatal:
        """Transform the success value.

        Args:
            fn: Transformation function.

        Returns:
            Transformed result.
        """
        return Ok(fn(self.value))

    def map_error(self, fn: Callable[[Error], Error]) -> Ok[T] | Failed | Fatal:
        """Transform the error (no-op for Ok).

        Args:
            fn: Error transformation function.

        Returns:
            Self (unchanged).
        """
        return self

    def on_failure(self, fn: Callable[[Error], Any]) -> Ok[T] | Failed | Fatal:
        """Execute side effect on failure (no-op for Ok).

        Args:
            fn: Side effect function.

        Returns:
            Self (unchanged).
        """
        return self

    def unwrap(self) -> T:
        """Unwrap the value.

        Returns:
            The contained value.
        """
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Unwrap the value or return default.

        Args:
            default: Default value.

        Returns:
            The contained value.
        """
        return self.value

    def __repr__(self) -> str:
        return f"Ok({self.value!r})"


@dataclass(frozen=True, slots=True)
class Failed:
    """Failed result containing a single error.

    失败结果，包含单个错误。
    """

    error: Error

    def is_ok(self) -> bool:
        """Check if this is an Ok result."""
        return False

    def is_failed(self) -> bool:
        """Check if this is a Failed result."""
        return True

    def map(self, fn: Callable[[Any], Any]) -> Ok[Any] | Failed | Fatal:
        """Transform the success value (no-op for Failed).

        Args:
            fn: Transformation function.

        Returns:
            Self (unchanged).
        """
        return self

    def map_error(self, fn: Callable[[Error], Error]) -> Ok[Any] | Failed | Fatal:
        """Transform the error.

        Args:
            fn: Error transformation function.

        Returns:
            New Failed with transformed error.
        """
        return Failed(fn(self.error))

    def on_failure(self, fn: Callable[[Error], Any]) -> Ok[Any] | Failed | Fatal:
        """Execute side effect on failure.

        Args:
            fn: Side effect function.

        Returns:
            Self (unchanged).
        """
        fn(self.error)
        return self

    def unwrap(self) -> Any:
        """Unwrap the value (raises ValueError).

        Raises:
            ValueError: Always, since this is a Failed result.
        """
        raise ValueError(f"Unwrap failed: {self.error}")

    def unwrap_or(self, default: Any) -> Any:
        """Unwrap the value or return default.

        Args:
            default: Default value.

        Returns:
            The default value.
        """
        return default

    def __repr__(self) -> str:
        return f"Failed({self.error!r})"


@dataclass(frozen=True, slots=True)
class Fatal:
    """Fatal result containing multiple errors.

    致命结果，包含多个错误。
    """

    errors: tuple[Error, ...]

    def __init__(self, *errors: Error) -> None:
        object.__setattr__(self, "errors", tuple(errors))

    def is_ok(self) -> bool:
        """Check if this is an Ok result."""
        return False

    def is_failed(self) -> bool:
        """Check if this is a Failed result."""
        return True

    def map(self, fn: Callable[[Any], Any]) -> Ok[Any] | Failed | Fatal:
        """Transform the success value (no-op for Fatal).

        Args:
            fn: Transformation function.

        Returns:
            Self (unchanged).
        """
        return self

    def map_error(self, fn: Callable[[Error], Error]) -> Ok[Any] | Failed | Fatal:
        """Transform the errors.

        Args:
            fn: Error transformation function.

        Returns:
            New Fatal with transformed errors.
        """
        return Fatal(*(fn(e) for e in self.errors))

    def on_failure(self, fn: Callable[[Error], Any]) -> Ok[Any] | Failed | Fatal:
        """Execute side effect on each failure.

        Args:
            fn: Side effect function.

        Returns:
            Self (unchanged).
        """
        for error in self.errors:
            fn(error)
        return self

    def unwrap(self) -> Any:
        """Unwrap the value (raises ValueError).

        Raises:
            ValueError: Always, since this is a Fatal result.
        """
        raise ValueError(f"Unwrap fatal: {self.errors}")

    def unwrap_or(self, default: Any) -> Any:
        """Unwrap the value or return default.

        Args:
            default: Default value.

        Returns:
            The default value.
        """
        return default

    def __repr__(self) -> str:
        return f"Fatal({self.errors!r})"


# Result type alias
Result = Union[Ok[T], Failed, Fatal]


def ok(value: T) -> Ok[T]:
    """Create a successful result.

    Args:
        value: The success value.

    Returns:
        Ok result containing the value.
    """
    return Ok(value)


def failed(
    code_or_error: ErrorCode | Error,
    message: str = "",
    value: Any = None,
) -> Failed:
    """Create a failed result.

    Args:
        code_or_error: Error code or Error object.
        message: Error message (required if code_or_error is ErrorCode).
        value: Optional associated value.

    Returns:
        Failed result.
    """
    if isinstance(code_or_error, Error):
        return Failed(code_or_error)
    error = (
        ExErr(code_or_error, message, value)
        if value is not None
        else Err(code_or_error, message)
    )
    return Failed(error)


def fatal(
    code_or_errors: ErrorCode | list[Error] | tuple[Error, ...],
    message: str = "",
    value: Any = None,
) -> Fatal:
    """Create a fatal result.

    Args:
        code_or_errors: Error code, list of errors, or tuple of errors.
        message: Error message (required if code_or_errors is ErrorCode).
        value: Optional associated value.

    Returns:
        Fatal result.
    """
    if isinstance(code_or_errors, (list, tuple)):
        return Fatal(*code_or_errors)
    error = (
        ExErr(code_or_errors, message, value)
        if value is not None
        else Err(code_or_errors, message)
    )
    return Fatal(error)


@dataclass(frozen=True, slots=True)
class Warn(Generic[T]):
    """Warning result containing a value and a warning.

    警告结果，同时包含值和警告。
    """

    value: T
    warning: Error

    def is_ok(self) -> bool:
        """Check if this is an Ok result."""
        return True

    def is_failed(self) -> bool:
        """Check if this is a Failed result."""
        return False

    def map(self, fn: Callable[[T], U]) -> Warn[U]:
        """Transform the success value.

        Args:
            fn: Transformation function.

        Returns:
            Transformed Warn result.
        """
        return Warn(fn(self.value), self.warning)

    def map_error(self, fn: Callable[[Error], Error]) -> Warn[T]:
        """Transform the warning.

        Args:
            fn: Error transformation function.

        Returns:
            New Warn with transformed warning.
        """
        return Warn(self.value, fn(self.warning))

    def on_failure(self, fn: Callable[[Error], Any]) -> Warn[T]:
        """Execute side effect on warning.

        Args:
            fn: Side effect function.

        Returns:
            Self (unchanged).
        """
        fn(self.warning)
        return self

    def unwrap(self) -> T:
        """Unwrap the value.

        Returns:
            The contained value.
        """
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Unwrap the value or return default.

        Args:
            default: Default value.

        Returns:
            The contained value.
        """
        return self.value

    def __repr__(self) -> str:
        return f"Warn(value={self.value!r}, warning={self.warning!r})"


# ExResult type alias (includes Warn)
ExResult = Union[Ok[T], Failed, Fatal, Warn[T]]


def warn(value: T, code_or_error: ErrorCode | Error, message: str = "") -> Warn[T]:
    """Create a warning result.

    Args:
        value: The value.
        code_or_error: Error code or Error object.
        message: Warning message (required if code_or_error is ErrorCode).

    Returns:
        Warn result.
    """
    if isinstance(code_or_error, Error):
        warning = code_or_error
    else:
        warning = Err(code_or_error, message)
    return Warn(value, warning)


# Type aliases
Try = Result[None]
"""Result with no meaningful return value."""

Ret = Result[T]
"""Result with a return value."""


def run(
    *blocks: Callable[[], Ok[Any] | Failed | Fatal],
    last_block: Callable[[], Ok[U] | Failed | Fatal] | None = None,
) -> Ok[U] | Failed | Fatal:
    """Execute multiple operations sequentially, short-circuiting on failure.

    Args:
        *blocks: Operations to execute.
        last_block: Final operation whose result is returned.

    Returns:
        Result of last_block, or first failure encountered.
    """
    for block in blocks:
        result = block()
        if result.is_failed():
            return result
    if last_block is not None:
        return last_block()
    return Ok(None)  # type: ignore[arg-type]


def pipe(
    initial: Ok[T] | Failed | Fatal,
    *fns: Callable[[T], Ok[Any] | Failed | Fatal],
    last_fn: Callable[[Any], Ok[U] | Failed | Fatal] | None = None,
) -> Ok[U] | Failed | Fatal:
    """Pipe a result through multiple transformations.

    Args:
        initial: Initial result.
        *fns: Transformation functions.
        last_fn: Final transformation whose result is returned.

    Returns:
        Result of last_fn, or first failure encountered.
    """
    current: Ok[Any] | Failed | Fatal = initial
    for fn in fns:
        if current.is_failed():
            return current
        current = fn(current.unwrap())
    if last_fn is not None:
        if current.is_failed():
            return current
        return last_fn(current.unwrap())
    return current
