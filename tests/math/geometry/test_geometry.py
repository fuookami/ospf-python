"""Tests for ospf_python.math.geometry module."""

import math

from ospf_python.math.geometry import (
    Circle,
    Line2D,
    Point2D,
    Point3D,
    Rectangle,
    Vector2D,
    Vector3D,
    angle_between_vectors,
    rotate_vector,
)


class TestPoint2D:
    """Tests for Point2D."""

    def test_creation(self) -> None:
        """Test creating point."""
        p = Point2D(1.0, 2.0)
        assert p.x == 1.0
        assert p.y == 2.0

    def test_distance_to(self) -> None:
        """Test distance calculation."""
        p1 = Point2D(0, 0)
        p2 = Point2D(3, 4)
        assert p1.distance_to(p2) == 5.0

    def test_add_vector(self) -> None:
        """Test adding vector to point."""
        p = Point2D(1, 2)
        v = Vector2D(3, 4)
        result = p + v
        assert result.x == 4.0
        assert result.y == 6.0

    def test_sub_points(self) -> None:
        """Test subtracting points."""
        p1 = Point2D(3, 4)
        p2 = Point2D(1, 2)
        result = p1 - p2
        assert isinstance(result, Vector2D)
        assert result.x == 2.0
        assert result.y == 2.0


class TestVector2D:
    """Tests for Vector2D."""

    def test_creation(self) -> None:
        """Test creating vector."""
        v = Vector2D(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0

    def test_length(self) -> None:
        """Test vector length."""
        v = Vector2D(3, 4)
        assert v.length == 5.0

    def test_normalize(self) -> None:
        """Test normalization."""
        v = Vector2D(3, 4)
        n = v.normalize()
        assert abs(n.length - 1.0) < 1e-10
        assert abs(n.x - 0.6) < 1e-10
        assert abs(n.y - 0.8) < 1e-10

    def test_dot(self) -> None:
        """Test dot product."""
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        assert v1.dot(v2) == 11.0

    def test_cross(self) -> None:
        """Test cross product."""
        v1 = Vector2D(1, 0)
        v2 = Vector2D(0, 1)
        assert v1.cross(v2) == 1.0

    def test_add(self) -> None:
        """Test vector addition."""
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        result = v1 + v2
        assert result.x == 4.0
        assert result.y == 6.0

    def test_sub(self) -> None:
        """Test vector subtraction."""
        v1 = Vector2D(3, 4)
        v2 = Vector2D(1, 2)
        result = v1 - v2
        assert result.x == 2.0
        assert result.y == 2.0

    def test_mul_scalar(self) -> None:
        """Test scalar multiplication."""
        v = Vector2D(1, 2)
        result = v * 3
        assert result.x == 3.0
        assert result.y == 6.0

    def test_neg(self) -> None:
        """Test negation."""
        v = Vector2D(1, 2)
        result = -v
        assert result.x == -1.0
        assert result.y == -2.0


class TestPoint3D:
    """Tests for Point3D."""

    def test_creation(self) -> None:
        """Test creating point."""
        p = Point3D(1, 2, 3)
        assert p.x == 1.0
        assert p.y == 2.0
        assert p.z == 3.0

    def test_distance_to(self) -> None:
        """Test distance calculation."""
        p1 = Point3D(0, 0, 0)
        p2 = Point3D(1, 2, 2)
        assert p1.distance_to(p2) == 3.0


class TestVector3D:
    """Tests for Vector3D."""

    def test_creation(self) -> None:
        """Test creating vector."""
        v = Vector3D(1, 2, 3)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0

    def test_length(self) -> None:
        """Test vector length."""
        v = Vector3D(1, 2, 2)
        assert v.length == 3.0

    def test_dot(self) -> None:
        """Test dot product."""
        v1 = Vector3D(1, 2, 3)
        v2 = Vector3D(4, 5, 6)
        assert v1.dot(v2) == 32.0

    def test_cross(self) -> None:
        """Test cross product."""
        v1 = Vector3D(1, 0, 0)
        v2 = Vector3D(0, 1, 0)
        result = v1.cross(v2)
        assert result.x == 0.0
        assert result.y == 0.0
        assert result.z == 1.0


class TestLine2D:
    """Tests for Line2D."""

    def test_distance_to_point(self) -> None:
        """Test distance from line to point."""
        # Line: x = 0 (y-axis)
        line = Line2D(1, 0, 0)
        point = Point2D(3, 4)
        assert line.distance_to_point(point) == 3.0


class TestCircle:
    """Tests for Circle."""

    def test_creation(self) -> None:
        """Test creating circle."""
        c = Circle(Point2D(0, 0), 5.0)
        assert c.center.x == 0.0
        assert c.radius == 5.0

    def test_area(self) -> None:
        """Test area calculation."""
        c = Circle(Point2D(0, 0), 5.0)
        assert abs(c.area - math.pi * 25) < 1e-10

    def test_circumference(self) -> None:
        """Test circumference calculation."""
        c = Circle(Point2D(0, 0), 5.0)
        assert abs(c.circumference - 10 * math.pi) < 1e-10

    def test_contains(self) -> None:
        """Test contains."""
        c = Circle(Point2D(0, 0), 5.0)
        assert c.contains(Point2D(0, 0))
        assert c.contains(Point2D(3, 4))
        assert not c.contains(Point2D(10, 0))


class TestRectangle:
    """Tests for Rectangle."""

    def test_creation(self) -> None:
        """Test creating rectangle."""
        r = Rectangle(0, 0, 10, 20)
        assert r.x == 0
        assert r.width == 10
        assert r.height == 20

    def test_area(self) -> None:
        """Test area calculation."""
        r = Rectangle(0, 0, 10, 20)
        assert r.area == 200

    def test_perimeter(self) -> None:
        """Test perimeter calculation."""
        r = Rectangle(0, 0, 10, 20)
        assert r.perimeter == 60

    def test_contains(self) -> None:
        """Test contains."""
        r = Rectangle(0, 0, 10, 20)
        assert r.contains(Point2D(5, 10))
        assert not r.contains(Point2D(15, 10))


class TestAngleAndRotation:
    """Tests for angle and rotation functions."""

    def test_angle_between_vectors(self) -> None:
        """Test angle between vectors."""
        v1 = Vector2D(1, 0)
        v2 = Vector2D(0, 1)
        angle = angle_between_vectors(v1, v2)
        assert abs(angle - math.pi / 2) < 1e-10

    def test_rotate_vector(self) -> None:
        """Test vector rotation."""
        v = Vector2D(1, 0)
        rotated = rotate_vector(v, math.pi / 2)
        assert abs(rotated.x) < 1e-10
        assert abs(rotated.y - 1.0) < 1e-10
