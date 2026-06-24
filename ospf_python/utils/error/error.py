"""错误类型层次结构 / Error type hierarchy.

对应 Kotlin 端 Error<out C : Any> sealed class 体系。
Mirrors the Kotlin Error<out C : Any> sealed class hierarchy.
"""

from __future__ import annotations

import abc
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ospf_python.utils.error.code import ErrorCode

# C: 错误分类类型（协变） / Error category type (covariant)
C = TypeVar("C", covariant=True)

# T: 附带值类型 / Associated value type
T = TypeVar("T")


class Error(abc.ABC, Generic[C]):
    """错误基类（抽象） / Abstract base class for errors.

    所有错误类型的公共接口。泛型参数 C 表示错误分类。
    Common interface for all error types. The generic parameter C
    represents the error category.

    Attributes:
        code: 错误码 / The error code.
        message: 错误信息 / The error message.
    """

    @property
    @abc.abstractmethod
    def code(self) -> ErrorCode:
        """获取错误码 / Get the error code."""
        ...

    @property
    @abc.abstractmethod
    def message(self) -> str:
        """获取错误信息 / Get the error message."""
        ...

    def __str__(self) -> str:
        return f"[{self.code.name}] {self.message}"


@dataclass(frozen=True)
class Err(Error[C]):
    """基本错误 / Basic error.

    携带错误码和即时计算的错误信息。
    Carries an error code and an eagerly computed message.

    Attributes:
        _code: 错误码 / The error code.
        _message: 错误信息 / The error message.
    """

    _code: ErrorCode
    _message: str

    @property
    def code(self) -> ErrorCode:
        """获取错误码 / Get the error code."""
        return self._code

    @property
    def message(self) -> str:
        """获取错误信息 / Get the error message."""
        return self._message


@dataclass(frozen=True)
class LazyErr(Error[C]):
    """惰性错误 / Lazy error.

    错误信息通过可调用对象延迟计算，避免不必要的字符串拼接。
    The message is lazily computed via a callable to avoid
    unnecessary string concatenation.

    Attributes:
        _code: 错误码 / The error code.
        _message_fn: 返回错误信息的可调用对象 / Callable returning
            the error message.
    """

    _code: ErrorCode
    _message_fn: Callable[[], str]

    @property
    def code(self) -> ErrorCode:
        """获取错误码 / Get the error code."""
        return self._code

    @property
    def message(self) -> str:
        """获取错误信息（惰性求值） / Get the error message (lazy evaluation)."""
        return self._message_fn()


@dataclass(frozen=True)
class ExErr(Error[C], Generic[C, T]):
    """附带值的错误 / Error with an associated value.

    除错误码和信息外，还携带一个类型为 T 的关联值。
    In addition to code and message, carries an associated
    value of type T.

    Attributes:
        _code: 错误码 / The error code.
        _message: 错误信息 / The error message.
        value: 关联值 / The associated value.
    """

    _code: ErrorCode
    _message: str
    value: T

    @property
    def code(self) -> ErrorCode:
        """获取错误码 / Get the error code."""
        return self._code

    @property
    def message(self) -> str:
        """获取错误信息 / Get the error message."""
        return self._message


@dataclass(frozen=True)
class LazyExErr(Error[C], Generic[C, T]):
    """惰性附带值的错误 / Lazy error with an associated value.

    错误信息延迟计算，同时携带一个类型为 T 的关联值。
    The message is lazily computed, and an associated value
    of type T is carried alongside.

    Attributes:
        _code: 错误码 / The error code.
        _message_fn: 返回错误信息的可调用对象 / Callable returning
            the error message.
        value: 关联值 / The associated value.
    """

    _code: ErrorCode
    _message_fn: Callable[[], str]
    value: T

    @property
    def code(self) -> ErrorCode:
        """获取错误码 / Get the error code."""
        return self._code

    @property
    def message(self) -> str:
        """获取错误信息（惰性求值） / Get the error message (lazy evaluation)."""
        return self._message_fn()


@dataclass(frozen=True)
class ApplicationException(Error[str]):
    """应用级异常 / Application-level exception.

    固定 C=str 的具体错误类型，用于应用层错误。
    A concrete error type with C=str, used for application-level
    errors.

    Attributes:
        _code: 错误码 / The error code.
        _message: 错误信息 / The error message.
    """

    _code: ErrorCode
    _message: str

    @property
    def code(self) -> ErrorCode:
        """获取错误码 / Get the error code."""
        return self._code

    @property
    def message(self) -> str:
        """获取错误信息 / Get the error message."""
        return self._message
