"""Tests for Resource model.

资源模型测试。
"""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_type import (
    ResourceType,
)


class TestResourceBasic:
    """Resource 基本属性测试。"""

    def test_create_with_defaults(self) -> None:
        """使用默认值创建。"""
        r = Resource(
            resource_key="res-1",
            name="Machine A",
            capacity=10.0,
        )
        assert r.resource_key == "res-1"
        assert r.name == "Machine A"
        assert r.capacity == 10.0
        assert r.resource_type == ResourceType.MACHINE
        assert r.availability == ()

    def test_create_with_all_fields(self) -> None:
        """使用所有字段创建。"""
        r = Resource(
            resource_key="res-2",
            name="Worker B",
            capacity=5.0,
            resource_type=ResourceType.WORKER,
            availability=((0.0, 10.0), (15.0, 20.0)),
        )
        assert r.resource_type == ResourceType.WORKER
        assert len(r.availability) == 2

    def test_frozen(self) -> None:
        """不可变性测试。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
        )
        assert hasattr(r, "__dataclass_fields__")

    def test_is_available_at_with_no_windows(self) -> None:
        """无可用窗口时默认可用。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
        )
        assert r.is_available_at(5.0) is True

    def test_is_available_at_within_window(self) -> None:
        """在可用窗口内。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
            availability=((0.0, 10.0), (20.0, 30.0)),
        )
        assert r.is_available_at(5.0) is True
        assert r.is_available_at(25.0) is True

    def test_is_available_at_outside_window(self) -> None:
        """在可用窗口外。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
            availability=((0.0, 10.0), (20.0, 30.0)),
        )
        assert r.is_available_at(15.0) is False

    def test_available_during_with_no_windows(self) -> None:
        """无窗口时整个区间可用。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
        )
        assert r.available_during(start=0.0, end=100.0) is True

    def test_available_during_fully_covered(self) -> None:
        """区间完全被窗口覆盖。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
            availability=((0.0, 20.0),),
        )
        assert r.available_during(start=5.0, end=15.0) is True

    def test_available_during_not_covered(self) -> None:
        """区间未被窗口覆盖。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
            availability=((0.0, 5.0),),
        )
        assert r.available_during(start=0.0, end=10.0) is False

    def test_effective_capacity_available(self) -> None:
        """可用时返回完整容量。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
            availability=((0.0, 20.0),),
        )
        assert (
            r.effective_capacity_during(
                start=5.0,
                end=15.0,
            )
            == 10.0
        )

    def test_effective_capacity_unavailable(self) -> None:
        """不可用时返回 0。"""
        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
            availability=((0.0, 5.0),),
        )
        assert (
            r.effective_capacity_during(
                start=0.0,
                end=10.0,
            )
            == 0.0
        )
