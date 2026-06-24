"""几何图元模块测试。

Geometry primitives module tests.

测试 Point、Vector、Box、Circle、Triangle 等几何图元。
Tests Point, Vector, Box, Circle, Triangle
and other geometric primitives.
"""

from __future__ import annotations

import math

from ospf_python.math.geometry.axis2 import Axis2
from ospf_python.math.geometry.axis3 import Axis3
from ospf_python.math.geometry.axis_permutation2 import AxisPermutation2
from ospf_python.math.geometry.axis_permutation3 import AxisPermutation3
from ospf_python.math.geometry.axis_plane3 import AxisPlane3
from ospf_python.math.geometry.box2 import Box2
from ospf_python.math.geometry.box3 import Box3
from ospf_python.math.geometry.circle import Circle
from ospf_python.math.geometry.cuboid3 import Cuboid3
from ospf_python.math.geometry.cuboid3_view import Cuboid3View
from ospf_python.math.geometry.cylinder3 import Cylinder3
from ospf_python.math.geometry.dimension import Dimension
from ospf_python.math.geometry.distance import (
    distance,
    distance3,
    distance_squared,
    manhattan_distance,
)
from ospf_python.math.geometry.edge import Edge
from ospf_python.math.geometry.placement2 import Placement2
from ospf_python.math.geometry.placement3 import Placement3
from ospf_python.math.geometry.plane_frame3 import PlaneFrame3
from ospf_python.math.geometry.point import Point, Point3
from ospf_python.math.geometry.projection2 import Projection2
from ospf_python.math.geometry.quadrilateral import Quadrilateral
from ospf_python.math.geometry.quantity_ops import QuantityOps
from ospf_python.math.geometry.rectangle import Rectangle
from ospf_python.math.geometry.shape3 import Shape3
from ospf_python.math.geometry.triangle import Triangle
from ospf_python.math.geometry.triangulation import triangulate
from ospf_python.math.geometry.vector import Vector

# ── Point ──────────────────────────────────────────────────────


class TestPoint:
    """二维点测试。"""

    def test_creation(self) -> None:
        """创建二维点。/ Create 2D point."""
        p = Point(x=1.0, y=2.0)
        assert p.x == 1.0
        assert p.y == 2.0

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        p = Point(x=3.0, y=4.0)
        assert "Point" in repr(p)

    def test_equality(self) -> None:
        """相等比较。/ Equality."""
        a = Point(x=1.0, y=2.0)
        b = Point(x=1.0, y=2.0)
        assert a == b


class TestPoint3:
    """三维点测试。"""

    def test_creation(self) -> None:
        """创建三维点。/ Create 3D point."""
        p = Point3(x=1.0, y=2.0, z=3.0)
        assert p.x == 1.0
        assert p.y == 2.0
        assert p.z == 3.0


# ── Distance ──────────────────────────────────────────────────


class TestDistance:
    """距离函数测试。"""

    def test_euclidean(self) -> None:
        """欧氏距离。/ Euclidean distance."""
        p1 = Point(x=0.0, y=0.0)
        p2 = Point(x=3.0, y=4.0)
        assert distance(p1, p2) == 5.0

    def test_distance_squared(self) -> None:
        """距离平方。/ Squared distance."""
        p1 = Point(x=0.0, y=0.0)
        p2 = Point(x=3.0, y=4.0)
        assert distance_squared(p1, p2) == 25.0

    def test_manhattan(self) -> None:
        """曼哈顿距离。/ Manhattan distance."""
        p1 = Point(x=1.0, y=2.0)
        p2 = Point(x=4.0, y=6.0)
        assert manhattan_distance(p1, p2) == 7.0

    def test_distance3(self) -> None:
        """三维欧氏距离。/ 3D Euclidean distance."""
        p1 = Point3(x=0.0, y=0.0, z=0.0)
        p2 = Point3(x=1.0, y=2.0, z=2.0)
        assert distance3(p1, p2) == 3.0


# ── Vector ─────────────────────────────────────────────────────


class TestVector:
    """向量测试。"""

    def test_creation(self) -> None:
        """创建向量。/ Create vector."""
        v = Vector(x=3.0, y=4.0)
        assert v.x == 3.0
        assert v.y == 4.0

    def test_magnitude(self) -> None:
        """向量长度。/ Vector magnitude."""
        v = Vector(x=3.0, y=4.0)
        assert v.magnitude() == 5.0

    def test_normalize(self) -> None:
        """归一化。/ Normalize."""
        v = Vector(x=3.0, y=4.0)
        n = v.normalize()
        assert abs(n.magnitude() - 1.0) < 1e-10

    def test_normalize_zero(self) -> None:
        """零向量归一化。/ Zero vector normalize."""
        v = Vector(x=0.0, y=0.0)
        n = v.normalize()
        assert n.x == 0.0
        assert n.y == 0.0

    def test_dot(self) -> None:
        """点积。/ Dot product."""
        v1 = Vector(x=1.0, y=0.0)
        v2 = Vector(x=0.0, y=1.0)
        assert v1.dot(v2) == 0.0

    def test_cross(self) -> None:
        """叉积。/ Cross product."""
        v1 = Vector(x=1.0, y=0.0)
        v2 = Vector(x=0.0, y=1.0)
        assert v1.cross(v2) == 1.0

    def test_add(self) -> None:
        """向量加法。/ Vector addition."""
        v1 = Vector(x=1.0, y=2.0)
        v2 = Vector(x=3.0, y=4.0)
        result = v1 + v2
        assert result.x == 4.0
        assert result.y == 6.0

    def test_sub(self) -> None:
        """向量减法。/ Vector subtraction."""
        v1 = Vector(x=5.0, y=3.0)
        v2 = Vector(x=2.0, y=1.0)
        result = v1 - v2
        assert result.x == 3.0
        assert result.y == 2.0

    def test_scalar_mul(self) -> None:
        """标量乘法。/ Scalar multiplication."""
        v = Vector(x=2.0, y=3.0)
        result = v * 2.0
        assert result.x == 4.0
        assert result.y == 6.0

    def test_neg(self) -> None:
        """取反。/ Negation."""
        v = Vector(x=1.0, y=-2.0)
        result = -v
        assert result.x == -1.0
        assert result.y == 2.0


# ── Box2 ───────────────────────────────────────────────────────


class TestBox2:
    """二维包围盒测试。"""

    def test_contains_inside(self) -> None:
        """包含内部点。/ Contains inside point."""
        box = Box2(
            min_point=Point(x=0.0, y=0.0),
            max_point=Point(x=10.0, y=10.0),
        )
        assert box.contains(Point(x=5.0, y=5.0))

    def test_contains_outside(self) -> None:
        """不包含外部点。/ Not contains outside point."""
        box = Box2(
            min_point=Point(x=0.0, y=0.0),
            max_point=Point(x=10.0, y=10.0),
        )
        assert not box.contains(Point(x=15.0, y=5.0))

    def test_contains_boundary(self) -> None:
        """包含边界点。/ Contains boundary point."""
        box = Box2(
            min_point=Point(x=0.0, y=0.0),
            max_point=Point(x=10.0, y=10.0),
        )
        assert box.contains(Point(x=0.0, y=0.0))
        assert box.contains(Point(x=10.0, y=10.0))

    def test_area(self) -> None:
        """面积。/ Area."""
        box = Box2(
            min_point=Point(x=0.0, y=0.0),
            max_point=Point(x=3.0, y=4.0),
        )
        assert box.area() == 12.0

    def test_center(self) -> None:
        """中心点。/ Center."""
        box = Box2(
            min_point=Point(x=0.0, y=0.0),
            max_point=Point(x=10.0, y=10.0),
        )
        c = box.center()
        assert c.x == 5.0
        assert c.y == 5.0


# ── Box3 ───────────────────────────────────────────────────────


class TestBox3:
    """三维包围盒测试。"""

    def test_contains_inside(self) -> None:
        """包含内部点。/ Contains inside point."""
        box = Box3(
            min_point=Point3(x=0.0, y=0.0, z=0.0),
            max_point=Point3(x=10.0, y=10.0, z=10.0),
        )
        assert box.contains(Point3(x=5.0, y=5.0, z=5.0))

    def test_contains_outside(self) -> None:
        """不包含外部点。/ Not contains outside point."""
        box = Box3(
            min_point=Point3(x=0.0, y=0.0, z=0.0),
            max_point=Point3(x=10.0, y=10.0, z=10.0),
        )
        assert not box.contains(
            Point3(x=5.0, y=5.0, z=15.0),
        )

    def test_volume(self) -> None:
        """体积。/ Volume."""
        box = Box3(
            min_point=Point3(x=0.0, y=0.0, z=0.0),
            max_point=Point3(x=2.0, y=3.0, z=4.0),
        )
        assert box.volume() == 24.0

    def test_center(self) -> None:
        """中心点。/ Center."""
        box = Box3(
            min_point=Point3(x=0.0, y=0.0, z=0.0),
            max_point=Point3(x=10.0, y=10.0, z=10.0),
        )
        c = box.center()
        assert c.x == 5.0
        assert c.y == 5.0
        assert c.z == 5.0


# ── Circle ─────────────────────────────────────────────────────


class TestCircle:
    """圆测试。"""

    def test_area(self) -> None:
        """面积。/ Area."""
        c = Circle(center=Point(x=0.0, y=0.0), radius=1.0)
        assert abs(c.area() - math.pi) < 1e-10

    def test_circumference(self) -> None:
        """周长。/ Circumference."""
        c = Circle(center=Point(x=0.0, y=0.0), radius=1.0)
        assert abs(c.circumference() - 2 * math.pi) < 1e-10

    def test_contains_inside(self) -> None:
        """包含内部点。/ Contains inside point."""
        c = Circle(center=Point(x=0.0, y=0.0), radius=5.0)
        assert c.contains(Point(x=3.0, y=0.0))

    def test_contains_outside(self) -> None:
        """不包含外部点。/ Not contains outside point."""
        c = Circle(center=Point(x=0.0, y=0.0), radius=5.0)
        assert not c.contains(Point(x=6.0, y=0.0))

    def test_contains_boundary(self) -> None:
        """包含边界点。/ Contains boundary point."""
        c = Circle(center=Point(x=0.0, y=0.0), radius=5.0)
        assert c.contains(Point(x=5.0, y=0.0))


# ── Triangle ──────────────────────────────────────────────────


class TestTriangle:
    """三角形测试。"""

    def test_area(self) -> None:
        """面积。/ Area."""
        t = Triangle(
            v1=Point(x=0.0, y=0.0),
            v2=Point(x=4.0, y=0.0),
            v3=Point(x=0.0, y=3.0),
        )
        assert t.area() == 6.0

    def test_contains_inside(self) -> None:
        """包含内部点。/ Contains inside point."""
        t = Triangle(
            v1=Point(x=0.0, y=0.0),
            v2=Point(x=10.0, y=0.0),
            v3=Point(x=0.0, y=10.0),
        )
        assert t.contains(Point(x=2.0, y=2.0))

    def test_contains_outside(self) -> None:
        """不包含外部点。/ Not contains outside point."""
        t = Triangle(
            v1=Point(x=0.0, y=0.0),
            v2=Point(x=10.0, y=0.0),
            v3=Point(x=0.0, y=10.0),
        )
        assert not t.contains(Point(x=8.0, y=8.0))


# ── Cuboid3 ───────────────────────────────────────────────────


class TestCuboid3:
    """长方体测试。"""

    def test_volume(self) -> None:
        """体积。/ Volume."""
        c = Cuboid3(
            origin=Point3(x=0.0, y=0.0, z=0.0),
            width=2.0,
            height=3.0,
            depth=4.0,
        )
        assert c.volume() == 24.0

    def test_contains(self) -> None:
        """包含内部点。/ Contains inside point."""
        c = Cuboid3(
            origin=Point3(x=0.0, y=0.0, z=0.0),
            width=10.0,
            height=10.0,
            depth=10.0,
        )
        assert c.contains(Point3(x=5.0, y=5.0, z=5.0))
        assert not c.contains(
            Point3(x=15.0, y=5.0, z=5.0),
        )


# ── Cuboid3View ───────────────────────────────────────────────


class TestCuboid3View:
    """长方体视图测试。"""

    def test_origin_with_offset(self) -> None:
        """带偏移的原点。/ Origin with offset."""
        cuboid = Cuboid3(
            origin=Point3(x=0.0, y=0.0, z=0.0),
            width=10.0,
            height=10.0,
            depth=10.0,
        )
        view = Cuboid3View(
            cuboid=cuboid,
            offset=Point3(x=5.0, y=5.0, z=5.0),
        )
        o = view.origin
        assert o.x == 5.0
        assert o.y == 5.0
        assert o.z == 5.0


# ── Cylinder3 ─────────────────────────────────────────────────


class TestCylinder3:
    """圆柱体测试。"""

    def test_volume(self) -> None:
        """体积。/ Volume."""
        cyl = Cylinder3(
            center=Point3(x=0.0, y=0.0, z=0.0),
            radius=1.0,
            height=2.0,
        )
        expected = math.pi * 1.0 * 1.0 * 2.0
        assert abs(cyl.volume() - expected) < 1e-10


# ── Rectangle ─────────────────────────────────────────────────


class TestRectangle:
    """矩形测试。"""

    def test_area(self) -> None:
        """面积。/ Area."""
        r = Rectangle(
            origin=Point(x=0.0, y=0.0),
            width=3.0,
            height=4.0,
        )
        assert r.area() == 12.0

    def test_contains(self) -> None:
        """包含内部点。/ Contains inside point."""
        r = Rectangle(
            origin=Point(x=0.0, y=0.0),
            width=10.0,
            height=10.0,
        )
        assert r.contains(Point(x=5.0, y=5.0))
        assert not r.contains(Point(x=15.0, y=5.0))


# ── Dimension ─────────────────────────────────────────────────


class TestDimension:
    """尺寸测试。"""

    def test_creation(self) -> None:
        """创建尺寸。/ Create dimension."""
        d = Dimension(width=1.0, height=2.0, depth=3.0)
        assert d.width == 1.0

    def test_cube(self) -> None:
        """立方体尺寸。/ Cube dimension."""
        d = Dimension.cube(5.0)
        assert d.width == 5.0
        assert d.height == 5.0
        assert d.depth == 5.0

    def test_volume(self) -> None:
        """体积。/ Volume."""
        d = Dimension(width=2.0, height=3.0, depth=4.0)
        assert d.volume() == 24.0


# ── Edge ──────────────────────────────────────────────────────


class TestEdge:
    """线段测试。"""

    def test_length(self) -> None:
        """长度。/ Length."""
        e = Edge(
            start=Point(x=0.0, y=0.0),
            end=Point(x=3.0, y=4.0),
        )
        assert e.length() == 5.0


# ── Axis enums ────────────────────────────────────────────────


class TestAxisEnums:
    """坐标轴枚举测试。"""

    def test_axis2_index(self) -> None:
        """二维轴索引。/ 2D axis index."""
        assert Axis2.X.index == 0
        assert Axis2.Y.index == 1

    def test_axis2_other(self) -> None:
        """二维轴取反。/ 2D axis other."""
        assert Axis2.X.other() == Axis2.Y
        assert Axis2.Y.other() == Axis2.X

    def test_axis3_index(self) -> None:
        """三维轴索引。/ 3D axis index."""
        assert Axis3.X.index == 0
        assert Axis3.Y.index == 1
        assert Axis3.Z.index == 2

    def test_axis_plane3(self) -> None:
        """坐标平面。/ Coordinate planes."""
        assert AxisPlane3.XY.value == "xy"
        assert AxisPlane3.XZ.value == "xz"


# ── AxisPermutation ──────────────────────────────────────────


class TestAxisPermutation:
    """坐标轴排列测试。"""

    def test_permutation2_identity(self) -> None:
        """二维恒等排列。/ 2D identity permutation."""
        p = AxisPermutation2.identity()
        assert p.x == Axis2.X
        assert p.y == Axis2.Y

    def test_permutation2_apply(self) -> None:
        """二维排列应用。/ 2D permutation apply."""
        p = AxisPermutation2(x=Axis2.Y, y=Axis2.X)
        result = p.apply((1.0, 2.0))
        assert result == (2.0, 1.0)

    def test_permutation3_identity(self) -> None:
        """三维恒等排列。/ 3D identity permutation."""
        p = AxisPermutation3.identity()
        assert p.x == Axis3.X
        assert p.y == Axis3.Y
        assert p.z == Axis3.Z

    def test_permutation3_apply(self) -> None:
        """三维排列应用。/ 3D permutation apply."""
        p = AxisPermutation3(
            x=Axis3.Z,
            y=Axis3.X,
            z=Axis3.Y,
        )
        result = p.apply((1.0, 2.0, 3.0))
        assert result == (3.0, 1.0, 2.0)


# ── Placement ────────────────────────────────────────────────


class TestPlacement:
    """放置类型测试。"""

    def test_placement2_identity(self) -> None:
        """二维单位放置。/ 2D identity placement."""
        p = Placement2.identity()
        assert p.position.x == 0.0
        assert p.rotation == 0.0

    def test_placement3_identity(self) -> None:
        """三维单位放置。/ 3D identity placement."""
        p = Placement3.identity()
        assert p.position.x == 0.0
        assert p.rotation_x == 0.0


# ── Projection2 ───────────────────────────────────────────────


class TestProjection2:
    """投影测试。"""

    def test_onto_line_midpoint(self) -> None:
        """投影到线段中点。/ Project to line midpoint."""
        result = Projection2.onto_line(
            point=Point(x=5.0, y=5.0),
            line_start=Point(x=0.0, y=0.0),
            line_end=Point(x=10.0, y=0.0),
        )
        assert abs(result.point.x - 5.0) < 1e-10
        assert abs(result.point.y - 0.0) < 1e-10

    def test_onto_line_clamp_start(self) -> None:
        """投影截断到起点。/ Project clamped to start."""
        result = Projection2.onto_line(
            point=Point(x=-5.0, y=0.0),
            line_start=Point(x=0.0, y=0.0),
            line_end=Point(x=10.0, y=0.0),
        )
        assert result.parameter == 0.0

    def test_onto_line_clamp_end(self) -> None:
        """投影截断到终点。/ Project clamped to end."""
        result = Projection2.onto_line(
            point=Point(x=20.0, y=0.0),
            line_start=Point(x=0.0, y=0.0),
            line_end=Point(x=10.0, y=0.0),
        )
        assert result.parameter == 1.0


# ── Quadrilateral ────────────────────────────────────────────


class TestQuadrilateral:
    """四边形测试。"""

    def test_area_square(self) -> None:
        """正方形面积。/ Square area."""
        q = Quadrilateral(
            v1=Point(x=0.0, y=0.0),
            v2=Point(x=4.0, y=0.0),
            v3=Point(x=4.0, y=4.0),
            v4=Point(x=0.0, y=4.0),
        )
        assert q.area() == 16.0


# ── QuantityOps ───────────────────────────────────────────────


class TestQuantityOps:
    """物理量操作测试。"""

    def test_length(self) -> None:
        """长度量。/ Length quantity."""
        q = QuantityOps.length(5.0)
        assert q.value == 5.0
        assert q.unit == "m"

    def test_area(self) -> None:
        """面积量。/ Area quantity."""
        q = QuantityOps.area(12.0)
        assert q.unit == "m^2"

    def test_volume(self) -> None:
        """体积量。/ Volume quantity."""
        q = QuantityOps.volume(24.0)
        assert q.unit == "m^3"

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        q = QuantityOps.length(3.0)
        assert "3.0 m" in repr(q)


# ── Triangulation ─────────────────────────────────────────────


class TestTriangulation:
    """三角剖分测试。"""

    def test_fan_triangulation(self) -> None:
        """扇形三角剖分。/ Fan triangulation."""
        points = [
            Point(x=0.0, y=0.0),
            Point(x=4.0, y=0.0),
            Point(x=4.0, y=3.0),
            Point(x=0.0, y=3.0),
        ]
        tris = triangulate(points)
        assert len(tris) == 2

    def test_too_few_points(self) -> None:
        """点不足。/ Too few points."""
        points = [Point(x=0.0, y=0.0), Point(x=1.0, y=0.0)]
        tris = triangulate(points)
        assert len(tris) == 0


# ── Shape3 ABC ───────────────────────────────────────────────


class TestShape3:
    """三维形状基类测试。"""

    def test_cuboid_as_shape3(self) -> None:
        """长方体作为 Shape3。/ Cuboid as Shape3."""

        class CuboidShape(Shape3):
            def __init__(self, c: Cuboid3) -> None:
                self._c = c

            def volume(self) -> float:
                return self._c.volume()

            def bounding_box(self) -> Box3:
                o = self._c.origin
                return Box3(
                    min_point=o,
                    max_point=Point3(
                        x=o.x + self._c.width,
                        y=o.y + self._c.height,
                        z=o.z + self._c.depth,
                    ),
                )

        cuboid = Cuboid3(
            origin=Point3(x=0.0, y=0.0, z=0.0),
            width=2.0,
            height=3.0,
            depth=4.0,
        )
        shape = CuboidShape(cuboid)
        assert shape.volume() == 24.0
        bb = shape.bounding_box()
        assert bb.volume() == 24.0


# ── PlaneFrame3 ───────────────────────────────────────────────


class TestPlaneFrame3:
    """平面框架测试。"""

    def test_creation(self) -> None:
        """创建平面框架。/ Create plane frame."""
        frame = PlaneFrame3(
            origin=Point3(x=0.0, y=0.0, z=0.0),
            normal=Point3(x=0.0, y=0.0, z=1.0),
        )
        assert frame.normal.z == 1.0
