"""ResourceAvailability model tests / 资源可用性模型测试.

Exercises ResourceAvailability free-slot queries and occupation.
覆盖 ResourceAvailability 的空闲时段查询和占用操作。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_availability import (
    ResourceAvailability,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_type import (
    ResourceType,
)


def _make_resource(
    key: str = "r1",
    availability: tuple[tuple[float, float], ...] = (),
) -> Resource:
    """Helper to create a Resource. / 创建 Resource 的辅助函数."""
    return Resource(
        resource_key=key,
        name="M1",
        capacity=10.0,
        resource_type=ResourceType.MACHINE,
        availability=availability,
    )


class TestResourceAvailabilityCreate:
    """Creation tests / 创建测试."""

    def test_create_default(self) -> None:
        """Create with defaults. / 使用默认值创建."""
        r = _make_resource()
        ra = ResourceAvailability(resource=r)
        assert ra.resource_key == "r1"
        assert ra.occupied_windows == ()

    def test_create_with_occupations(self) -> None:
        """Create with occupied windows. / 创建时有占用窗口."""
        r = _make_resource()
        ra = ResourceAvailability(
            resource=r,
            occupied_windows=((2.0, 5.0),),
        )
        assert len(ra.occupied_windows) == 1

    def test_frozen(self) -> None:
        """Immutable. / 不可变."""
        r = _make_resource()
        ra = ResourceAvailability(resource=r)
        with pytest.raises(AttributeError):
            ra.occupied_windows = ()  # type: ignore[misc]


class TestResourceAvailabilityFreeCheck:
    """Free-at checks / 空闲检查测试."""

    def test_free_at_no_occupation(self) -> None:
        """Free when no occupation. / 无占用时空闲."""
        r = _make_resource(availability=((0.0, 20.0),))
        ra = ResourceAvailability(resource=r)
        assert ra.is_free_at(10.0) is True

    def test_free_at_occupied(self) -> None:
        """Not free when occupied. / 占用时不空闲."""
        r = _make_resource(availability=((0.0, 20.0),))
        ra = ResourceAvailability(
            resource=r,
            occupied_windows=((5.0, 10.0),),
        )
        assert ra.is_free_at(7.0) is False

    def test_free_at_outside_availability(self) -> None:
        """Not free outside availability. / 不在可用窗口时不空闲."""
        r = _make_resource(availability=((0.0, 10.0),))
        ra = ResourceAvailability(resource=r)
        assert ra.is_free_at(15.0) is False


class TestResourceAvailabilityFreeSlots:
    """Free slots tests / 空闲时段测试."""

    def test_free_slots_no_occupation(self) -> None:
        """Full slot when no occupation. / 无占用时整个时段空闲."""
        r = _make_resource(availability=((0.0, 20.0),))
        ra = ResourceAvailability(resource=r)
        slots = ra.free_slots_within(start=0.0, end=20.0)
        assert len(slots) == 1
        assert slots[0] == (0.0, 20.0)

    def test_free_slots_with_occupation(self) -> None:
        """Slots split by occupation. / 占用分割空闲时段."""
        r = _make_resource(availability=((0.0, 20.0),))
        ra = ResourceAvailability(
            resource=r,
            occupied_windows=((5.0, 10.0),),
        )
        slots = ra.free_slots_within(start=0.0, end=20.0)
        assert len(slots) == 2
        assert slots[0] == (0.0, 5.0)
        assert slots[1] == (10.0, 20.0)

    def test_free_slots_not_available(self) -> None:
        """Empty when resource not available. / 资源不可用时时段为空."""
        r = _make_resource(availability=((0.0, 5.0),))
        ra = ResourceAvailability(resource=r)
        slots = ra.free_slots_within(start=0.0, end=20.0)
        assert slots == ()

    def test_free_slots_multiple_occupations(self) -> None:
        """Multiple occupations. / 多个占用."""
        r = _make_resource(availability=((0.0, 30.0),))
        ra = ResourceAvailability(
            resource=r,
            occupied_windows=((5.0, 10.0), (15.0, 20.0)),
        )
        slots = ra.free_slots_within(start=0.0, end=30.0)
        assert len(slots) == 3


class TestResourceAvailabilityMutation:
    """Mutation tests (immutable returns) / 变更测试."""

    def test_with_occupation(self) -> None:
        """Add occupation returns new instance. / 添加占用返回新实例."""
        r = _make_resource(availability=((0.0, 20.0),))
        ra = ResourceAvailability(resource=r)
        ra2 = ra.with_occupation(start=5.0, end=10.0)
        assert len(ra2.occupied_windows) == 1
        assert ra.occupied_windows == ()

    def test_total_occupied_duration(self) -> None:
        """Total occupied duration. / 总占用时长."""
        r = _make_resource()
        ra = ResourceAvailability(
            resource=r,
            occupied_windows=((2.0, 5.0), (8.0, 12.0)),
        )
        assert ra.total_occupied_duration == pytest.approx(7.0)

    def test_total_occupied_duration_empty(self) -> None:
        """Zero when no occupations. / 无占用时为零."""
        r = _make_resource()
        ra = ResourceAvailability(resource=r)
        assert ra.total_occupied_duration == pytest.approx(0.0)
