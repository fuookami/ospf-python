"""ResourceDemand model tests / 资源需求模型测试.

Exercises ResourceDemand properties and methods.
覆盖 ResourceDemand 的属性和方法。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand import (
    ResourceDemand,
)


class TestResourceDemandCreate:
    """Creation tests / 创建测试."""

    def test_create_direct(self) -> None:
        """Direct construction. / 直接构造."""
        rd = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        assert rd.resource_key == "r1"
        assert rd.task_key == "t1"
        assert rd.demand_amount == pytest.approx(5.0)
        assert rd.is_mandatory is True

    def test_frozen(self) -> None:
        """Immutable. / 不可变."""
        rd = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        with pytest.raises(AttributeError):
            rd.demand_amount = 10.0  # type: ignore[misc]


class TestResourceDemandProperties:
    """Property tests / 属性测试."""

    def test_duration(self) -> None:
        """Duration = end - start. / 时长 = 结束 - 开始."""
        rd = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=2.0,
            time_window_end=8.0,
            demand_amount=5.0,
        )
        assert rd.duration == pytest.approx(6.0)


class TestResourceDemandMethods:
    """Method tests / 方法测试."""

    def test_overlaps_same_resource_true(self) -> None:
        """Overlapping demands on same resource. / 同资源重叠需求."""
        rd1 = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        rd2 = ResourceDemand(
            resource_key="r1",
            task_key="t2",
            time_window_start=5.0,
            time_window_end=15.0,
            demand_amount=3.0,
        )
        assert rd1.overlaps_with(rd2) is True

    def test_overlaps_same_resource_false(self) -> None:
        """Non-overlapping demands on same resource. / 同资源不重叠需求."""
        rd1 = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=5.0,
            demand_amount=5.0,
        )
        rd2 = ResourceDemand(
            resource_key="r1",
            task_key="t2",
            time_window_start=10.0,
            time_window_end=15.0,
            demand_amount=3.0,
        )
        assert rd1.overlaps_with(rd2) is False

    def test_overlaps_different_resource(self) -> None:
        """No overlap on different resources. / 不同资源无重叠."""
        rd1 = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        rd2 = ResourceDemand(
            resource_key="r2",
            task_key="t2",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=3.0,
        )
        assert rd1.overlaps_with(rd2) is False

    def test_with_amount(self) -> None:
        """Create copy with new amount. / 创建不同需求量的副本."""
        rd = ResourceDemand(
            resource_key="r1",
            task_key="t1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        rd2 = rd.with_amount(8.0)
        assert rd2.demand_amount == pytest.approx(8.0)
        assert rd.demand_amount == pytest.approx(5.0)
        assert rd2.resource_key == "r1"
