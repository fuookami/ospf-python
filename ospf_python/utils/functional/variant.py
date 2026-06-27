"""变体类型 / Variant types.

密封变体类型 Variant2..Variant7。
Sealed variant types Variant2..Variant7.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
T5 = TypeVar("T5")
T6 = TypeVar("T6")
T7 = TypeVar("T7")
Ret = TypeVar("Ret")


# ==================== Variant2 ====================


class Variant2(ABC, Generic[T1, T2]):
    """二元变体 / Two-element variant."""

    @abstractmethod
    def index(self) -> int:
        """获取当前分支索引 / Get current branch index."""

    @abstractmethod
    def match(
        self,
        handler1: Callable[[T1], Ret],
        handler2: Callable[[T2], Ret],
    ) -> Ret:
        """模式匹配 / Pattern match."""


@dataclass(frozen=True)
class V2Left(Variant2[T1, T2]):
    """Variant2 的第一个分支 / First branch of Variant2.

    Args:
        value: 值 / Value.
    """

    _value: T1

    @property
    def value(self) -> T1:
        return self._value

    def index(self) -> int:
        return 0

    def match(
        self,
        handler1: Callable[[T1], Ret],
        handler2: Callable[[T2], Ret],
    ) -> Ret:
        return handler1(self._value)


@dataclass(frozen=True)
class V2Right(Variant2[T1, T2]):
    """Variant2 的第二个分支 / Second branch of Variant2.

    Args:
        value: 值 / Value.
    """

    _value: T2

    @property
    def value(self) -> T2:
        return self._value

    def index(self) -> int:
        return 1

    def match(
        self,
        handler1: Callable[[T1], Ret],
        handler2: Callable[[T2], Ret],
    ) -> Ret:
        return handler2(self._value)


# ==================== Variant3 ====================


class Variant3(ABC, Generic[T1, T2, T3]):
    """三元变体 / Three-element variant."""

    @abstractmethod
    def index(self) -> int:
        """获取当前分支索引 / Get current branch index."""

    @abstractmethod
    def match(
        self,
        handler1: Callable[[T1], Ret],
        handler2: Callable[[T2], Ret],
        handler3: Callable[[T3], Ret],
    ) -> Ret:
        """模式匹配 / Pattern match."""


@dataclass(frozen=True)
class V3V1(Variant3[T1, T2, T3]):
    """Variant3 的第一个分支 / First branch of Variant3."""

    _value: T1

    @property
    def value(self) -> T1:
        return self._value

    def index(self) -> int:
        return 0

    def match(
        self,
        handler1: Callable[[T1], Ret],
        handler2: Callable[[T2], Ret],
        handler3: Callable[[T3], Ret],
    ) -> Ret:
        return handler1(self._value)


@dataclass(frozen=True)
class V3V2(Variant3[T1, T2, T3]):
    """Variant3 的第二个分支 / Second branch of Variant3."""

    _value: T2

    @property
    def value(self) -> T2:
        return self._value

    def index(self) -> int:
        return 1

    def match(
        self,
        handler1: Callable[[T1], Ret],
        handler2: Callable[[T2], Ret],
        handler3: Callable[[T3], Ret],
    ) -> Ret:
        return handler2(self._value)


@dataclass(frozen=True)
class V3V3(Variant3[T1, T2, T3]):
    """Variant3 的第三个分支 / Third branch of Variant3."""

    _value: T3

    @property
    def value(self) -> T3:
        return self._value

    def index(self) -> int:
        return 2

    def match(
        self,
        handler1: Callable[[T1], Ret],
        handler2: Callable[[T2], Ret],
        handler3: Callable[[T3], Ret],
    ) -> Ret:
        return handler3(self._value)


# ==================== Variant4 ====================


class Variant4(ABC, Generic[T1, T2, T3, T4]):
    """四元变体 / Four-element variant."""

    @abstractmethod
    def index(self) -> int:
        """获取当前分支索引 / Get current branch index."""

    @abstractmethod
    def match(
        self,
        handler1: Callable[[T1], Ret],
        handler2: Callable[[T2], Ret],
        handler3: Callable[[T3], Ret],
        handler4: Callable[[T4], Ret],
    ) -> Ret:
        """模式匹配 / Pattern match."""


@dataclass(frozen=True)
class V4V1(Variant4[T1, T2, T3, T4]):
    _value: T1

    @property
    def value(self) -> T1:
        return self._value

    def index(self) -> int:
        return 0

    def match(
        self,
        h1: Callable[[T1], Ret],
        h2: Callable[[T2], Ret],
        h3: Callable[[T3], Ret],
        h4: Callable[[T4], Ret],
    ) -> Ret:
        return h1(self._value)


@dataclass(frozen=True)
class V4V2(Variant4[T1, T2, T3, T4]):
    _value: T2

    @property
    def value(self) -> T2:
        return self._value

    def index(self) -> int:
        return 1

    def match(
        self,
        h1: Callable[[T1], Ret],
        h2: Callable[[T2], Ret],
        h3: Callable[[T3], Ret],
        h4: Callable[[T4], Ret],
    ) -> Ret:
        return h2(self._value)


@dataclass(frozen=True)
class V4V3(Variant4[T1, T2, T3, T4]):
    _value: T3

    @property
    def value(self) -> T3:
        return self._value

    def index(self) -> int:
        return 2

    def match(
        self,
        h1: Callable[[T1], Ret],
        h2: Callable[[T2], Ret],
        h3: Callable[[T3], Ret],
        h4: Callable[[T4], Ret],
    ) -> Ret:
        return h3(self._value)


@dataclass(frozen=True)
class V4V4(Variant4[T1, T2, T3, T4]):
    _value: T4

    @property
    def value(self) -> T4:
        return self._value

    def index(self) -> int:
        return 3

    def match(
        self,
        h1: Callable[[T1], Ret],
        h2: Callable[[T2], Ret],
        h3: Callable[[T3], Ret],
        h4: Callable[[T4], Ret],
    ) -> Ret:
        return h4(self._value)


# ==================== Variant5-7 简化别名 ====================
# Variant5-7 结构相同，用类型别名表达 / Same structure, expressed as aliases

Variant5 = Any  # Five-element variant alternative
Variant6 = Any  # Six-element variant alternative
Variant7 = Any  # Seven-element variant alternative
