"""线性空间协议 / Linear space protocols.

VectorSpace / NormedSpace / InnerProductSpace 线性空间层次。
VectorSpace / NormedSpace / InnerProductSpace hierarchy.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class VectorSpace(Protocol):
    """向量空间协议 / Vector space protocol.

    向量空间是定义在域上的加法群，支持标量乘法。
    A vector space is an additive group over a field
    with scalar multiplication.
    """

    def __add__(self: Self, other: Self) -> Self:
        """向量加法 / Vector addition."""

    def __sub__(self: Self, other: Self) -> Self:
        """向量减法 / Vector subtraction."""

    def __neg__(self: Self) -> Self:
        """向量取反 / Vector negation."""

    def __mul__(self: Self, scalar: float) -> Self:
        """标量乘法（右）/ Scalar multiplication (right)."""

    def __rmul__(self: Self, scalar: float) -> Self:
        """标量乘法（左）/ Scalar multiplication (left)."""


@runtime_checkable
class NormedSpace(VectorSpace, Protocol):
    """赋范空间协议 / Normed space protocol.

    赋范空间是定义了范数的向量空间。
    A normed space is a vector space with a norm.
    """

    @property
    def norm(self) -> float:
        """范数 / Norm (length)."""

    @property
    def norm_squared(self) -> float:
        """范数的平方 / Squared norm."""


@runtime_checkable
class InnerProductSpace(NormedSpace, Protocol):
    """内积空间协议 / Inner product space protocol.

    内积空间是定义了内积的赋范空间。
    An inner product space is a normed space
    with an inner product.
    """

    def dot(self: Self, other: Self) -> float:
        """内积 / Inner product (dot product)."""
