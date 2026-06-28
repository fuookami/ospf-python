"""BPP2D 求解器集成测试 / BPP2D solver integration tests.

测试 GeometricPacker 的放置逻辑和边界检测。
Test GeometricPacker placement logic and boundary checks.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.bpp2d.domain.item.model.circle import Circle
from ospf_python.framework.bpp2d.domain.item.model.rectangle import Rectangle
from ospf_python.framework.bpp2d.domain.service.geometric_packer import (
    GeometricPacker,
)


class TestGeometricPacker:
    """几何装箱器测试 / Geometric packer tests."""

    def test_create_packer(self) -> None:
        """创建几何装箱器 / Create geometric packer."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=80.0,
        )
        assert packer.container_width == 100.0
        assert packer.container_height == 80.0
        assert packer.container_area == 8000.0

    def test_place_rectangle_valid(self) -> None:
        """有效放置矩形 / Valid rectangle placement."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        rect = Rectangle.create(
            item_key="r1",
            width=20.0,
            height=10.0,
        )
        result = packer.place_rectangle(rect, 10.0, 20.0)
        assert result.is_ok()
        placed = result.unwrap()
        assert placed.item_key == "r1"
        assert placed.x == 10.0
        assert placed.y == 20.0
        assert placed.placed_width == 20.0
        assert placed.placed_height == 10.0
        assert placed.rotated is False

    def test_place_rectangle_rotated(self) -> None:
        """旋转放置矩形 / Rotated rectangle placement."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        rect = Rectangle.create(
            item_key="r1",
            width=20.0,
            height=10.0,
        )
        result = packer.place_rectangle(rect, 0.0, 0.0, rotate=True)
        assert result.is_ok()
        placed = result.unwrap()
        assert placed.placed_width == 10.0
        assert placed.placed_height == 20.0
        assert placed.rotated is True

    def test_place_rectangle_negative_position(self) -> None:
        """负坐标放置 / Negative position placement."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        rect = Rectangle.create(item_key="r1", width=10.0, height=10.0)
        result = packer.place_rectangle(rect, -1.0, 0.0)
        assert result.is_failed()

    def test_place_rectangle_exceeds_right(self) -> None:
        """超出右边界 / Exceeds right boundary."""
        packer = GeometricPacker.create(
            container_width=50.0,
            container_height=100.0,
        )
        rect = Rectangle.create(item_key="r1", width=20.0, height=10.0)
        result = packer.place_rectangle(rect, 40.0, 0.0)
        assert result.is_failed()

    def test_place_rectangle_exceeds_top(self) -> None:
        """超出上边界 / Exceeds top boundary."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=50.0,
        )
        rect = Rectangle.create(item_key="r1", width=10.0, height=20.0)
        result = packer.place_rectangle(rect, 0.0, 40.0)
        assert result.is_failed()

    def test_place_circle_valid(self) -> None:
        """有效放置圆形 / Valid circle placement."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        circle = Circle.create(item_key="c1", radius=10.0)
        # Place at center (20, 20)
        result = packer.place_circle(circle, 20.0, 20.0)
        assert result.is_ok()
        placed = result.unwrap()
        assert placed.item_key == "c1"
        assert placed.x == 10.0  # center - radius
        assert placed.y == 10.0
        assert placed.placed_width == 20.0  # diameter
        assert placed.placed_height == 20.0

    def test_place_circle_exceeds_left(self) -> None:
        """圆形超出左边界 / Circle exceeds left boundary."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        circle = Circle.create(item_key="c1", radius=10.0)
        result = packer.place_circle(circle, 5.0, 50.0)
        assert result.is_failed()

    def test_place_circle_exceeds_right(self) -> None:
        """圆形超出右边界 / Circle exceeds right boundary."""
        packer = GeometricPacker.create(
            container_width=50.0,
            container_height=100.0,
        )
        circle = Circle.create(item_key="c1", radius=10.0)
        result = packer.place_circle(circle, 45.0, 50.0)
        assert result.is_failed()

    def test_place_circle_exceeds_top(self) -> None:
        """圆形超出上边界 / Circle exceeds top boundary."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=50.0,
        )
        circle = Circle.create(item_key="c1", radius=10.0)
        result = packer.place_circle(circle, 50.0, 45.0)
        assert result.is_failed()

    def test_check_no_overlap(self) -> None:
        """无重叠检查 / No overlap check."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        r1 = Rectangle.create(item_key="r1", width=20.0, height=20.0)
        r2 = Rectangle.create(item_key="r2", width=20.0, height=20.0)
        p1 = packer.place_rectangle(r1, 0.0, 0.0).unwrap()
        p2 = packer.place_rectangle(r2, 30.0, 30.0).unwrap()
        result = packer.check_no_overlap((p1, p2))
        assert result.is_ok()

    def test_check_overlap_detected(self) -> None:
        """检测到重叠 / Overlap detected."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        r1 = Rectangle.create(item_key="r1", width=20.0, height=20.0)
        r2 = Rectangle.create(item_key="r2", width=20.0, height=20.0)
        p1 = packer.place_rectangle(r1, 0.0, 0.0).unwrap()
        p2 = packer.place_rectangle(r2, 10.0, 10.0).unwrap()
        result = packer.check_no_overlap((p1, p2))
        assert result.is_failed()


# ============================================================
# Deep behavioral: boundary contact, rotation, overlap detection
# ============================================================


class TestGeometricPackerDeep:
    """几何装箱器深度测试。/ Geometric packer deep tests."""

    def test_items_touching_edges(self) -> None:
        """物品接触容器边缘。/ Items touching container edges."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        r = Rectangle.create(item_key="r1", width=10.0, height=10.0)
        # Place at top-right corner
        result = packer.place_rectangle(r, 90.0, 90.0)
        assert result.is_ok()
        p = result.unwrap()
        assert p.right == pytest.approx(100.0)
        assert p.top == pytest.approx(100.0)

    def test_item_at_origin(self) -> None:
        """物品放在原点。/ Item at origin."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        r = Rectangle.create(item_key="r1", width=50.0, height=50.0)
        result = packer.place_rectangle(r, 0.0, 0.0)
        assert result.is_ok()
        p = result.unwrap()
        assert p.x == 0.0
        assert p.y == 0.0

    def test_rotation_preserves_area(self) -> None:
        """旋转后面积不变。/ Rotation preserves area."""
        r = Rectangle.create(item_key="r1", width=8.0, height=4.0, can_rotate=True)
        rot = r.rotated()
        assert r.area == rot.area

    def test_no_overlap_diagonal_placement(self) -> None:
        """对角线放置无重叠。/ Diagonal placement no overlap."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        r1 = Rectangle.create(item_key="r1", width=30.0, height=30.0)
        r2 = Rectangle.create(item_key="r2", width=30.0, height=30.0)
        p1 = packer.place_rectangle(r1, 0.0, 0.0).unwrap()
        p2 = packer.place_rectangle(r2, 50.0, 50.0).unwrap()
        assert packer.check_no_overlap((p1, p2)).is_ok()

    def test_no_overlap_adjacent_no_gap(self) -> None:
        """相邻放置无间隙无重叠。/ Adjacent no gap, no overlap."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        r1 = Rectangle.create(item_key="r1", width=50.0, height=50.0)
        r2 = Rectangle.create(item_key="r2", width=50.0, height=50.0)
        p1 = packer.place_rectangle(r1, 0.0, 0.0).unwrap()
        p2 = packer.place_rectangle(r2, 50.0, 0.0).unwrap()
        assert packer.check_no_overlap((p1, p2)).is_ok()

    def test_circle_place_at_center(self) -> None:
        """圆形放在容器中心。/ Circle at container center."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        circle = Circle.create(item_key="c1", radius=10.0)
        result = packer.place_circle(circle, 50.0, 50.0)
        assert result.is_ok()

    def test_multiple_rects_no_overlap(self) -> None:
        """多个矩形无重叠放置。/ Multiple rects no overlap."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        rects = [
            Rectangle.create(item_key=f"r{i}", width=20.0, height=20.0)
            for i in range(4)
        ]
        positions = [(0.0, 0.0), (25.0, 0.0), (0.0, 25.0), (25.0, 25.0)]
        placed = [
            packer.place_rectangle(r, x, y).unwrap()
            for r, (x, y) in zip(rects, positions, strict=False)
        ]
        assert packer.check_no_overlap(tuple(placed)).is_ok()
