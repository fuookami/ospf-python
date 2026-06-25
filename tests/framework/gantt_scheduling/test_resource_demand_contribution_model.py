"""ResourceDemandContribution model tests / 资源需求贡献模型测试.

Exercises ResourceDemandContribution properties and methods.
覆盖 ResourceDemandContribution 的属性和方法。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand_contribution import (
    ResourceDemandContribution,
)


class TestResourceDemandContribution:
    """ResourceDemandContribution tests."""

    def test_create(self) -> None:
        """Create with fields. / 使用字段创建."""
        rdc = ResourceDemandContribution(
            task_key="t1",
            resource_key="r1",
            contribution_ratio=0.5,
            base_demand=10.0,
        )
        assert rdc.task_key == "t1"
        assert rdc.resource_key == "r1"
        assert rdc.contribution_ratio == pytest.approx(0.5)
        assert rdc.base_demand == pytest.approx(10.0)

    def test_effective_demand(self) -> None:
        """Effective demand = base * ratio. / 有效需求 = 基础 * 比例."""
        rdc = ResourceDemandContribution(
            task_key="t1",
            resource_key="r1",
            contribution_ratio=0.5,
            base_demand=10.0,
        )
        assert rdc.effective_demand == pytest.approx(5.0)

    def test_with_ratio(self) -> None:
        """Create copy with new ratio. / 创建不同比例的副本."""
        rdc = ResourceDemandContribution(
            task_key="t1",
            resource_key="r1",
            contribution_ratio=0.5,
            base_demand=10.0,
        )
        rdc2 = rdc.with_ratio(0.8)
        assert rdc2.contribution_ratio == pytest.approx(0.8)
        assert rdc.contribution_ratio == pytest.approx(0.5)
        assert rdc2.base_demand == pytest.approx(10.0)

    def test_frozen(self) -> None:
        """Immutable. / 不可变."""
        rdc = ResourceDemandContribution(
            task_key="t1",
            resource_key="r1",
            contribution_ratio=0.5,
            base_demand=10.0,
        )
        with pytest.raises(AttributeError):
            rdc.contribution_ratio = 1.0  # type: ignore[misc]
