"""CuttingPlan tests.

Test CuttingPlan model creation, fields, and immutability.
测试切割计划模型创建、字段和不可变性。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.domain.material.model.cutting_plan import (
    CuttingPlan,
)
from ospf_python.framework.csp1d.domain.material.model.product import (
    Product,
)


class TestCuttingPlan:
    """CuttingPlan frozen dataclass tests."""

    def _make_product(self, name: str = "P1", width: float = 30.0) -> Product:
        """Helper to create a product. / 创建产品辅助方法。"""
        return Product(name=name, width=width, length=200.0, demand=10)

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        p = self._make_product()
        cp = CuttingPlan(
            material="Steel",
            products=((p, 3),),
            waste=10.0,
        )
        assert cp.material == "Steel"
        assert len(cp.products) == 1
        assert cp.products[0][1] == 3
        assert cp.waste == 10.0

    def test_empty_products(self) -> None:
        """Create with empty products tuple. / 空产品元组。"""
        cp = CuttingPlan(material="Steel", products=(), waste=100.0)
        assert len(cp.products) == 0

    def test_multiple_products(self) -> None:
        """Create with multiple products. / 多产品方案。"""
        p1 = self._make_product("P1", 30.0)
        p2 = self._make_product("P2", 40.0)
        cp = CuttingPlan(
            material="Steel",
            products=((p1, 2), (p2, 1)),
            waste=0.0,
        )
        assert len(cp.products) == 2

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        cp = CuttingPlan(material="Steel", products=(), waste=10.0)
        with pytest.raises(AttributeError):
            cp.material = "Copper"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Same field values yield equality. / 相同字段值相等。"""
        a = CuttingPlan(material="Steel", products=(), waste=10.0)
        b = CuttingPlan(material="Steel", products=(), waste=10.0)
        assert a == b

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        cp = CuttingPlan(material="Steel", products=(), waste=10.0)
        assert hash(cp) is not None
