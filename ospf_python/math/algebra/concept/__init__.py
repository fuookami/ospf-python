"""Algebraic concepts module.

Provides algebraic structure interfaces: Group, Ring, Field.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ospf_python.math.algebra.number import RealNumber

V = TypeVar("V", bound=RealNumber)


class Group(ABC, Generic[V]):
    """Group interface: set with associative binary operation, identity, inverse.

    群接口：集合 + 结合二元运算 + 单位元 + 逆元。
    """

    @abstractmethod
    def identity(self) -> V:
        """Get identity element."""
        ...

    @abstractmethod
    def operate(self, a: V, b: V) -> V:
        """Apply group operation."""
        ...

    @abstractmethod
    def inverse(self, a: V) -> V:
        """Get inverse element."""
        ...


class AbelianGroup(Group[V]):
    """Abelian group: group with commutative operation.

    阿贝尔群：交换群。
    """

    pass


class Ring(ABC, Generic[V]):
    """Ring: set with two operations (addition, multiplication).

    环：集合 + 加法 + 乘法。
    """

    @abstractmethod
    def zero(self) -> V:
        """Get additive identity."""
        ...

    @abstractmethod
    def one(self) -> V:
        """Get multiplicative identity."""
        ...

    @abstractmethod
    def add(self, a: V, b: V) -> V:
        """Add two elements."""
        ...

    @abstractmethod
    def multiply(self, a: V, b: V) -> V:
        """Multiply two elements."""
        ...

    @abstractmethod
    def negate(self, a: V) -> V:
        """Negate element."""
        ...


class Field(ABC, Generic[V]):
    """Field: ring where every non-zero element has multiplicative inverse.

    域：每个非零元素都有乘法逆元的环。
    """

    @abstractmethod
    def zero(self) -> V:
        """Get additive identity."""
        ...

    @abstractmethod
    def one(self) -> V:
        """Get multiplicative identity."""
        ...

    @abstractmethod
    def add(self, a: V, b: V) -> V:
        """Add two elements."""
        ...

    @abstractmethod
    def multiply(self, a: V, b: V) -> V:
        """Multiply two elements."""
        ...

    @abstractmethod
    def negate(self, a: V) -> V:
        """Negate element."""
        ...

    @abstractmethod
    def reciprocal(self, a: V) -> V:
        """Get multiplicative inverse."""
        ...
