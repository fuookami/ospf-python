"""TaskShadowPriceMap model tests / 任务影子价格映射模型测试.

Exercises ShadowPriceKey creation and TaskShadowPriceMap operations.
覆盖 ShadowPriceKey 创建和 TaskShadowPriceMap 操作。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.task.model.task_shadow_price_map import (
    ShadowPriceKey,
    TaskShadowPriceMap,
)


class TestShadowPriceKey:
    """ShadowPriceKey tests / 影子价格键测试."""

    def test_global_constraint(self) -> None:
        """Global constraint key. / 全局约束键."""
        key = ShadowPriceKey.global_constraint("c1")
        assert key.constraint_name == "c1"
        assert key.task_key is None
        assert key.executor_key is None

    def test_task_constraint(self) -> None:
        """Task constraint key. / 任务约束键."""
        key = ShadowPriceKey.task_constraint("c1", "t1")
        assert key.constraint_name == "c1"
        assert key.task_key == "t1"
        assert key.executor_key is None

    def test_executor_constraint(self) -> None:
        """Executor constraint key. / 执行者约束键."""
        key = ShadowPriceKey.executor_constraint("c1", "e1")
        assert key.constraint_name == "c1"
        assert key.task_key is None
        assert key.executor_key == "e1"

    def test_frozen(self) -> None:
        """Immutable. / 不可变."""
        key = ShadowPriceKey.global_constraint("c1")
        with pytest.raises(AttributeError):
            key.constraint_name = "x"  # type: ignore[misc]


class TestTaskShadowPriceMap:
    """TaskShadowPriceMap tests / 影子价格映射测试."""

    def test_get_default_zero(self) -> None:
        """Default price is 0.0. / 默认价格为 0.0."""
        m = TaskShadowPriceMap()
        key = ShadowPriceKey.global_constraint("c1")
        assert m.get(key) == pytest.approx(0.0)

    def test_set_and_get(self) -> None:
        """Set and get price. / 设置和获取价格."""
        m = TaskShadowPriceMap()
        key = ShadowPriceKey.global_constraint("c1")
        m.set(key, 3.5)
        assert m.get(key) == pytest.approx(3.5)

    def test_update(self) -> None:
        """Batch update. / 批量更新."""
        m = TaskShadowPriceMap()
        k1 = ShadowPriceKey.global_constraint("c1")
        k2 = ShadowPriceKey.global_constraint("c2")
        m.update({k1: 1.0, k2: 2.0})
        assert m.get(k1) == pytest.approx(1.0)
        assert m.get(k2) == pytest.approx(2.0)

    def test_clear(self) -> None:
        """Clear all prices. / 清空所有价格."""
        m = TaskShadowPriceMap()
        m.set(ShadowPriceKey.global_constraint("c1"), 1.0)
        m.clear()
        assert m.size == 0

    def test_keys(self) -> None:
        """Get registered keys. / 获取已注册的键."""
        m = TaskShadowPriceMap()
        k1 = ShadowPriceKey.global_constraint("c1")
        k2 = ShadowPriceKey.task_constraint("c2", "t1")
        m.set(k1, 1.0)
        m.set(k2, 2.0)
        assert len(m.keys) == 2

    def test_size(self) -> None:
        """Map size. / 映射大小."""
        m = TaskShadowPriceMap()
        assert m.size == 0
        m.set(ShadowPriceKey.global_constraint("c1"), 1.0)
        assert m.size == 1

    def test_get_task_price(self) -> None:
        """Get task-level price. / 获取任务级价格."""
        m = TaskShadowPriceMap()
        key = ShadowPriceKey.task_constraint("c1", "t1")
        m.set(key, 5.0)
        assert m.get_task_price("c1", "t1") == pytest.approx(5.0)

    def test_get_task_price_default(self) -> None:
        """Task price defaults to 0. / 任务价格默认为 0."""
        m = TaskShadowPriceMap()
        assert m.get_task_price("c1", "t1") == pytest.approx(0.0)

    def test_get_global_price(self) -> None:
        """Get global price. / 获取全局价格."""
        m = TaskShadowPriceMap()
        m.set(ShadowPriceKey.global_constraint("c1"), 7.0)
        assert m.get_global_price("c1") == pytest.approx(7.0)

    def test_get_executor_price(self) -> None:
        """Get executor-level price. / 获取执行者级价格."""
        m = TaskShadowPriceMap()
        m.set(ShadowPriceKey.executor_constraint("c1", "e1"), 4.0)
        assert m.get_executor_price("c1", "e1") == pytest.approx(4.0)

    def test_reduced_cost(self) -> None:
        """Compute reduced cost. / 计算缩减成本."""
        m = TaskShadowPriceMap()
        m.set(ShadowPriceKey.task_constraint("c1", "t1"), 3.0)
        m.set(ShadowPriceKey.task_constraint("c1", "t2"), 2.0)
        rc = m.reduced_cost(10.0, ("t1", "t2"), "c1")
        assert rc == pytest.approx(5.0)

    def test_contains(self) -> None:
        """Contains check. / 包含检查."""
        m = TaskShadowPriceMap()
        k = ShadowPriceKey.global_constraint("c1")
        assert k not in m
        m.set(k, 1.0)
        assert k in m

    def test_len(self) -> None:
        """Len check. / 长度检查."""
        m = TaskShadowPriceMap()
        assert len(m) == 0
        m.set(ShadowPriceKey.global_constraint("c1"), 1.0)
        assert len(m) == 1
