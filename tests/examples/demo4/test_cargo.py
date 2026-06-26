"""Cargo 测试 / Cargo tests.

覆盖 Cargo 创建和 CargoAllocator。
Covers Cargo creation and CargoAllocator.
"""

from __future__ import annotations

import pytest

from examples.framework_demo.demo4.domain.cargo.model.cargo import (
    Cargo,
)
from examples.framework_demo.demo4.domain.cargo.service.cargo_allocator import (
    BunchSlot,
    CargoAllocator,
)


class TestCargo:
    """Cargo 测试 / Cargo tests."""

    def test_is_heavy(self) -> None:
        """是否重货 / Is heavy."""
        heavy = Cargo(
            cargo_id="C1",
            weight=1_500.0,
            volume=2.0,
            priority=5,
            destination="PVG",
        )
        light = Cargo(
            cargo_id="C2",
            weight=500.0,
            volume=1.0,
            priority=5,
            destination="PVG",
        )
        assert heavy.is_heavy is True
        assert light.is_heavy is False

    def test_density(self) -> None:
        """密度 / Density."""
        c = Cargo(
            cargo_id="C1",
            weight=1_000.0,
            volume=2.0,
            priority=5,
            destination="PEK",
        )
        assert c.density == pytest.approx(500.0)

    def test_is_high_priority(self) -> None:
        """高优先级 / High priority."""
        high = Cargo(
            cargo_id="C1",
            weight=100.0,
            volume=1.0,
            priority=9,
            destination="PEK",
        )
        low = Cargo(
            cargo_id="C2",
            weight=100.0,
            volume=1.0,
            priority=3,
            destination="PEK",
        )
        assert high.is_high_priority is True
        assert low.is_high_priority is False

    def test_size_category(self) -> None:
        """尺寸类别 / Size category."""
        c = Cargo(
            cargo_id="C1",
            weight=500.0,
            volume=1.0,
            priority=5,
            destination="PEK",
        )
        assert c.size_category in ("small", "medium", "large", "extra_large")

    def test_same_destination(self) -> None:
        """同目的地 / Same destination."""
        c1 = Cargo(
            cargo_id="C1",
            weight=100.0,
            volume=1.0,
            priority=5,
            destination="PVG",
        )
        c2 = Cargo(
            cargo_id="C2",
            weight=200.0,
            volume=2.0,
            priority=5,
            destination="PVG",
        )
        c3 = Cargo(
            cargo_id="C3",
            weight=300.0,
            volume=3.0,
            priority=5,
            destination="PEK",
        )
        assert c1.same_destination(c2) is True
        assert c1.same_destination(c3) is False

    def test_combined_weight(self) -> None:
        """合并重量 / Combined weight."""
        c1 = Cargo(
            cargo_id="C1",
            weight=100.0,
            volume=1.0,
            priority=5,
            destination="PVG",
        )
        c2 = Cargo(
            cargo_id="C2",
            weight=200.0,
            volume=2.0,
            priority=5,
            destination="PVG",
        )
        assert c1.combined_weight(c2) == pytest.approx(300.0)

    def test_frozen(self) -> None:
        """不可变 / Frozen."""
        c = Cargo(
            cargo_id="C1",
            weight=100.0,
            volume=1.0,
            priority=5,
            destination="PEK",
        )
        with pytest.raises(AttributeError):
            c.weight = 999.0  # type: ignore[misc]


class TestCargoAllocator:
    """CargoAllocator 测试 / Allocator tests."""

    def test_allocate_basic(self) -> None:
        """基本分配 / Basic allocation."""
        allocator = CargoAllocator()
        cargos = (
            Cargo("C1", 500.0, 1.0, 5, "PVG"),
            Cargo("C2", 300.0, 0.5, 5, "PVG"),
        )
        slots = (BunchSlot("B1", capacity=1_000.0, destination="PVG"),)
        allocations = allocator.allocate(cargos, slots)
        assert len(allocations) == 2

    def test_unallocated(self) -> None:
        """未分配 / Unallocated."""
        allocator = CargoAllocator()
        cargos = (
            Cargo("C1", 500.0, 1.0, 5, "PVG"),
            Cargo("C2", 2_000.0, 5.0, 5, "PEK"),
        )
        slots = (BunchSlot("B1", capacity=1_000.0, destination="PVG"),)
        allocations = allocator.allocate(cargos, slots)
        unalloc = allocator.unallocated(cargos, allocations)
        assert len(unalloc) >= 1

    def test_allocation_summary(self) -> None:
        """分配摘要 / Allocation summary."""
        allocator = CargoAllocator()
        (
            type(
                "A",
                (),
                {"cargo_id": "C1", "bunch_id": "B1"},
            )(),
            type(
                "A",
                (),
                {"cargo_id": "C2", "bunch_id": "B1"},
            )(),
        )
        # Use actual Allocation type
        from examples.framework_demo.demo4.domain.cargo.service.cargo_allocator import (
            Allocation as CargoAllocation,
        )

        allocs = (
            CargoAllocation(cargo_id="C1", bunch_id="B1"),
            CargoAllocation(cargo_id="C2", bunch_id="B1"),
        )
        summary = allocator.allocation_summary(allocs)
        assert "B1" in summary
