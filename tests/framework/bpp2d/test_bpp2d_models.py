"""BPP2D 领域模型测试 / BPP2D domain model tests.

测试矩形、圆形物品和装箱结果的创建与属性。
Test creation and properties of Rectangle, Circle,
and PackingResult in BPP2D.
"""

from __future__ import annotations

import math

from ospf_python.framework.bpp2d.domain.item.model.circle import Circle
from ospf_python.framework.bpp2d.domain.item.model.packing_result import (
    PackingResult,
)
from ospf_python.framework.bpp2d.domain.item.model.rectangle import Rectangle


class TestRectangle:
    """矩形物品测试 / Rectangle item tests."""

    def test_create_rectangle(self) -> None:
        """创建矩形物品 / Create rectangle."""
        r = Rectangle.create(
            item_key="r1",
            width=10.0,
            height=5.0,
            weight=2.0,
            can_rotate=True,
        )
        assert r.item_key == "r1"
        assert r.width == 10.0
        assert r.height == 5.0
        assert r.weight == 2.0
        assert r.can_rotate is True

    def test_rectangle_defaults(self) -> None:
        """矩形默认值 / Rectangle defaults."""
        r = Rectangle(item_key="r1", width=3.0, height=4.0)
        assert r.weight == 0.0
        assert r.can_rotate is False

    def test_rectangle_area(self) -> None:
        """矩形面积 / Rectangle area."""
        r = Rectangle.create(item_key="r1", width=6.0, height=4.0)
        assert r.area == 24.0

    def test_rectangle_perimeter(self) -> None:
        """矩形周长 / Rectangle perimeter."""
        r = Rectangle.create(item_key="r1", width=6.0, height=4.0)
        assert r.perimeter == 20.0

    def test_rectangle_aspect_ratio(self) -> None:
        """矩形宽高比 / Rectangle aspect ratio."""
        r = Rectangle.create(item_key="r1", width=8.0, height=4.0)
        assert r.aspect_ratio == 2.0

    def test_rectangle_aspect_ratio_zero_height(self) -> None:
        """高度为零的宽高比 / Aspect ratio with zero height."""
        r = Rectangle.create(item_key="r1", width=8.0, height=0.0)
        assert r.aspect_ratio == float("inf")

    def test_rectangle_rotated(self) -> None:
        """旋转矩形 / Rotated rectangle."""
        r = Rectangle.create(
            item_key="r1",
            width=8.0,
            height=4.0,
            can_rotate=True,
        )
        rot = r.rotated()
        assert rot.width == 4.0
        assert rot.height == 8.0
        assert rot.item_key == "r1"

    def test_fits_in_container(self) -> None:
        """放入容器检查 / Fits in container."""
        r = Rectangle.create(item_key="r1", width=5.0, height=3.0)
        assert r.fits_in(10.0, 10.0) is True
        assert r.fits_in(2.0, 10.0) is False

    def test_fits_in_with_rotation(self) -> None:
        """旋转后放入容器 / Fits in with rotation."""
        r = Rectangle.create(
            item_key="r1",
            width=8.0,
            height=3.0,
            can_rotate=True,
        )
        # 8x3 does not fit in 5x10, but 3x8 does
        assert r.fits_in(5.0, 10.0) is True
        # Without rotation it would not fit
        r_no_rot = Rectangle.create(
            item_key="r2",
            width=8.0,
            height=3.0,
            can_rotate=False,
        )
        assert r_no_rot.fits_in(5.0, 10.0) is False


class TestCircle:
    """圆形物品测试 / Circle item tests."""

    def test_create_circle(self) -> None:
        """创建圆形物品 / Create circle."""
        c = Circle.create(item_key="c1", radius=5.0, weight=1.0)
        assert c.item_key == "c1"
        assert c.radius == 5.0
        assert c.weight == 1.0

    def test_circle_diameter(self) -> None:
        """圆形直径 / Circle diameter."""
        c = Circle.create(item_key="c1", radius=5.0)
        assert c.diameter == 10.0

    def test_circle_area(self) -> None:
        """圆形面积 / Circle area."""
        c = Circle.create(item_key="c1", radius=5.0)
        assert c.area == math.pi * 25.0

    def test_circle_circumference(self) -> None:
        """圆形周长 / Circle circumference."""
        c = Circle.create(item_key="c1", radius=5.0)
        assert c.circumference == 2.0 * math.pi * 5.0

    def test_circle_bounding_box(self) -> None:
        """圆形包围盒 / Circle bounding box."""
        c = Circle.create(item_key="c1", radius=5.0)
        assert c.bounding_box_width == 10.0
        assert c.bounding_box_height == 10.0

    def test_circle_fits_in(self) -> None:
        """圆形放入容器 / Circle fits in container."""
        c = Circle.create(item_key="c1", radius=3.0)
        assert c.fits_in(10.0, 10.0) is True
        # 半径 3 → 直径 6，需要 ≥6 的容器
        # radius 3 → diameter 6, needs ≥6 container
        assert c.fits_in(6.0, 10.0) is True
        assert c.fits_in(5.0, 10.0) is False
        assert c.fits_in(5.0, 5.0) is False

    def test_circle_overlaps_with(self) -> None:
        """圆形重叠检查 / Circle overlap check."""
        c1 = Circle.create(item_key="c1", radius=3.0)
        c2 = Circle.create(item_key="c2", radius=3.0)
        # Conservative: always returns True
        assert c1.overlaps_with(c2) is True

    def test_circle_distance_to(self) -> None:
        """圆形距离 / Circle distance."""
        c1 = Circle.create(item_key="c1", radius=3.0)
        c2 = Circle.create(item_key="c2", radius=5.0)
        # Conservative: returns -(r1 + r2)
        assert c1.distance_to(c2) == -8.0


class TestPackingResult:
    """装箱结果测试 / Packing result tests."""

    def test_create_packing_result(self) -> None:
        """创建装箱结果 / Create packing result."""
        p = PackingResult.create(
            item_key="r1",
            x=10.0,
            y=20.0,
            placed_width=5.0,
            placed_height=3.0,
            rotated=False,
        )
        assert p.item_key == "r1"
        assert p.x == 10.0
        assert p.y == 20.0
        assert p.placed_width == 5.0
        assert p.placed_height == 3.0
        assert p.rotated is False

    def test_packing_result_boundaries(self) -> None:
        """装箱结果边界 / Packing result boundaries."""
        p = PackingResult.create(
            item_key="r1",
            x=10.0,
            y=20.0,
            placed_width=5.0,
            placed_height=3.0,
        )
        assert p.right == 15.0
        assert p.top == 23.0

    def test_packing_result_area(self) -> None:
        """装箱结果面积 / Packing result area."""
        p = PackingResult.create(
            item_key="r1",
            x=0.0,
            y=0.0,
            placed_width=5.0,
            placed_height=3.0,
        )
        assert p.area == 15.0

    def test_packing_result_center(self) -> None:
        """装箱结果中心 / Packing result center."""
        p = PackingResult.create(
            item_key="r1",
            x=10.0,
            y=20.0,
            placed_width=6.0,
            placed_height=4.0,
        )
        assert p.center_x == 13.0
        assert p.center_y == 22.0

    def test_overlaps_with(self) -> None:
        """重叠检测 / Overlap detection."""
        p1 = PackingResult.create(
            item_key="a",
            x=0.0,
            y=0.0,
            placed_width=5.0,
            placed_height=5.0,
        )
        p2 = PackingResult.create(
            item_key="b",
            x=3.0,
            y=3.0,
            placed_width=5.0,
            placed_height=5.0,
        )
        p3 = PackingResult.create(
            item_key="c",
            x=10.0,
            y=10.0,
            placed_width=5.0,
            placed_height=5.0,
        )
        assert p1.overlaps_with(p2) is True
        assert p1.overlaps_with(p3) is False

    def test_contains_point(self) -> None:
        """包含点检测 / Contains point."""
        p = PackingResult.create(
            item_key="r1",
            x=10.0,
            y=20.0,
            placed_width=5.0,
            placed_height=3.0,
        )
        assert p.contains_point(12.0, 21.0) is True
        assert p.contains_point(0.0, 0.0) is False
        # Boundary: x inclusive, right exclusive
        assert p.contains_point(10.0, 20.0) is True
        assert p.contains_point(15.0, 20.0) is False
