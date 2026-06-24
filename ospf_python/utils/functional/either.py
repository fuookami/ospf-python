"""Either 类型 / Either type.

密封二选一类型：Either[L, R]。
Sealed disjunction type: Either[L, R].
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

L = TypeVar("L")
R = TypeVar("R")
L2 = TypeVar("L2")
R2 = TypeVar("R2")
Ret = TypeVar("Ret")


class Either(ABC, Generic[L, R]):
    """密封二选一类型 / Sealed disjunction type.

    要么是 Left[L]，要么是 Right[R]。
    Either Left[L] or Right[R].
    """

    @abstractmethod
    def is_left(self) -> bool:
        """判断是否为 Left / Check if Left."""

    @abstractmethod
    def is_right(self) -> bool:
        """判断是否为 Right / Check if Right."""

    @abstractmethod
    def map(self, f: Callable[[R], R2]) -> Either[L, R2]:
        """映射 Right 值 / Map the Right value."""

    @abstractmethod
    def map_left(self, f: Callable[[L], L2]) -> Either[L2, R]:
        """映射 Left 值 / Map the Left value."""

    @abstractmethod
    def fold(self, f_left: Callable[[L], Ret], f_right: Callable[[R], Ret]) -> Ret:
        """折叠 / Fold: apply f_left to Left, f_right to Right."""


@dataclass(frozen=True)
class Left(Either[L, R]):
    """Left 分支 / Left branch.

    Args:
        value: Left 值 / Left value.
    """

    _value: L

    @property
    def value(self) -> L:
        """获取 Left 值 / Get Left value."""
        return self._value

    def is_left(self) -> bool:
        return True

    def is_right(self) -> bool:
        return False

    def map(self, f: Callable[[R], R2]) -> Either[L, R2]:
        return Left(self._value)

    def map_left(self, f: Callable[[L], L2]) -> Either[L2, R]:
        return Left(f(self._value))

    def fold(self, f_left: Callable[[L], Ret], f_right: Callable[[R], Ret]) -> Ret:
        return f_left(self._value)


@dataclass(frozen=True)
class Right(Either[L, R]):
    """Right 分支 / Right branch.

    Args:
        value: Right 值 / Right value.
    """

    _value: R

    @property
    def value(self) -> R:
        """获取 Right 值 / Get Right value."""
        return self._value

    def is_left(self) -> bool:
        return False

    def is_right(self) -> bool:
        return True

    def map(self, f: Callable[[R], R2]) -> Either[L, R2]:
        return Right(f(self._value))

    def map_left(self, f: Callable[[L], L2]) -> Either[L2, R]:
        return Right(self._value)

    def fold(self, f_left: Callable[[L], Ret], f_right: Callable[[R], Ret]) -> Ret:
        return f_right(self._value)
