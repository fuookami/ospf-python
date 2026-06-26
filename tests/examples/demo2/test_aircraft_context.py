"""Aircraft context 测试 / Aircraft context tests.

覆盖 Aircraft 创建、AircraftContext 注册、重量校验、
重心计算和容量检查。
Covers Aircraft creation, AircraftContext registration,
weight validation, CG calculation, and capacity checking.
"""

from __future__ import annotations

import pytest

from examples.framework_demo.demo2.domain.aircraft.model.aircraft import (
    Aircraft,
)
from examples.framework_demo.demo2.domain.aircraft.model.aircraft_aggregation import (
    AircraftAggregation,
)
from examples.framework_demo.demo2.domain.aircraft.model.deck import (
    Deck,
)
from examples.framework_demo.demo2.domain.aircraft.model.flight_phase import (
    FlightPhase,
)
from examples.framework_demo.demo2.domain.aircraft.model.position import (
    Position,
)
from examples.framework_demo.demo2.domain.aircraft.service.aircraft_balance_calculator import (
    AircraftBalanceCalculator,
    LoadItem,
)
from examples.framework_demo.demo2.domain.aircraft.service.aircraft_capacity_checker import (
    AircraftCapacityChecker,
)
from examples.framework_demo.demo2.domain.aircraft.service.aircraft_context import (
    AircraftContext,
)
from examples.framework_demo.demo2.domain.aircraft.service.aircraft_weight_validator import (
    AircraftWeightValidator,
)


def _make_b747() -> Aircraft:
    """创建 B747 测试航空器 / Create B747 test aircraft."""
    return Aircraft.create(
        aircraft_type="B747",
        registration="B-2447",
        max_takeoff_weight=396_900.0,
        max_landing_weight=260_800.0,
        max_zero_fuel_weight=238_800.0,
        fuel_capacity=193_280.0,
        cargo_hold_volume=158.0,
        deck_count=2,
    )


class TestAircraftCreation:
    """Aircraft 创建测试 / Aircraft creation tests."""

    def test_create_basic(self) -> None:
        """基本创建字段正确 / Basic creation fields correct."""
        ac = _make_b747()
        assert ac.aircraft_type == "B747"
        assert ac.registration == "B-2447"
        assert ac.max_takeoff_weight == 396_900.0

    def test_weight_margin(self) -> None:
        """起飞与着陆重量差 / Takeoff-landing weight margin."""
        ac = _make_b747()
        expected = 396_900.0 - 260_800.0
        assert ac.weight_margin == pytest.approx(expected)

    def test_with_registration_immutability(self) -> None:
        """with_registration 返回新实例 / Returns new instance."""
        ac = _make_b747()
        new_ac = ac.with_registration("B-1234")
        assert new_ac.registration == "B-1234"
        assert ac.registration == "B-2447"

    def test_frozen(self) -> None:
        """不可变性 / Frozen dataclass."""
        ac = _make_b747()
        with pytest.raises(AttributeError):
            ac.registration = "X"  # type: ignore[misc]


class TestAircraftAggregation:
    """AircraftAggregation 测试 / Aggregation tests."""

    def test_empty_aggregation(self) -> None:
        """空聚合 / Empty aggregation."""
        agg = AircraftAggregation.empty()
        assert agg.count == 0
        assert agg.is_empty is True

    def test_add_and_lookup(self) -> None:
        """添加和查找 / Add and lookup."""
        ac = _make_b747()
        agg = AircraftAggregation.create(aircraft=(ac,))
        assert agg.count == 1
        found = agg.by_registration("B-2447")
        assert found is ac

    def test_by_type_filter(self) -> None:
        """按机型筛选 / Filter by type."""
        ac1 = _make_b747()
        ac2 = ac1.with_registration("B-9999")
        agg = AircraftAggregation.create(aircraft=(ac1, ac2))
        result = agg.by_type("B747")
        assert len(result) == 2

    def test_heaviest_capacity(self) -> None:
        """最大起飞重量 / Heaviest capacity."""
        small = Aircraft.create(
            aircraft_type="A320",
            registration="D-AIMA",
            max_takeoff_weight=78_000.0,
            max_landing_weight=66_000.0,
            max_zero_fuel_weight=62_500.0,
            fuel_capacity=24_210.0,
            cargo_hold_volume=37.0,
        )
        big = _make_b747()
        agg = AircraftAggregation.create(aircraft=(small, big))
        assert agg.heaviest_capacity() is big


class TestAircraftContext:
    """AircraftContext 测试 / Context tests."""

    def test_create_and_current_aircraft(self) -> None:
        """创建上下文并查找当前航空器 / Create context and lookup."""
        ac = _make_b747()
        agg = AircraftAggregation.create(aircraft=(ac,))
        ctx = AircraftContext.create(
            aircraft_aggregation=agg,
            current_registration="B-2447",
        )
        assert ctx.current_aircraft is ac

    def test_with_phase_returns_new(self) -> None:
        """with_phase 返回新上下文 / Returns new context."""
        agg = AircraftAggregation.create(aircraft=(_make_b747(),))
        ctx = AircraftContext.create(
            aircraft_aggregation=agg,
            current_registration="B-2447",
        )
        new_ctx = ctx.with_phase(FlightPhase.LANDING)
        assert new_ctx.current_phase == FlightPhase.LANDING
        assert ctx.current_phase == FlightPhase.CRUISE

    def test_available_payload_capacity(self) -> None:
        """可用载荷能力 / Available payload capacity."""
        ac = _make_b747()
        agg = AircraftAggregation.create(aircraft=(ac,))
        ctx = AircraftContext.create(
            aircraft_aggregation=agg,
            current_registration="B-2447",
            current_payload_weight=100_000.0,
        )
        capacity = ctx.available_payload_capacity
        assert capacity > 0.0

    def test_with_fuel_and_payload(self) -> None:
        """with_fuel 和 with_payload 更新 / Fuel and payload update."""
        agg = AircraftAggregation.create(aircraft=(_make_b747(),))
        ctx = AircraftContext.create(
            aircraft_aggregation=agg,
            current_registration="B-2447",
        )
        ctx2 = ctx.with_fuel(50_000.0)
        ctx3 = ctx2.with_payload(80_000.0)
        assert ctx3.remaining_fuel_weight == 50_000.0
        assert ctx3.current_payload_weight == 80_000.0


class TestWeightValidator:
    """AircraftWeightValidator 测试 / Weight validator tests."""

    def test_takeoff_within_limit(self) -> None:
        """起飞重量在限内 / Takeoff weight within limit."""
        ac = _make_b747()
        v = AircraftWeightValidator()
        result = v.validate_takeoff(
            aircraft=ac,
            current_weight=350_000.0,
        )
        assert result.is_ok()
        data = result.unwrap()
        assert data.is_valid is True
        assert data.margin > 0

    def test_takeoff_exceeds_limit(self) -> None:
        """起飞重量超限 / Takeoff weight exceeds limit."""
        ac = _make_b747()
        v = AircraftWeightValidator()
        result = v.validate_takeoff(
            aircraft=ac,
            current_weight=400_000.0,
        )
        assert result.is_failed()

    def test_landing_validation(self) -> None:
        """着陆重量校验 / Landing weight validation."""
        ac = _make_b747()
        v = AircraftWeightValidator()
        ok = v.validate_landing(aircraft=ac, current_weight=250_000.0)
        assert ok.is_ok()
        fail = v.validate_landing(aircraft=ac, current_weight=270_000.0)
        assert fail.is_failed()

    def test_validate_for_phase(self) -> None:
        """按阶段校验 / Phase-based validation."""
        ac = _make_b747()
        v = AircraftWeightValidator()
        result = v.validate_for_phase(
            aircraft=ac,
            current_weight=300_000.0,
            phase=FlightPhase.TAKEOFF,
        )
        assert result.is_ok()


class TestBalanceCalculator:
    """AircraftBalanceCalculator 测试 / Balance calculator tests."""

    def test_cg_with_no_loads(self) -> None:
        """无载荷重心 / CG with no loads."""
        ac = _make_b747()
        calc = AircraftBalanceCalculator()
        result = calc.calculate_cg(
            aircraft=ac,
            loads=(),
            empty_weight=180_000.0,
            empty_cg_x=25.0,
            fuel_weight=50_000.0,
            fuel_cg_x=20.0,
            max_cg_offset=5.0,
        )
        assert result.total_weight == pytest.approx(230_000.0)
        assert result.is_balanced is True

    def test_cg_with_loads(self) -> None:
        """有载荷重心 / CG with loads."""
        ac = _make_b747()
        calc = AircraftBalanceCalculator()
        loads = (
            LoadItem(
                weight=10_000.0,
                position=Position.create(x=30.0, y=0.0, z=0.0, deck_id="lower"),
                item_id="cargo_1",
            ),
        )
        result = calc.calculate_cg(
            aircraft=ac,
            loads=loads,
            empty_weight=180_000.0,
            empty_cg_x=25.0,
            fuel_weight=50_000.0,
            fuel_cg_x=20.0,
            max_cg_offset=5.0,
        )
        assert result.total_weight == pytest.approx(240_000.0)

    def test_ballast_calculation(self) -> None:
        """压舱物计算 / Ballast weight calculation."""
        calc = AircraftBalanceCalculator()
        ballast = calc.calculate_required_ballast(
            current_cg_x=26.0,
            target_cg_x=25.0,
            total_weight=200_000.0,
            ballast_position_x=10.0,
        )
        assert ballast > 0


class TestCapacityChecker:
    """AircraftCapacityChecker 测试 / Capacity checker tests."""

    def test_cargo_fits(self) -> None:
        """货物可装入 / Cargo fits."""
        ac = _make_b747()
        checker = AircraftCapacityChecker()
        result = checker.check_cargo_fit(
            aircraft=ac,
            cargo_volume=10.0,
            cargo_weight=20_000.0,
            current_used_volume=100.0,
            current_used_weight=100_000.0,
        )
        assert result.is_ok()

    def test_volume_overflow(self) -> None:
        """体积溢出 / Volume overflow."""
        ac = _make_b747()
        checker = AircraftCapacityChecker()
        result = checker.check_cargo_fit(
            aircraft=ac,
            cargo_volume=200.0,
            cargo_weight=1_000.0,
            current_used_volume=0.0,
            current_used_weight=0.0,
        )
        assert result.is_failed()

    def test_utilization_estimate(self) -> None:
        """利用率估算 / Utilization estimate."""
        ac = _make_b747()
        checker = AircraftCapacityChecker()
        vol, wt = checker.estimate_utilization(
            aircraft=ac,
            total_cargo_volume=80.0,
            total_cargo_weight=100_000.0,
        )
        assert 0.0 < vol < 1.0
        assert 0.0 < wt < 1.0


class TestPositionAndDeck:
    """Position 和 Deck 测试 / Position and Deck tests."""

    def test_position_distance(self) -> None:
        """位置距离计算 / Position distance calculation."""
        p1 = Position.create(x=0.0, y=0.0, z=0.0, deck_id="d1")
        p2 = Position.create(x=3.0, y=4.0, z=0.0, deck_id="d1")
        assert p1.distance_to(p2) == pytest.approx(5.0)

    def test_position_translated(self) -> None:
        """位置平移 / Position translation."""
        p = Position.origin(deck_id="d1")
        t = p.translated(dx=1.0, dy=2.0, dz=3.0)
        assert t.x == pytest.approx(1.0)
        assert t.y == pytest.approx(2.0)
        assert t.z == pytest.approx(3.0)

    def test_deck_volume(self) -> None:
        """甲板体积 / Deck volume."""
        d = Deck.create(
            deck_id="lower",
            aircraft_type="B747",
            width=5.0,
            height=2.5,
            depth=20.0,
            max_load=50_000.0,
        )
        assert d.volume == pytest.approx(250.0)

    def test_deck_floor_area(self) -> None:
        """甲板底面积 / Deck floor area."""
        d = Deck.create(
            deck_id="lower",
            aircraft_type="B747",
            width=5.0,
            height=2.5,
            depth=20.0,
            max_load=50_000.0,
        )
        assert d.floor_area == pytest.approx(100.0)
