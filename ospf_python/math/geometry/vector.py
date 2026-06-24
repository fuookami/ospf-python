"""向量类型。

Vector type for 2D geometric operations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Vector:
    """二维向量，不可变。

    Immutable 2D vector.

    Attributes:
        x: X 分量。/ X component.
        y: Y 分量。/ Y component.
    """

    x: float
    y: float

    def magnitude(self) -> float:
        """计算向量长度。

        Compute vector magnitude.

        Returns:
            向量长度。/ Vector magnitude.
        """
        return math.hypot(self.x, self.y)

    def normalize(self) -> Vector:
        """归一化向量。

        Normalize the vector.

        Returns:
            单位向量；零向量返回自身。
            Unit vector; zero vector returns itself.
        """
        mag = self.magnitude()
        if mag == 0.0:
            return Vector(x=0.0, y=0.0)
        return Vector(x=self.x / mag, y=self.y / mag)

    def dot(self, other: Vector) -> float:
        """计算点积。

        Compute dot product.

        Args:
            other: 另一个向量。/ Another vector.

        Returns:
            点积值。/ Dot product value.
        """
        return self.x * other.x + self.y * other.y

    def cross(self, other: Vector) -> float:
        """计算二维叉积（标量）。

        Compute 2D cross product (scalar).

        Args:
            other: 另一个向量。/ Another vector.

        Returns:
            叉积标量值。/ Cross product scalar.
        """
        return self.x * other.y - self.y * other.x

    def __add__(self, other: Vector) -> Vector:
        """向量加法。/ Vector addition."""
        return Vector(
            x=self.x + other.x,
            y=self.y + other.y,
        )

    def __sub__(self, other: Vector) -> Vector:
        """向量减法。/ Vector subtraction."""
        return Vector(
            x=self.x - other.x,
            y=self.y - other.y,
        )

    def __mul__(self, scalar: float) -> Vector:
        """标量乘法。/ Scalar multiplication."""
        return Vector(
            x=self.x * scalar,
            y=self.y * scalar,
        )

    def __neg__(self) -> Vector:
        """取反。/ Negation."""
        return Vector(x=-self.x, y=-self.y)

    def __repr__(self) -> str:
        """字符串表示。/ String representation."""
        return f"Vector({self.x}, {self.y})"
