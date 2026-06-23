"""Geometry module.

Provides geometric primitives and operations: points, vectors, lines, shapes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TypeVar

from ospf_python.math.algebra.number import RealNumber

V = TypeVar("V", bound=RealNumber)


@dataclass(frozen=True, slots=True)
class Point2D:
    """2D point.

    二维点。
    """

    x: float
    y: float

    def distance_to(self, other: Point2D) -> float:
        """Compute distance to another point.

        Args:
            other: Other point.

        Returns:
            Distance.
        """
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __add__(self, other: Vector2D) -> Point2D:
        """Add vector to point."""
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point2D) -> Vector2D:
        """Subtract points to get vector."""
        return Vector2D(self.x - other.x, self.y - other.y)


@dataclass(frozen=True, slots=True)
class Vector2D:
    """2D vector.

    二维向量。
    """

    x: float
    y: float

    @property
    def length(self) -> float:
        """Get vector length."""
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self) -> Vector2D:
        """Normalize vector.

        Returns:
            Unit vector.
        """
        length = self.length
        if length == 0:
            return Vector2D(0, 0)
        return Vector2D(self.x / length, self.y / length)

    def dot(self, other: Vector2D) -> float:
        """Dot product.

        Args:
            other: Other vector.

        Returns:
            Dot product.
        """
        return self.x * other.x + self.y * other.y

    def cross(self, other: Vector2D) -> float:
        """Cross product (z-component).

        Args:
            other: Other vector.

        Returns:
            Cross product.
        """
        return self.x * other.y - self.y * other.x

    def __add__(self, other: Vector2D) -> Vector2D:
        """Add vectors."""
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        """Subtract vectors."""
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2D:
        """Multiply by scalar."""
        return Vector2D(self.x * scalar, self.y * scalar)

    def __neg__(self) -> Vector2D:
        """Negate vector."""
        return Vector2D(-self.x, -self.y)


@dataclass(frozen=True, slots=True)
class Point3D:
    """3D point.

    三维点。
    """

    x: float
    y: float
    z: float

    def distance_to(self, other: Point3D) -> float:
        """Compute distance to another point.

        Args:
            other: Other point.

        Returns:
            Distance.
        """
        return math.sqrt(
            (self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2
        )

    def __add__(self, other: Vector3D) -> Point3D:
        """Add vector to point."""
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Point3D) -> Vector3D:
        """Subtract points to get vector."""
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)


@dataclass(frozen=True, slots=True)
class Vector3D:
    """3D vector.

    三维向量。
    """

    x: float
    y: float
    z: float

    @property
    def length(self) -> float:
        """Get vector length."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> Vector3D:
        """Normalize vector.

        Returns:
            Unit vector.
        """
        length = self.length
        if length == 0:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x / length, self.y / length, self.z / length)

    def dot(self, other: Vector3D) -> float:
        """Dot product.

        Args:
            other: Other vector.

        Returns:
            Dot product.
        """
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vector3D) -> Vector3D:
        """Cross product.

        Args:
            other: Other vector.

        Returns:
            Cross product vector.
        """
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def __add__(self, other: Vector3D) -> Vector3D:
        """Add vectors."""
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector3D) -> Vector3D:
        """Subtract vectors."""
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vector3D:
        """Multiply by scalar."""
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def __neg__(self) -> Vector3D:
        """Negate vector."""
        return Vector3D(-self.x, -self.y, -self.z)


@dataclass(frozen=True, slots=True)
class Line2D:
    """2D line (ax + by + c = 0).

    二维直线。
    """

    a: float
    b: float
    c: float

    def distance_to_point(self, point: Point2D) -> float:
        """Compute distance from line to point.

        Args:
            point: Point.

        Returns:
            Distance.
        """
        return abs(self.a * point.x + self.b * point.y + self.c) / math.sqrt(
            self.a**2 + self.b**2
        )


@dataclass(frozen=True, slots=True)
class Circle:
    """Circle.

    圆。
    """

    center: Point2D
    radius: float

    @property
    def area(self) -> float:
        """Get circle area."""
        return math.pi * self.radius**2

    @property
    def circumference(self) -> float:
        """Get circle circumference."""
        return 2 * math.pi * self.radius

    def contains(self, point: Point2D) -> bool:
        """Check if circle contains point.

        Args:
            point: Point to check.

        Returns:
            True if point is inside circle.
        """
        return self.center.distance_to(point) <= self.radius


@dataclass(frozen=True, slots=True)
class Rectangle:
    """Rectangle (axis-aligned).

    矩形（轴对齐）。
    """

    x: float
    y: float
    width: float
    height: float

    @property
    def area(self) -> float:
        """Get rectangle area."""
        return self.width * self.height

    @property
    def perimeter(self) -> float:
        """Get rectangle perimeter."""
        return 2 * (self.width + self.height)

    def contains(self, point: Point2D) -> bool:
        """Check if rectangle contains point.

        Args:
            point: Point to check.

        Returns:
            True if point is inside rectangle.
        """
        return (
            self.x <= point.x <= self.x + self.width
            and self.y <= point.y <= self.y + self.height
        )


def angle_between_vectors(v1: Vector2D, v2: Vector2D) -> float:
    """Compute angle between two 2D vectors.

    Args:
        v1: First vector.
        v2: Second vector.

    Returns:
        Angle in radians.
    """
    dot = v1.dot(v2)
    det = v1.cross(v2)
    return math.atan2(det, dot)


def rotate_vector(v: Vector2D, angle: float) -> Vector2D:
    """Rotate 2D vector by angle.

    Args:
        v: Vector to rotate.
        angle: Rotation angle in radians.

    Returns:
        Rotated vector.
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return Vector2D(
        v.x * cos_a - v.y * sin_a,
        v.x * sin_a + v.y * cos_a,
    )
