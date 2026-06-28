"""BPP2D 约束上下文行为测试 / BPP2D constraint context behavioral tests.

测试 ConstraintContext 的注册、注销、查询和辅助方法。
Test ConstraintContext registration, unregistration, lookup, and helpers.
"""

from __future__ import annotations

from ospf_python.framework.bpp2d.domain.constraint.constraint_context import (
    ConstraintContext,
)
from ospf_python.framework.bpp2d.domain.constraint.model.geometric_constraint import (
    GeometricConstraint,
)
from ospf_python.framework.bpp2d.domain.constraint.model.weight_constraint import (
    WeightConstraint,
)


class TestConstraintContextBehavioral:
    """约束上下文行为测试 / Constraint context behavioral tests."""

    def test_unregister_constraint(self) -> None:
        """注销约束 / Unregister constraint."""
        ctx = ConstraintContext()
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            max_x=100.0,
            max_y=100.0,
        )
        ctx.register(gc)
        assert ctx.size == 1

        result = ctx.unregister("geo_1")
        assert result.is_ok()
        assert ctx.size == 0
        assert ctx.is_empty is True

    def test_unregister_nonexistent_constraint(self) -> None:
        """注销不存在的约束 / Unregister nonexistent constraint."""
        ctx = ConstraintContext()
        result = ctx.unregister("nonexistent")
        assert result.is_failed()

    def test_register_duplicate_constraint(self) -> None:
        """注册重复约束 / Register duplicate constraint."""
        ctx = ConstraintContext()
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            max_x=100.0,
            max_y=100.0,
        )
        ctx.register(gc)
        result = ctx.register(gc)
        assert result.is_failed()

    def test_get_or_error_found(self) -> None:
        """获取存在的约束 / Get existing constraint."""
        ctx = ConstraintContext()
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            max_x=100.0,
            max_y=100.0,
        )
        ctx.register(gc)
        result = ctx.get_or_error("geo_1")
        assert result.is_ok()
        assert result.unwrap().constraint_key == "geo_1"

    def test_get_or_error_not_found(self) -> None:
        """获取不存在的约束返回错误 / Get nonexistent constraint returns error."""
        ctx = ConstraintContext()
        result = ctx.get_or_error("nonexistent")
        assert result.is_failed()

    def test_get_returns_none_for_missing(self) -> None:
        """获取缺失约束返回 None / Get returns None for missing."""
        ctx = ConstraintContext()
        assert ctx.get("missing") is None

    def test_constraints_returns_all(self) -> None:
        """获取所有约束 / Get all constraints."""
        ctx = ConstraintContext()
        gc = GeometricConstraint.create(
            constraint_key="geo_1", max_x=100.0, max_y=100.0,
        )
        wc = WeightConstraint.create(
            constraint_key="wt_1", max_weight=50.0,
        )
        ctx.register(gc)
        ctx.register(wc)

        all_constraints = ctx.constraints()
        assert len(all_constraints) == 2

    def test_constraint_keys(self) -> None:
        """获取所有约束键 / Get all constraint keys."""
        ctx = ConstraintContext()
        gc = GeometricConstraint.create(
            constraint_key="geo_1", max_x=100.0, max_y=100.0,
        )
        wc = WeightConstraint.create(
            constraint_key="wt_1", max_weight=50.0,
        )
        ctx.register(gc)
        ctx.register(wc)

        keys = ctx.constraint_keys()
        assert "geo_1" in keys
        assert "wt_1" in keys

    def test_get_for_item(self) -> None:
        """按物品键查询约束 / Get constraints for item."""
        ctx = ConstraintContext()
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            item_keys=("r1", "r2"),
            max_x=100.0,
            max_y=100.0,
        )
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            max_weight=50.0,
        )
        ctx.register(gc)
        ctx.register(wc)

        r1_constraints = ctx.get_for_item("r1")
        assert len(r1_constraints) == 2  # gc applies to r1, wc applies to all

        r3_constraints = ctx.get_for_item("r3")
        assert len(r3_constraints) == 1  # only wc (applies to all)

    def test_contains(self) -> None:
        """检查约束是否存在 / Check constraint exists."""
        ctx = ConstraintContext()
        gc = GeometricConstraint.create(
            constraint_key="geo_1", max_x=100.0, max_y=100.0,
        )
        ctx.register(gc)
        assert ctx.contains("geo_1") is True
        assert ctx.contains("nonexistent") is False

    def test_is_empty_on_new_context(self) -> None:
        """新上下文为空 / New context is empty."""
        ctx = ConstraintContext()
        assert ctx.is_empty is True
        assert ctx.size == 0

    def test_clear(self) -> None:
        """清空约束 / Clear constraints."""
        ctx = ConstraintContext()
        gc = GeometricConstraint.create(
            constraint_key="geo_1", max_x=100.0, max_y=100.0,
        )
        ctx.register(gc)
        ctx.clear()
        assert ctx.is_empty is True
        assert ctx.size == 0
