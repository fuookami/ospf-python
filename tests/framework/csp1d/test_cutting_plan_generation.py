"""Cutting plan generation tests.

Test plan generation constraints and canonical keys.
测试计划生成约束和规范键。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.constraints import (
    Constraints,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.cutting_plan_canonical_key import (
    CuttingPlanCanonicalKey,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.cutting_plan_constraint import (
    CuttingPlanConstraint,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.model.generation_constraints import (
    GenerationConstraints,
)


class TestConstraints:
    """Constraints frozen dataclass tests."""

    def test_defaults(self) -> None:
        """Default values. / 默认值。"""
        c = Constraints()
        assert c.max_knife_count == 0
        assert c.min_length == 0.0
        assert c.max_length == float("inf")
        assert c.allow_waste is True
        assert c.precision == 1e-8

    def test_custom_values(self) -> None:
        """Custom values. / 自定义值。"""
        c = Constraints(
            max_knife_count=5,
            min_length=10.0,
            max_length=500.0,
            allow_waste=False,
        )
        assert c.max_knife_count == 5
        assert c.allow_waste is False

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        c = Constraints()
        with pytest.raises(AttributeError):
            c.max_knife_count = 10  # type: ignore[misc]


class TestCuttingPlanConstraint:
    """CuttingPlanConstraint frozen dataclass tests."""

    def test_defaults(self) -> None:
        """Default values. / 默认值。"""
        c = CuttingPlanConstraint()
        assert c.product_key == ""
        assert c.min_quantity == 0
        assert c.max_quantity == 0

    def test_is_active(self) -> None:
        """Active when min_quantity > 0. / 最小数量大于 0 时活跃。"""
        c = CuttingPlanConstraint(min_quantity=1)
        assert c.is_active is True

    def test_is_not_active(self) -> None:
        """Not active when min_quantity == 0. / 最小数量为 0 时不活跃。"""
        c = CuttingPlanConstraint(min_quantity=0)
        assert c.is_active is False

    def test_quantity_range(self) -> None:
        """Quantity range property. / 数量范围属性。"""
        c = CuttingPlanConstraint(min_quantity=1, max_quantity=10)
        assert c.quantity_range == (1, 10)

    def test_is_satisfied_by(self) -> None:
        """Check quantity satisfaction. / 检查数量满足。"""
        c = CuttingPlanConstraint(min_quantity=2, max_quantity=8)
        assert c.is_satisfied_by(5) is True
        assert c.is_satisfied_by(1) is False
        assert c.is_satisfied_by(9) is False

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        c = CuttingPlanConstraint()
        with pytest.raises(AttributeError):
            c.product_key = "x"  # type: ignore[misc]


class TestCuttingPlanCanonicalKey:
    """CuttingPlanCanonicalKey frozen dataclass tests."""

    def test_default_empty(self) -> None:
        """Default is empty pattern. / 默认空模式。"""
        k = CuttingPlanCanonicalKey()
        assert k.pattern == ()

    def test_create_from_dict(self) -> None:
        """Create from dict sorts by key. / 从字典创建按键排序。"""
        k = CuttingPlanCanonicalKey.create(items={"b": 2, "a": 1})
        assert k.pattern == (("a", 1), ("b", 2))

    def test_from_pairs(self) -> None:
        """Create from pairs sorts by key. / 从对创建按键排序。"""
        k = CuttingPlanCanonicalKey.from_pairs(pairs=(("b", 2), ("a", 1)))
        assert k.pattern == (("a", 1), ("b", 2))

    def test_product_keys(self) -> None:
        """Product keys property. / 产品键属性。"""
        k = CuttingPlanCanonicalKey.create(items={"a": 1, "b": 2})
        assert k.product_keys == ("a", "b")

    def test_total_quantity(self) -> None:
        """Total quantity property. / 总数量属性。"""
        k = CuttingPlanCanonicalKey.create(items={"a": 1, "b": 2})
        assert k.total_quantity == 3

    def test_contains_product(self) -> None:
        """Contains product check. / 包含产品检查。"""
        k = CuttingPlanCanonicalKey.create(items={"a": 1})
        assert k.contains_product("a") is True
        assert k.contains_product("b") is False

    def test_quantity_of(self) -> None:
        """Get quantity of product. / 获取产品数量。"""
        k = CuttingPlanCanonicalKey.create(items={"a": 3, "b": 5})
        assert k.quantity_of("a") == 3
        assert k.quantity_of("b") == 5
        assert k.quantity_of("c") == 0

    def test_equality(self) -> None:
        """Same pattern yields equality. / 相同模式相等。"""
        a = CuttingPlanCanonicalKey.create(items={"a": 1, "b": 2})
        b = CuttingPlanCanonicalKey.create(items={"b": 2, "a": 1})
        assert a == b

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        k = CuttingPlanCanonicalKey.create(items={"a": 1})
        assert hash(k) is not None


class TestGenerationConstraints:
    """GenerationConstraints frozen dataclass tests."""

    def test_defaults(self) -> None:
        """Default values. / 默认值。"""
        gc = GenerationConstraints()
        assert gc.max_depth == 100
        assert gc.max_solutions == 10000
        assert gc.product_constraints == ()

    def test_create_static(self) -> None:
        """Create via static method. / 静态方法创建。"""
        mat = Constraints(max_knife_count=5)
        prod = (CuttingPlanConstraint(product_key="P1", min_quantity=1),)
        gc = GenerationConstraints.create(
            material_constraints=mat,
            product_constraints=prod,
            max_depth=50,
        )
        assert gc.max_depth == 50
        assert gc.material_constraints.max_knife_count == 5

    def test_active_product_count(self) -> None:
        """Count active product constraints. / 统计活跃约束。"""
        gc = GenerationConstraints(
            product_constraints=(
                CuttingPlanConstraint(product_key="P1", min_quantity=1),
                CuttingPlanConstraint(product_key="P2", min_quantity=0),
            )
        )
        assert gc.active_product_count == 1

    def test_get_constraint_for(self) -> None:
        """Get constraint for product. / 获取产品约束。"""
        gc = GenerationConstraints(
            product_constraints=(
                CuttingPlanConstraint(product_key="P1", min_quantity=1),
            )
        )
        c = gc.get_constraint_for("P1")
        assert c is not None
        assert c.product_key == "P1"
        assert gc.get_constraint_for("P2") is None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        gc = GenerationConstraints()
        with pytest.raises(AttributeError):
            gc.max_depth = 50  # type: ignore[misc]
