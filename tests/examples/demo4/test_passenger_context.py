"""Passenger context 测试 / Passenger context tests.

覆盖 Passenger 创建、booking class、中转航班和
PassengerContext。
Covers Passenger creation, booking classes, connecting
flights, and PassengerContext.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from examples.framework_demo.demo4.domain.passenger.model.booking_class import (
    BookingClass,
)
from examples.framework_demo.demo4.domain.passenger.model.connecting_flight import (
    ConnectingFlight,
)
from examples.framework_demo.demo4.domain.passenger.model.passenger import (
    Passenger,
)
from examples.framework_demo.demo4.domain.passenger.model.passenger_aggregation import (
    PassengerAggregation,
)
from examples.framework_demo.demo4.domain.passenger.model.passenger_cancel import (
    CancelReason,
    PassengerCancel,
)
from examples.framework_demo.demo4.domain.passenger.model.passenger_context import (
    PassengerContext,
)
from examples.framework_demo.demo4.domain.passenger.model.passenger_result import (
    PassengerResult,
    PassengerStatus,
)
from examples.framework_demo.demo4.domain.passenger.service.passenger_allocator import (
    PassengerAllocator,
    SeatMap,
)


class TestBookingClass:
    """BookingClass 测试 / BookingClass tests."""

    def test_display_name(self) -> None:
        """显示名称 / Display name."""
        first_name = BookingClass.FIRST.display_name
        economy_name = BookingClass.ECONOMY.display_name
        assert "First" in first_name
        assert "Economy" in economy_name

    def test_code(self) -> None:
        """舱位代码 / Class code."""
        assert BookingClass.FIRST.code == "F"
        assert BookingClass.BUSINESS.code == "J"
        assert BookingClass.ECONOMY.code == "Y"

    def test_ordering(self) -> None:
        """排序 / Ordering."""
        assert BookingClass.FIRST < BookingClass.BUSINESS
        assert BookingClass.BUSINESS < BookingClass.ECONOMY


class TestPassenger:
    """Passenger 测试 / Passenger tests."""

    def test_is_first_class(self) -> None:
        """头等舱旅客 / First class passenger."""
        p = Passenger(
            passenger_id="P1",
            name="Zhang",
            booking_class=BookingClass.FIRST,
        )
        assert p.is_first_class is True
        assert p.is_business_class is False

    def test_has_connection(self) -> None:
        """有中转 / Has connection."""
        p = Passenger(
            passenger_id="P1",
            name="Zhang",
            booking_class=BookingClass.ECONOMY,
            connecting_flight="CA5678",
        )
        assert p.has_connection is True

    def test_priority_score(self) -> None:
        """优先级分数 / Priority score."""
        first = Passenger(
            passenger_id="P1",
            name="A",
            booking_class=BookingClass.FIRST,
        )
        economy = Passenger(
            passenger_id="P2",
            name="B",
            booking_class=BookingClass.ECONOMY,
        )
        assert first.priority_score < economy.priority_score

    def test_frozen(self) -> None:
        """不可变 / Frozen."""
        p = Passenger(
            passenger_id="P1",
            name="Zhang",
            booking_class=BookingClass.ECONOMY,
        )
        with pytest.raises(AttributeError):
            p.name = "X"  # type: ignore[misc]


class TestPassengerContext:
    """PassengerContext 测试 / PassengerContext tests."""

    def test_register_and_get(self) -> None:
        """注册和查询 / Register and get."""
        ctx = PassengerContext()
        p = Passenger(
            passenger_id="P1",
            name="Zhang",
            booking_class=BookingClass.FIRST,
        )
        ctx.register_passenger(p)
        assert ctx.passenger_count == 1
        assert ctx.get_passenger("P1") is p

    def test_get_passengers_by_class(self) -> None:
        """按舱位查询 / Get by class."""
        ctx = PassengerContext()
        ctx.register_passenger(
            Passenger(
                passenger_id="P1",
                name="A",
                booking_class=BookingClass.FIRST,
            )
        )
        ctx.register_passenger(
            Passenger(
                passenger_id="P2",
                name="B",
                booking_class=BookingClass.ECONOMY,
            )
        )
        first = ctx.get_passengers_by_class(BookingClass.FIRST)
        assert len(list(first)) == 1

    def test_get_connecting_passengers(self) -> None:
        """查询中转旅客 / Get connecting passengers."""
        ctx = PassengerContext()
        ctx.register_passenger(
            Passenger(
                passenger_id="P1",
                name="A",
                booking_class=BookingClass.ECONOMY,
                connecting_flight="CA9999",
            )
        )
        ctx.register_passenger(
            Passenger(
                passenger_id="P2",
                name="B",
                booking_class=BookingClass.ECONOMY,
            )
        )
        connecting = ctx.get_connecting_passengers()
        assert len(list(connecting)) == 1

    def test_register_result(self) -> None:
        """注册结果 / Register result."""
        ctx = PassengerContext()
        r = PassengerResult(
            passenger_id="P1",
            status=PassengerStatus.CONFIRMED,
            seat="12A",
        )
        ctx.register_result(r)
        result = ctx.get_result("P1")
        assert result is r
        assert result is not None and result.is_confirmed is True

    def test_register_cancellation(self) -> None:
        """注册取消 / Register cancellation."""
        ctx = PassengerContext()
        c = PassengerCancel(
            passenger_id="P1",
            reason=CancelReason.PASSENGER_REQUEST,
            refund_amount=500.0,
        )
        ctx.register_cancellation(c)
        got = ctx.get_cancellation("P1")
        assert got is c
        assert got.has_refund is True

    def test_build_aggregation(self) -> None:
        """构建聚合 / Build aggregation."""
        ctx = PassengerContext()
        ctx.register_passenger(
            Passenger(
                passenger_id="P1",
                name="A",
                booking_class=BookingClass.FIRST,
            )
        )
        ctx.register_passenger(
            Passenger(
                passenger_id="P2",
                name="B",
                booking_class=BookingClass.ECONOMY,
            )
        )
        agg = ctx.build_aggregation()
        assert agg.total_count == 2
        assert agg.first_class_count == 1


class TestPassengerAggregation:
    """PassengerAggregation 测试 / Aggregation tests."""

    def test_from_passengers(self) -> None:
        """从旅客列表构建 / Build from passengers."""
        passengers = (
            Passenger(
                passenger_id="P1",
                name="A",
                booking_class=BookingClass.FIRST,
            ),
            Passenger(
                passenger_id="P2",
                name="B",
                booking_class=BookingClass.BUSINESS,
            ),
        )
        agg = PassengerAggregation.from_passengers(passengers)
        assert agg.total_count == 2

    def test_premium_ratio(self) -> None:
        """高端旅客比例 / Premium ratio."""
        passengers = (
            Passenger(
                passenger_id="P1",
                name="A",
                booking_class=BookingClass.FIRST,
            ),
            Passenger(
                passenger_id="P2",
                name="B",
                booking_class=BookingClass.ECONOMY,
            ),
            Passenger(
                passenger_id="P3",
                name="C",
                booking_class=BookingClass.ECONOMY,
            ),
        )
        agg = PassengerAggregation.from_passengers(passengers)
        assert agg.premium_ratio == pytest.approx(1 / 3)


class TestConnectingFlight:
    """ConnectingFlight 测试 / Connecting flight tests."""

    def test_layover_minutes(self) -> None:
        """中转时间 / Layover minutes."""
        cf = ConnectingFlight(
            from_flight="CA1234",
            to_flight="CA5678",
            layover_time=timedelta(hours=2, minutes=30),
        )
        assert cf.layover_minutes == 150

    def test_is_minimum_connection(self) -> None:
        """最短中转 / Minimum connection.

        需要 >= 45 分钟才满足最低中转时间。
        Requires >= 45 minutes for minimum connection.
        """
        meets = ConnectingFlight(
            from_flight="CA1234",
            to_flight="CA5678",
            layover_time=timedelta(minutes=60),
        )
        too_short = ConnectingFlight(
            from_flight="CA1234",
            to_flight="CA5678",
            layover_time=timedelta(minutes=20),
        )
        assert meets.is_minimum_connection is True
        assert too_short.is_minimum_connection is False

    def test_connection_key(self) -> None:
        """中转键 / Connection key."""
        cf = ConnectingFlight(
            from_flight="CA1234",
            to_flight="CA5678",
            layover_time=timedelta(hours=1),
        )
        assert cf.connection_key == "CA1234->CA5678"


class TestPassengerAllocator:
    """PassengerAllocator 测试 / Allocator tests."""

    def test_allocate_basic(self) -> None:
        """基本分配 / Basic allocation."""
        allocator = PassengerAllocator()
        passengers = [
            Passenger(
                passenger_id=f"P{i}",
                name=f"P{i}",
                booking_class=BookingClass.ECONOMY,
            )
            for i in range(5)
        ]
        seat_map = SeatMap(
            aircraft_type="A320",
            economy_class_rows=30,
            seats_per_row=6,
        )
        result = allocator.allocate(passengers, seat_map)
        assert result.allocated_count == 5
        assert result.waitlisted_count == 0

    def test_overbooking_waitlist(self) -> None:
        """超售候补 / Overbooking waitlist."""
        allocator = PassengerAllocator()
        passengers = [
            Passenger(
                passenger_id=f"P{i}",
                name=f"P{i}",
                booking_class=BookingClass.ECONOMY,
            )
            for i in range(200)
        ]
        seat_map = SeatMap(
            aircraft_type="A320",
            economy_class_rows=10,
            seats_per_row=6,
        )
        result = allocator.allocate(passengers, seat_map)
        assert result.waitlisted_count > 0
