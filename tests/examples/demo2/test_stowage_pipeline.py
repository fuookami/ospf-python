"""Stowage pipeline 测试 / Stowage pipeline tests.

覆盖 StowagePlan 创建、重量/体积/平衡约束和
管线组合。
Covers StowagePlan creation, weight/volume/balance
constraints, and pipeline composition.
"""

from __future__ import annotations

import pytest

from examples.framework_demo.demo2.domain.stowage.model.stowage_compartment import (
    StowageCompartment,
)
from examples.framework_demo.demo2.domain.stowage.model.stowage_context import (
    StowageContext,
)
from examples.framework_demo.demo2.domain.stowage.model.stowage_item import (
    Dimensions,
    StowageItem,
)
from examples.framework_demo.demo2.domain.stowage.model.stowage_plan import (
    ItemPlacement,
    StowagePlan,
)


def _make_compartment(
    comp_id: str = "C1",
    max_weight: float = 50_000.0,
    max_volume: float = 80.0,
) -> StowageCompartment:
    """创建测试货舱 / Create test compartment."""
    return StowageCompartment.create(
        comp_id=comp_id,
        deck="LOWER",
        max_weight=max_weight,
        max_volume=max_volume,
    )


def _make_item(
    item_id: str = "PKG001",
    weight: float = 500.0,
) -> StowageItem:
    """创建测试货物 / Create test item."""
    return StowageItem.create(
        item_id=item_id,
        weight=weight,
        dimensions=Dimensions(length=1.2, width=1.0, height=0.8),
    )


class TestStowagePlanCreation:
    """StowagePlan 创建测试 / Plan creation tests."""

    def test_create_empty_plan(self) -> None:
        """创建空方案 / Create empty plan."""
        plan = StowagePlan.create(
            plan_id="P1",
            aircraft_id="B-2447",
        )
        assert plan.plan_id == "P1"
        assert plan.aircraft_id == "B-2447"
        assert plan.leg_count == 0
        assert plan.item_count == 0

    def test_with_placement(self) -> None:
        """添加放置记录 / Add placement record."""
        plan = StowagePlan.create(plan_id="P1", aircraft_id="AC1")
        placement = ItemPlacement(
            item_id="PKG001",
            position=None,  # type: ignore[arg-type]
            leg_id="L1",
        )
        new_plan = plan.with_placement(placement)
        assert new_plan.placement_count == 1
        assert plan.placement_count == 0

    def test_placements_for_leg(self) -> None:
        """按航段筛选放置 / Filter placements by leg."""
        p1 = ItemPlacement(item_id="A", position=None, leg_id="L1")  # type: ignore[arg-type]
        p2 = ItemPlacement(item_id="B", position=None, leg_id="L2")  # type: ignore[arg-type]
        p3 = ItemPlacement(item_id="C", position=None, leg_id="L1")  # type: ignore[arg-type]
        plan = StowagePlan.create(
            plan_id="P1",
            aircraft_id="AC1",
            placements=(p1, p2, p3),
        )
        l1 = plan.placements_for_leg("L1")
        assert len(l1) == 2


class TestStowageItem:
    """StowageItem 测试 / Stowage item tests."""

    def test_item_volume(self) -> None:
        """货物体积计算 / Item volume calculation."""
        item = _make_item()
        assert item.volume == pytest.approx(1.2 * 1.0 * 0.8)

    def test_fragile_detection(self) -> None:
        """易碎品检测 / Fragile detection."""
        fragile = StowageItem.create(
            item_id="F1",
            weight=100.0,
            dimensions=Dimensions(1.0, 1.0, 1.0),
            fragility=0.8,
        )
        sturdy = StowageItem.create(
            item_id="S1",
            weight=100.0,
            dimensions=Dimensions(1.0, 1.0, 1.0),
            fragility=0.1,
        )
        assert fragile.is_fragile is True
        assert sturdy.is_fragile is False

    def test_density(self) -> None:
        """货物密度 / Item density."""
        item = StowageItem.create(
            item_id="D1",
            weight=1000.0,
            dimensions=Dimensions(2.0, 1.0, 1.0),
        )
        assert item.density == pytest.approx(500.0)

    def test_stacking_resistance(self) -> None:
        """堆叠抗压能力 / Stacking resistance."""
        item = StowageItem.create(
            item_id="SR1",
            weight=100.0,
            dimensions=Dimensions(1.0, 1.0, 1.0),
            fragility=0.3,
        )
        assert item.stacking_resistance() == pytest.approx(0.7)


class TestStowageCompartment:
    """StowageCompartment 测试 / Compartment tests."""

    def test_deck_detection(self) -> None:
        """甲板检测 / Deck detection."""
        lower = _make_compartment()
        assert lower.is_lower_deck is True
        assert lower.is_upper_deck is False

    def test_weight_utilization(self) -> None:
        """重量利用率 / Weight utilization."""
        comp = _make_compartment(max_weight=10_000.0)
        assert comp.weight_utilization(5_000.0) == pytest.approx(0.5)
        assert comp.weight_utilization(15_000.0) == pytest.approx(1.0)

    def test_remaining_capacity(self) -> None:
        """剩余容量 / Remaining capacity."""
        comp = _make_compartment(
            max_weight=10_000.0,
            max_volume=50.0,
        )
        assert comp.remaining_weight(3_000.0) == pytest.approx(7_000.0)
        assert comp.remaining_volume(60.0) == pytest.approx(0.0)


class TestStowageContext:
    """StowageContext 测试 / Context tests."""

    def test_register_compartment(self) -> None:
        """注册货舱 / Register compartment."""
        ctx = StowageContext()
        comp = _make_compartment()
        ctx2 = ctx.register_compartment(comp)
        assert len(ctx2.compartments) == 1
        assert len(ctx.compartments) == 0

    def test_register_item(self) -> None:
        """注册货物 / Register item."""
        ctx = StowageContext()
        item = _make_item()
        ctx2 = ctx.register_item(item)
        assert len(ctx2.items) == 1

    def test_compartment_by_id(self) -> None:
        """按 ID 查找货舱 / Lookup compartment by ID."""
        ctx = StowageContext().register_compartment(_make_compartment("C99"))
        assert ctx.compartment_by_id("C99") is not None
        assert ctx.compartment_by_id("MISSING") is None

    def test_total_registered_weight(self) -> None:
        """已注册货物总重 / Total registered weight."""
        ctx = StowageContext()
        ctx = ctx.register_item(_make_item("A", 1_000.0))
        ctx = ctx.register_item(_make_item("B", 2_000.0))
        assert ctx.total_registered_weight == pytest.approx(3_000.0)

    def test_total_compartment_capacity(self) -> None:
        """货舱总容量 / Total compartment capacity."""
        ctx = StowageContext()
        ctx = ctx.register_compartment(_make_compartment("C1", max_weight=10_000.0))
        ctx = ctx.register_compartment(_make_compartment("C2", max_weight=20_000.0))
        assert ctx.total_compartment_capacity == pytest.approx(30_000.0)

    def test_remaining_capacity_missing(self) -> None:
        """不存在货舱剩余容量为零 / Zero for missing compartment."""
        ctx = StowageContext()
        assert ctx.remaining_capacity("NOPE") == pytest.approx(0.0)
