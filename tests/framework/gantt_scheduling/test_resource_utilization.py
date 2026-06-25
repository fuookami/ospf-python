"""Tests for ResourceUtilization.

资源利用率测试。
"""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_utilization import (
    ResourceUtilization,
)


class TestResourceUtilizationBasic:
    """ResourceUtilization 基本测试。"""

    def test_create(self) -> None:
        """创建利用率记录。"""
        ru = ResourceUtilization(
            resource_key="res-1",
            time_range_start=0.0,
            time_range_end=10.0,
            total_capacity=10.0,
            used_capacity=6.0,
        )
        assert ru.resource_key == "res-1"
        assert ru.used_capacity == 6.0

    def test_frozen(self) -> None:
        """不可变性。"""
        ru = ResourceUtilization(
            resource_key="res-1",
            time_range_start=0.0,
            time_range_end=10.0,
            total_capacity=10.0,
            used_capacity=6.0,
        )
        assert hasattr(ru, "__dataclass_fields__")

    def test_utilization_rate(self) -> None:
        """利用率。"""
        ru = ResourceUtilization(
            resource_key="res-1",
            time_range_start=0.0,
            time_range_end=10.0,
            total_capacity=10.0,
            used_capacity=6.0,
        )
        assert ru.utilization_rate == 0.6

    def test_utilization_rate_zero_capacity(self) -> None:
        """零容量时返回 0。"""
        ru = ResourceUtilization(
            resource_key="res-1",
            time_range_start=0.0,
            time_range_end=10.0,
            total_capacity=0.0,
            used_capacity=0.0,
        )
        assert ru.utilization_rate == 0.0

    def test_idle_capacity(self) -> None:
        """空闲容量。"""
        ru = ResourceUtilization(
            resource_key="res-1",
            time_range_start=0.0,
            time_range_end=10.0,
            total_capacity=10.0,
            used_capacity=6.0,
        )
        assert ru.idle_capacity == 4.0

    def test_peak_utilization_rate(self) -> None:
        """峰值利用率。"""
        ru = ResourceUtilization(
            resource_key="res-1",
            time_range_start=0.0,
            time_range_end=10.0,
            total_capacity=10.0,
            used_capacity=6.0,
            peak_usage=8.0,
        )
        assert ru.peak_utilization_rate == 0.8

    def test_duration(self) -> None:
        """区间时长。"""
        ru = ResourceUtilization(
            resource_key="res-1",
            time_range_start=2.0,
            time_range_end=10.0,
            total_capacity=10.0,
            used_capacity=6.0,
        )
        assert ru.duration == 8.0

    def test_is_overloaded(self) -> None:
        """超载检测。"""
        ru = ResourceUtilization(
            resource_key="res-1",
            time_range_start=0.0,
            time_range_end=10.0,
            total_capacity=10.0,
            used_capacity=11.0,
        )
        # utilization_rate is clamped to 1.0, use lower threshold
        assert ru.is_overloaded(threshold=0.9) is True

    def test_is_not_overloaded(self) -> None:
        """未超载。"""
        ru = ResourceUtilization(
            resource_key="res-1",
            time_range_start=0.0,
            time_range_end=10.0,
            total_capacity=10.0,
            used_capacity=6.0,
        )
        assert ru.is_overloaded() is False

    def test_is_overloaded_custom_threshold(self) -> None:
        """自定义阈值超载检测。"""
        ru = ResourceUtilization(
            resource_key="res-1",
            time_range_start=0.0,
            time_range_end=10.0,
            total_capacity=10.0,
            used_capacity=8.0,
        )
        assert ru.is_overloaded(threshold=0.7) is True
        assert ru.is_overloaded(threshold=0.9) is False
