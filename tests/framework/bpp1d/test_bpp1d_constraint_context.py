"""BPP1D 约束上下文行为测试 / BPP1D constraint context behavioral tests.

测试 ConstraintContext 的创建、注册和查询。
Test ConstraintContext creation, registration, and lookup.
"""

from __future__ import annotations

from ospf_python.framework.bpp1d.domain.constraint.constraint_context import (
    ConstraintContext,
)
from ospf_python.framework.bpp1d.domain.constraint.model.constraint import (
    Constraint,
)


class TestConstraintContextBehavioral:
    """约束上下文行为测试 / Constraint context behavioral tests."""

    def test_create_with_initial_constraints(self) -> None:
        """创建带初始约束的上下文 / Create context with initial constraints."""
        c = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a",),
            max_weight=10.0,
        )
        ctx = ConstraintContext.create(constraints={"w1": c})
        assert ctx.count == 1
        assert ctx.get("w1") is not None

    def test_create_with_none_constraints(self) -> None:
        """创建无初始约束的上下文 / Create context with None constraints."""
        ctx = ConstraintContext.create(constraints=None)
        assert ctx.count == 0

    def test_register_returns_new_context(self) -> None:
        """注册返回新上下文 / Register returns new context."""
        ctx = ConstraintContext.create()
        c = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a",),
            max_weight=10.0,
        )
        new_ctx = ctx.register(c)
        assert ctx.count == 0  # Original unchanged (immutable)
        assert new_ctx.count == 1

    def test_register_many(self) -> None:
        """批量注册约束 / Register many constraints."""
        c1 = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a",),
            max_weight=10.0,
        )
        c2 = Constraint.item_exclusion(
            constraint_key="e1",
            item_keys=("a", "b"),
        )
        ctx = ConstraintContext.create()
        new_ctx = ctx.register_many((c1, c2))
        assert new_ctx.count == 2

    def test_get_returns_none_for_missing(self) -> None:
        """查询不存在的约束返回 None / Get returns None for missing."""
        ctx = ConstraintContext.create()
        assert ctx.get("nonexistent") is None

    def test_get_all(self) -> None:
        """获取所有约束 / Get all constraints."""
        c1 = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a",),
            max_weight=10.0,
        )
        c2 = Constraint.item_exclusion(
            constraint_key="e1",
            item_keys=("a", "b"),
        )
        ctx = ConstraintContext.create().register_many((c1, c2))
        all_constraints = ctx.get_all()
        assert len(all_constraints) == 2

    def test_get_by_item(self) -> None:
        """按物品键查询约束 / Get constraints by item key."""
        c1 = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a", "b"),
            max_weight=10.0,
        )
        c2 = Constraint.item_exclusion(
            constraint_key="e1",
            item_keys=("c",),
        )
        ctx = ConstraintContext.create().register_many((c1, c2))
        a_constraints = ctx.get_by_item("a")
        assert len(a_constraints) == 1
        assert a_constraints[0].constraint_key == "w1"

        c_constraints = ctx.get_by_item("c")
        assert len(c_constraints) == 1
        assert c_constraints[0].constraint_key == "e1"

    def test_count_property(self) -> None:
        """约束数量属性 / Constraint count property."""
        ctx = ConstraintContext.create()
        assert ctx.count == 0
        c = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a",),
            max_weight=10.0,
        )
        ctx = ctx.register(c)
        assert ctx.count == 1
