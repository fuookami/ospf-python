"""TaskDemand model tests / 任务需求模型测试.

Exercises TaskDemand properties and methods.
覆盖 TaskDemand 的属性和方法。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.task.model.task_demand import (
    TaskDemand,
)


class TestTaskDemandCreate:
    """TaskDemand creation tests / 创建测试."""

    def test_create_direct(self) -> None:
        """Direct construction. / 直接构造."""
        td = TaskDemand(task_key="t1", resource_key="r1", amount=5.0)
        assert td.task_key == "t1"
        assert td.resource_key == "r1"
        assert td.amount == pytest.approx(5.0)
        assert td.min_amount is None
        assert td.max_amount is None

    def test_create_factory(self) -> None:
        """Factory method. / 工厂方法."""
        td = TaskDemand.create(
            task_key="t1",
            resource_key="r1",
            amount=5.0,
            min_amount=3.0,
            max_amount=8.0,
        )
        assert td.min_amount == pytest.approx(3.0)
        assert td.max_amount == pytest.approx(8.0)

    def test_frozen(self) -> None:
        """Immutable. / 不可变."""
        td = TaskDemand(task_key="t1", resource_key="r1", amount=5.0)
        with pytest.raises(AttributeError):
            td.amount = 10.0  # type: ignore[misc]


class TestTaskDemandProperties:
    """Property tests / 属性测试."""

    def test_effective_min_with_value(self) -> None:
        """Effective min uses min_amount. / 有效最小值使用 min_amount."""
        td = TaskDemand(
            task_key="t1",
            resource_key="r1",
            amount=5.0,
            min_amount=3.0,
        )
        assert td.effective_min == pytest.approx(3.0)

    def test_effective_min_defaults_to_amount(self) -> None:
        """Effective min defaults to amount. / 有效最小值默认等于 amount."""
        td = TaskDemand(task_key="t1", resource_key="r1", amount=5.0)
        assert td.effective_min == pytest.approx(5.0)

    def test_effective_max_with_value(self) -> None:
        """Effective max uses max_amount. / 有效最大值使用 max_amount."""
        td = TaskDemand(
            task_key="t1",
            resource_key="r1",
            amount=5.0,
            max_amount=8.0,
        )
        assert td.effective_max == pytest.approx(8.0)

    def test_effective_max_defaults_to_amount(self) -> None:
        """Effective max defaults to amount. / 有效最大值默认等于 amount."""
        td = TaskDemand(task_key="t1", resource_key="r1", amount=5.0)
        assert td.effective_max == pytest.approx(5.0)

    def test_is_flexible_true(self) -> None:
        """Flexible when min != max. / min != max 时可灵活."""
        td = TaskDemand(
            task_key="t1",
            resource_key="r1",
            amount=5.0,
            min_amount=3.0,
            max_amount=8.0,
        )
        assert td.is_flexible is True

    def test_is_flexible_false(self) -> None:
        """Not flexible when min == max. / min == max 时不可灵活."""
        td = TaskDemand(task_key="t1", resource_key="r1", amount=5.0)
        assert td.is_flexible is False


class TestTaskDemandMethods:
    """Method tests / 方法测试."""

    def test_is_satisfied_by_true(self) -> None:
        """Satisfied when available >= min. / 可用量 >= 最小值时满足."""
        td = TaskDemand(
            task_key="t1",
            resource_key="r1",
            amount=5.0,
            min_amount=3.0,
        )
        assert td.is_satisfied_by(4.0) is True

    def test_is_satisfied_by_false(self) -> None:
        """Not satisfied when available < min. / 可用量 < 最小值时不满足."""
        td = TaskDemand(
            task_key="t1",
            resource_key="r1",
            amount=5.0,
            min_amount=3.0,
        )
        assert td.is_satisfied_by(2.0) is False

    def test_with_amount(self) -> None:
        """Create copy with new amount. / 创建不同需求量的副本."""
        td = TaskDemand(task_key="t1", resource_key="r1", amount=5.0)
        td2 = td.with_amount(10.0)
        assert td2.amount == pytest.approx(10.0)
        assert td.amount == pytest.approx(5.0)
