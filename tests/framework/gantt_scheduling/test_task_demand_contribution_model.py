"""TaskDemandContribution model tests / 任务需求贡献模型测试.

Exercises TaskDemandContribution factory methods, properties, and
scaling.
覆盖 TaskDemandContribution 的工厂方法、属性和缩放。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.task.model.task_demand_contribution import (
    TaskDemandContribution,
)


class TestTaskDemandContributionCreate:
    """Creation tests / 创建测试."""

    def test_create_factory(self) -> None:
        """Factory method. / 工厂方法."""
        c = TaskDemandContribution.create(
            task_key="t1",
            resource_key="r1",
            coefficient=2.5,
        )
        assert c.task_key == "t1"
        assert c.resource_key == "r1"
        assert c.coefficient == pytest.approx(2.5)

    def test_consumption(self) -> None:
        """Consumption creates positive coefficient. / 消耗创建正系数."""
        c = TaskDemandContribution.consumption("t1", "r1", 3.0)
        assert c.coefficient == pytest.approx(3.0)
        assert c.is_consumption is True
        assert c.is_release is False

    def test_release(self) -> None:
        """Release creates negative coefficient. / 释放创建负系数."""
        c = TaskDemandContribution.release("t1", "r1", 2.0)
        assert c.coefficient == pytest.approx(-2.0)
        assert c.is_release is True
        assert c.is_consumption is False

    def test_frozen(self) -> None:
        """Immutable. / 不可变."""
        c = TaskDemandContribution.create(
            task_key="t1",
            resource_key="r1",
            coefficient=1.0,
        )
        with pytest.raises(AttributeError):
            c.coefficient = 2.0  # type: ignore[misc]


class TestTaskDemandContributionProperties:
    """Property tests / 属性测试."""

    def test_absolute_contribution(self) -> None:
        """Absolute value of coefficient. / 系数绝对值."""
        c = TaskDemandContribution.create(
            task_key="t1",
            resource_key="r1",
            coefficient=-3.5,
        )
        assert c.absolute_contribution == pytest.approx(3.5)

    def test_zero_coefficient_not_consumption(self) -> None:
        """Zero coefficient is neither consumption nor release. / 零系数既非消耗也非释放."""
        c = TaskDemandContribution.create(
            task_key="t1",
            resource_key="r1",
            coefficient=0.0,
        )
        assert c.is_consumption is False
        assert c.is_release is False


class TestTaskDemandContributionMethods:
    """Method tests / 方法测试."""

    def test_scaled(self) -> None:
        """Scale coefficient. / 缩放系数."""
        c = TaskDemandContribution.create(
            task_key="t1",
            resource_key="r1",
            coefficient=2.0,
        )
        c2 = c.scaled(3.0)
        assert c2.coefficient == pytest.approx(6.0)
        assert c2.task_key == "t1"
        assert c.coefficient == pytest.approx(2.0)
