"""Result 类型系统 / Result type system.

三参 sealed 结果类型：Result[T, C, E]，不得退化为 Union。
Three-parameter sealed result type: Result[T, C, E], must not degrade to Union.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from ospf_python.utils.error.error import Error

if TYPE_CHECKING:
    from ospf_python.utils.error.code import ErrorCode

# TypeVar 声明 / TypeVar declarations
T = TypeVar("T")
T2 = TypeVar("T2")
C = TypeVar("C")
E = TypeVar("E", bound=Error[Any])


class Result(ABC, Generic[T, C, E]):
    """三参密封结果类型 / Three-parameter sealed result type.

    泛型参数：
    - T: 成功值类型 / Success value type
    - C: 错误上下文类型 / Error context type
    - E: 错误类型（bound=Error）/ Error type (bound=Error)
    """

    @abstractmethod
    def is_ok(self) -> bool:
        """判断是否成功 / Check if result is success."""

    @abstractmethod
    def is_failed(self) -> bool:
        """判断是否失败 / Check if result is failure."""

    @abstractmethod
    def map(self, f: Callable[[T], T2]) -> Result[T2, C, E]:
        """映射成功值 / Map the success value."""

    @abstractmethod
    def map_err(self, f: Callable[[E], E]) -> Result[T, C, E]:
        """映射错误 / Map the error."""

    @abstractmethod
    def flat_map(self, f: Callable[[T], Result[T2, C, E]]) -> Result[T2, C, E]:
        """扁平化映射 / Flat map."""

    @abstractmethod
    def unwrap(self) -> T:
        """解包成功值（失败时抛异常）/ Unwrap success value (raises on failure)."""

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """解包或返回默认值 / Unwrap or return default."""

    @abstractmethod
    def on_failure(self, f: Callable[[E], None]) -> Result[T, C, E]:
        """失败时执行副作用 / Execute side effect on failure."""

    @abstractmethod
    def on_success(self, f: Callable[[T], None]) -> Result[T, C, E]:
        """成功时执行副作用 / Execute side effect on success."""


class ExResult(Result[T, C, E], ABC):
    """扩展结果类型 / Extended result type.

    在 Result 基础上增加 Warn 状态。
    Extends Result with Warn state.
    """

    @abstractmethod
    def is_warn(self) -> bool:
        """判断是否有警告 / Check if result has warning."""


@dataclass(frozen=True)
class Ok(Result[T, C, E]):
    """成功结果 / Success result.

    Args:
        value: 成功值 / Success value.
    """

    _value: T

    @property
    def value(self) -> T:
        """获取成功值 / Get success value."""
        return self._value

    def is_ok(self) -> bool:
        return True

    def is_failed(self) -> bool:
        return False

    def map(self, f: Callable[[T], T2]) -> Result[T2, C, E]:
        return Ok(f(self._value))

    def map_err(self, f: Callable[[E], E]) -> Result[T, C, E]:
        return cast("Result[T, C, E]", self)

    def flat_map(self, f: Callable[[T], Result[T2, C, E]]) -> Result[T2, C, E]:
        return f(self._value)

    def unwrap(self) -> T:
        return self._value

    def unwrap_or(self, default: T) -> T:
        return self._value

    def on_failure(self, f: Callable[[E], None]) -> Result[T, C, E]:
        return cast("Result[T, C, E]", self)

    def on_success(self, f: Callable[[T], None]) -> Result[T, C, E]:
        f(self._value)
        return cast("Result[T, C, E]", self)


@dataclass(frozen=True)
class Failed(Result[T, C, E]):
    """失败结果 / Failure result.

    Args:
        error: 单个错误 / Single error.
    """

    _error: E

    @property
    def error(self) -> E:
        """获取错误 / Get error."""
        return self._error

    def is_ok(self) -> bool:
        return False

    def is_failed(self) -> bool:
        return True

    def map(self, f: Callable[[T], T2]) -> Result[T2, C, E]:
        return cast("Result[T2, C, E]", self)

    def map_err(self, f: Callable[[E], E]) -> Result[T, C, E]:
        return Failed(f(self._error))

    def flat_map(self, f: Callable[[T], Result[T2, C, E]]) -> Result[T2, C, E]:
        return cast("Result[T2, C, E]", self)

    def unwrap(self) -> T:
        raise RuntimeError(f"unwrap() called on Failed: {self._error}")

    def unwrap_or(self, default: T) -> T:
        return default

    def on_failure(self, f: Callable[[E], None]) -> Result[T, C, E]:
        f(self._error)
        return cast("Result[T, C, E]", self)

    def on_success(self, f: Callable[[T], None]) -> Result[T, C, E]:
        return cast("Result[T, C, E]", self)


@dataclass(frozen=True)
class Fatal(Result[T, C, E]):
    """致命错误结果 / Fatal error result.

    Args:
        errors: 错误列表 / List of errors.
    """

    _errors: tuple[E, ...]

    @property
    def errors(self) -> tuple[E, ...]:
        """获取错误列表 / Get error list."""
        return self._errors

    def is_ok(self) -> bool:
        return False

    def is_failed(self) -> bool:
        return True

    def map(self, f: Callable[[T], T2]) -> Result[T2, C, E]:
        return cast("Result[T2, C, E]", self)

    def map_err(self, f: Callable[[E], E]) -> Result[T, C, E]:
        return Fatal(tuple(f(e) for e in self._errors))

    def flat_map(self, f: Callable[[T], Result[T2, C, E]]) -> Result[T2, C, E]:
        return cast("Result[T2, C, E]", self)

    def unwrap(self) -> T:
        raise RuntimeError(f"unwrap() called on Fatal: {self._errors}")

    def unwrap_or(self, default: T) -> T:
        return default

    def on_failure(self, f: Callable[[E], None]) -> Result[T, C, E]:
        for e in self._errors:
            f(e)
        return cast("Result[T, C, E]", self)

    def on_success(self, f: Callable[[T], None]) -> Result[T, C, E]:
        return cast("Result[T, C, E]", self)


@dataclass(frozen=True)
class Success(Result[None, C, E]):
    """无值成功结果 / Parameterless success result.

    等价于 Ok(None) 但为独立类型。
    Equivalent to Ok(None) but a distinct type.
    """

    def is_ok(self) -> bool:
        return True

    def is_failed(self) -> bool:
        return False

    def map(self, f: Callable[[None], T2]) -> Result[T2, C, E]:
        return Ok(f(None))

    def map_err(self, f: Callable[[E], E]) -> Result[None, C, E]:
        return self

    def flat_map(self, f: Callable[[None], Result[T2, C, E]]) -> Result[T2, C, E]:
        return f(None)

    def unwrap(self) -> None:
        return None

    def unwrap_or(self, default: None) -> None:
        return None

    def on_failure(self, f: Callable[[E], None]) -> Result[None, C, E]:
        return self

    def on_success(self, f: Callable[[None], None]) -> Result[None, C, E]:
        f(None)
        return self


@dataclass(frozen=True)
class Warn(ExResult[T, C, E]):
    """警告结果 / Warning result.

    同时包含成功值和警告错误。
    Contains both success value and warning error.

    Args:
        value: 成功值 / Success value.
        warning: 警告错误 / Warning error.
    """

    _value: T
    _warning: E

    @property
    def value(self) -> T:
        """获取成功值 / Get success value."""
        return self._value

    @property
    def warning(self) -> E:
        """获取警告 / Get warning."""
        return self._warning

    def is_ok(self) -> bool:
        return True

    def is_failed(self) -> bool:
        return False

    def is_warn(self) -> bool:
        return True

    def map(self, f: Callable[[T], T2]) -> ExResult[T2, C, E]:
        return Warn(f(self._value), self._warning)

    def map_err(self, f: Callable[[E], E]) -> ExResult[T, C, E]:
        return Warn(self._value, f(self._warning))

    def flat_map(self, f: Callable[[T], Result[T2, C, E]]) -> Result[T2, C, E]:
        return f(self._value)

    def unwrap(self) -> T:
        return self._value

    def unwrap_or(self, default: T) -> T:
        return self._value

    def on_failure(self, f: Callable[[E], None]) -> ExResult[T, C, E]:
        return self

    def on_success(self, f: Callable[[T], None]) -> ExResult[T, C, E]:
        f(self._value)
        return self


# 便捷工厂函数 / Convenience factory functions
def failed_from_code(
    code: ErrorCode,
    message: str,
) -> Failed[Any, Any, Any]:
    """从错误码创建失败结果 / Create Failed result from error code."""
    from ospf_python.utils.error.error import Err

    return Failed(Err(_code=code, _message=message))
