"""TaskAttribute model tests / 任务属性模型测试.

Exercises TaskAttribute factory method, properties, and copy.
覆盖 TaskAttribute 的工厂方法、属性和副本创建。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.task.model.task_attribute import (
    TaskAttribute,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_type import TaskType


class TestTaskAttributeCreate:
    """Creation tests / 创建测试."""

    def test_defaults(self) -> None:
        """Default values. / 默认值."""
        a = TaskAttribute()
        assert a.task_type is TaskType.FIXED
        assert a.priority == 0
        assert a.cancel_enabled is False
        assert a.delay_enabled is False
        assert a.advance_enabled is False
        assert a.max_delay is None
        assert a.max_advance is None
        assert a.parallelable is False
        assert a.divisible is False

    def test_create_factory(self) -> None:
        """Factory method with all fields. / 工厂方法全部字段."""
        a = TaskAttribute.create(
            task_type=TaskType.PREEMPTIVE,
            priority=5,
            cancel_enabled=True,
            delay_enabled=True,
            advance_enabled=True,
            max_delay=10.0,
            max_advance=5.0,
            parallelable=True,
            divisible=True,
        )
        assert a.task_type is TaskType.PREEMPTIVE
        assert a.priority == 5
        assert a.cancel_enabled is True
        assert a.max_delay == pytest.approx(10.0)
        assert a.max_advance == pytest.approx(5.0)

    def test_frozen(self) -> None:
        """Immutable. / 不可变."""
        a = TaskAttribute()
        with pytest.raises(AttributeError):
            a.priority = 1  # type: ignore[misc]


class TestTaskAttributeProperties:
    """Property tests / 属性测试."""

    def test_is_preemptive_true(self) -> None:
        """Preemptive when task_type is PREEMPTIVE. / PREEMPTIVE 类型时为可抢占."""
        a = TaskAttribute(task_type=TaskType.PREEMPTIVE)
        assert a.is_preemptive is True

    def test_is_preemptive_false(self) -> None:
        """Not preemptive for FIXED. / FIXED 类型非可抢占."""
        a = TaskAttribute(task_type=TaskType.FIXED)
        assert a.is_preemptive is False

    def test_effective_max_delay_disabled(self) -> None:
        """Zero when delay disabled. / 延迟禁用时为零."""
        a = TaskAttribute(delay_enabled=False, max_delay=10.0)
        assert a.effective_max_delay == pytest.approx(0.0)

    def test_effective_max_delay_with_value(self) -> None:
        """Value when delay enabled. / 延迟启用时返回值."""
        a = TaskAttribute(delay_enabled=True, max_delay=10.0)
        assert a.effective_max_delay == pytest.approx(10.0)

    def test_effective_max_delay_unlimited(self) -> None:
        """Inf when delay enabled but no max. / 启用但无上限时为 inf."""
        a = TaskAttribute(delay_enabled=True, max_delay=None)
        assert a.effective_max_delay == float("inf")

    def test_effective_max_advance_disabled(self) -> None:
        """Zero when advance disabled. / 提前禁用时为零."""
        a = TaskAttribute(advance_enabled=False, max_advance=5.0)
        assert a.effective_max_advance == pytest.approx(0.0)

    def test_effective_max_advance_with_value(self) -> None:
        """Value when advance enabled. / 提前启用时返回值."""
        a = TaskAttribute(advance_enabled=True, max_advance=5.0)
        assert a.effective_max_advance == pytest.approx(5.0)

    def test_effective_max_advance_unlimited(self) -> None:
        """Inf when advance enabled but no max. / 启用但无上限时为 inf."""
        a = TaskAttribute(advance_enabled=True, max_advance=None)
        assert a.effective_max_advance == float("inf")


class TestTaskAttributeMethods:
    """Method tests / 方法测试."""

    def test_with_priority(self) -> None:
        """Create copy with new priority. / 创建不同优先级的副本."""
        a = TaskAttribute(priority=1)
        a2 = a.with_priority(5)
        assert a2.priority == 5
        assert a.priority == 1
