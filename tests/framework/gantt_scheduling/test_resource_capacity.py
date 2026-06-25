"""Tests for ResourceCapacity.

资源容量测试。
"""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_capacity import (
    ResourceCapacity,
)


class TestResourceCapacityBasic:
    """ResourceCapacity 基本测试。"""

    def test_create(self) -> None:
        """创建容量记录。"""
        rc = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
        )
        assert rc.resource_key == "res-1"
        assert rc.max_capacity == 10.0
        assert rc.used_capacity == 0.0

    def test_frozen(self) -> None:
        """不可变性。"""
        rc = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
        )
        assert hasattr(rc, "__dataclass_fields__")

    def test_remaining_capacity(self) -> None:
        """剩余容量。"""
        rc = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
            used_capacity=3.0,
        )
        assert rc.remaining_capacity == 7.0

    def test_remaining_capacity_clamped(self) -> None:
        """剩余容量不为负。"""
        rc = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
            used_capacity=15.0,
        )
        assert rc.remaining_capacity == 0.0

    def test_utilization_ratio(self) -> None:
        """利用率。"""
        rc = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
            used_capacity=6.0,
        )
        assert rc.utilization_ratio == 0.6

    def test_utilization_ratio_zero_capacity(self) -> None:
        """零容量时利用率返回 0。"""
        rc = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=0.0,
        )
        assert rc.utilization_ratio == 0.0

    def test_can_accommodate(self) -> None:
        """检查是否能容纳需求。"""
        rc = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
            used_capacity=6.0,
        )
        assert rc.can_accommodate(3.0) is True
        assert rc.can_accommodate(5.0) is False

    def test_with_usage(self) -> None:
        """创建增加使用量后的副本。"""
        rc = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
            used_capacity=3.0,
        )
        rc2 = rc.with_usage(4.0)
        assert rc.used_capacity == 3.0
        assert rc2.used_capacity == 7.0
