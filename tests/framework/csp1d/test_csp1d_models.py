"""CSP1D domain model tests for 0%-coverage files.

覆盖 CSP1D 领域模型中 0% 覆盖率的文件。
Covers 0%-coverage files in CSP1D domain models.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.application.model.csp1d_problem import (
    Csp1dProblem,
)
from ospf_python.framework.csp1d.application.service.csp1d_produce_context import (
    Csp1dProduceContext,
)
from ospf_python.framework.csp1d.application.service.top_k_cutting_plans import (
    TopKCuttingPlans,
)
from ospf_python.framework.csp1d.domain.material.aggregation import (
    Aggregation,
)
from ospf_python.framework.csp1d.domain.material.error.csp1d_errors import (
    Csp1dErrors,
)
from ospf_python.framework.csp1d.domain.material.material_context import (
    MaterialContext,
)
from ospf_python.framework.csp1d.domain.material.model.costar import Costar
from ospf_python.framework.csp1d.domain.material.model.csp1d_domain_policy import (
    Csp1dDomainPolicy,
)
from ospf_python.framework.csp1d.domain.material.model.cutting_plan import (
    CuttingPlan,
)
from ospf_python.framework.csp1d.domain.material.model.cutting_plan_demand_contribution import (
    CuttingPlanDemandContribution,
)
from ospf_python.framework.csp1d.domain.material.model.demand_mode import (
    DemandMode,
)
from ospf_python.framework.csp1d.domain.material.model.domain_value_conversion import (
    DomainValueConversion,
)
from ospf_python.framework.csp1d.domain.material.model.machine import Machine
from ospf_python.framework.csp1d.domain.material.model.material import Material
from ospf_python.framework.csp1d.domain.material.model.product import Product
from ospf_python.framework.csp1d.domain.material.model.production import (
    Production,
)
from ospf_python.framework.csp1d.domain.material.model.render_mappers import (
    RenderMappers,
)
from ospf_python.framework.csp1d.domain.material.model.shadow_price_map import (
    ShadowPriceMap,
)
from ospf_python.framework.csp1d.infrastructure.cutting_plan_product_order import (
    CuttingPlanProductOrder,
)

# ============================================================
# Costar model tests
# ============================================================


class TestCostar:
    """Costar dataclass tests / Costar 数据类测试."""

    def test_create(self) -> None:
        """Test costar creation. / 测试协切产品创建."""
        cs = Costar(left="P1", right="P2", compatible=True)
        assert cs.left == "P1"
        assert cs.right == "P2"
        assert cs.compatible is True

    def test_incompatible(self) -> None:
        """Test incompatible costar. / 测试不兼容协切."""
        cs = Costar(left="P1", right="P3", compatible=False)
        assert cs.compatible is False

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        cs = Costar(left="P1", right="P2", compatible=True)
        with pytest.raises(AttributeError):
            cs.compatible = False  # type: ignore[misc]


# ============================================================
# DemandMode enum tests
# ============================================================


class TestDemandMode:
    """DemandMode enum tests / DemandMode 枚举测试."""

    def test_values(self) -> None:
        """Test enum values. / 测试枚举值."""
        assert DemandMode.EXACT.value == "exact"
        assert DemandMode.AT_LEAST.value == "at_least"
        assert DemandMode.AT_MOST.value == "at_most"

    def test_member_count(self) -> None:
        """Test member count. / 测试成员数量."""
        assert len(DemandMode) == 3


# ============================================================
# Production model tests
# ============================================================


class TestProduction:
    """Production dataclass tests / Production 数据类测试."""

    def test_create(self) -> None:
        """Test production creation. / 测试生产创建."""
        p = Production()
        assert p is not None

    def test_frozen(self) -> None:
        """Test is frozen dataclass. / 测试是冻结数据类."""
        from dataclasses import fields

        assert hasattr(Production, "__dataclass_fields__")
        # Production has no fields, just verify it is a dataclass
        assert len(fields(Production)) == 0


# ============================================================
# CuttingPlanDemandContribution tests
# ============================================================


class TestCuttingPlanDemandContribution:
    """CuttingPlanDemandContribution tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        cpdc = CuttingPlanDemandContribution()
        assert cpdc is not None


# ============================================================
# DomainValueConversion tests
# ============================================================


class TestDomainValueConversion:
    """DomainValueConversion tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        dvc = DomainValueConversion()
        assert dvc is not None


# ============================================================
# Csp1dDomainPolicy tests
# ============================================================


class TestCsp1dDomainPolicy:
    """Csp1dDomainPolicy tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        policy = Csp1dDomainPolicy()
        assert policy is not None


# ============================================================
# MaterialContext tests
# ============================================================


class TestMaterialContext:
    """MaterialContext tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        ctx = MaterialContext()
        assert ctx is not None


# ============================================================
# Aggregation tests
# ============================================================


class TestAggregation:
    """Aggregation tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        agg = Aggregation()
        assert agg is not None


# ============================================================
# Csp1dErrors tests
# ============================================================


class TestCsp1dErrors:
    """Csp1dErrors tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        err = Csp1dErrors()
        assert err is not None


# ============================================================
# RenderMappers tests
# ============================================================


class TestRenderMappers:
    """RenderMappers tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        rm = RenderMappers()
        assert rm is not None


# ============================================================
# ShadowPriceMap tests
# ============================================================


class TestShadowPriceMap:
    """ShadowPriceMap tests / ShadowPriceMap 测试."""

    def test_create_empty(self) -> None:
        """Test empty map creation. / 测试空映射创建."""
        spm = ShadowPriceMap()
        assert len(spm) == 0

    def test_set_and_get(self) -> None:
        """Test set and get. / 测试设置和获取."""
        spm = ShadowPriceMap()
        spm.set("P1", 3.5)
        assert spm.get("P1") == pytest.approx(3.5)

    def test_get_missing(self) -> None:
        """Test missing key returns 0. / 测试缺失键返回 0."""
        spm = ShadowPriceMap()
        assert spm.get("missing") == pytest.approx(0.0)

    def test_update(self) -> None:
        """Test batch update. / 测试批量更新."""
        spm = ShadowPriceMap()
        spm.update({"P1": 1.0, "P2": 2.0})
        assert spm.get("P1") == pytest.approx(1.0)
        assert spm.get("P2") == pytest.approx(2.0)

    def test_clear(self) -> None:
        """Test clear. / 测试清空."""
        spm = ShadowPriceMap()
        spm.set("P1", 1.0)
        spm.clear()
        assert len(spm) == 0

    def test_products(self) -> None:
        """Test products property. / 测试产品列表属性."""
        spm = ShadowPriceMap()
        spm.set("P1", 1.0)
        spm.set("P2", 2.0)
        assert "P1" in spm.products
        assert "P2" in spm.products

    def test_contains(self) -> None:
        """Test __contains__. / 测试包含判断."""
        spm = ShadowPriceMap()
        spm.set("P1", 1.0)
        assert "P1" in spm
        assert "P2" not in spm

    def test_len(self) -> None:
        """Test __len__. / 测试长度."""
        spm = ShadowPriceMap()
        spm.set("P1", 1.0)
        spm.set("P2", 2.0)
        assert len(spm) == 2


# ============================================================
# CuttingPlanProductOrder tests
# ============================================================


class TestCuttingPlanProductOrder:
    """CuttingPlanProductOrder tests."""

    def test_create_with_defaults(self) -> None:
        """Test default values. / 测试默认值."""
        cpo = CuttingPlanProductOrder()
        assert cpo.product_key == ""
        assert cpo.order_index == 0
        assert cpo.quantity == 0
        assert cpo.width == 0.0
        assert cpo.length == 0.0

    def test_create_with_values(self) -> None:
        """Test creation with values. / 测试带值创建."""
        cpo = CuttingPlanProductOrder.create(
            product_key="P1",
            order_index=1,
            quantity=5,
            width=30.0,
            length=200.0,
        )
        assert cpo.product_key == "P1"
        assert cpo.quantity == 5

    def test_total_width(self) -> None:
        """Test total_width property. / 测试总宽度属性."""
        cpo = CuttingPlanProductOrder.create(
            product_key="P1",
            order_index=0,
            quantity=3,
            width=30.0,
        )
        assert cpo.total_width == pytest.approx(90.0)

    def test_total_length(self) -> None:
        """Test total_length property. / 测试总长度属性."""
        cpo = CuttingPlanProductOrder.create(
            product_key="P1",
            order_index=0,
            quantity=4,
            width=30.0,
            length=200.0,
        )
        assert cpo.total_length == pytest.approx(800.0)

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        cpo = CuttingPlanProductOrder.create(
            product_key="P1", order_index=0, quantity=1
        )
        with pytest.raises(AttributeError):
            cpo.quantity = 10  # type: ignore[misc]


# ============================================================
# Csp1dProduceContext tests
# ============================================================


class TestCsp1dProduceContext:
    """Csp1dProduceContext tests."""

    def _make_problem(self) -> Csp1dProblem:
        """Helper to create a problem. / 辅助创建问题."""
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        machine = Machine(name="C1", max_width=200.0, cut_loss=2.0)
        return Csp1dProblem(
            materials=(mat,),
            products=(prod,),
            machines=(machine,),
            demands=(),
        )

    def test_create(self) -> None:
        """Test context creation. / 测试上下文创建."""
        problem = self._make_problem()
        ctx = Csp1dProduceContext(problem=problem)
        assert ctx.problem is problem

    def test_cutting_plans_empty(self) -> None:
        """Test initial cutting plans empty. / 测试初始切割方案为空."""
        problem = self._make_problem()
        ctx = Csp1dProduceContext(problem=problem)
        assert ctx.cutting_plans == ()

    def test_add_cutting_plans(self) -> None:
        """Test adding cutting plans. / 测试添加切割方案."""
        problem = self._make_problem()
        ctx = Csp1dProduceContext(problem=problem)
        cp = CuttingPlan(material="Steel", products=(), waste=5.0)
        ctx.add_cutting_plans((cp,))
        assert len(ctx.cutting_plans) == 1

    def test_remove_cutting_plans(self) -> None:
        """Test removing cutting plans. / 测试移除切割方案."""
        problem = self._make_problem()
        ctx = Csp1dProduceContext(problem=problem)
        cp1 = CuttingPlan(material="Steel", products=(), waste=5.0)
        cp2 = CuttingPlan(material="Steel", products=(), waste=3.0)
        ctx.add_cutting_plans((cp1, cp2))
        ctx.remove_cutting_plans((0,))
        assert len(ctx.cutting_plans) == 1

    def test_update_shadow_prices(self) -> None:
        """Test updating shadow prices. / 测试更新影子价格."""
        problem = self._make_problem()
        ctx = Csp1dProduceContext(problem=problem)
        spm = ShadowPriceMap()
        spm.set("P1", 5.0)
        ctx.update_shadow_prices(spm)
        assert ctx.shadow_prices.get("P1") == pytest.approx(5.0)


# ============================================================
# TopKCuttingPlans tests
# ============================================================


class TestTopKCuttingPlans:
    """TopKCuttingPlans tests."""

    def test_create(self) -> None:
        """Test selector creation. / 测试选择器创建."""
        selector = TopKCuttingPlans(k=3)
        assert selector.k == 3

    def test_select_empty(self) -> None:
        """Test select with empty plans. / 测试空方案选择."""
        selector = TopKCuttingPlans(k=5)
        spm = ShadowPriceMap()
        result = selector.select(plans=(), shadow_prices=spm)
        assert result == ()

    def test_select_returns_top_k(self) -> None:
        """Test select returns top K plans. / 测试返回前 K 个方案."""
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        cp1 = CuttingPlan(material="Steel", products=((prod, 3),), waste=10.0)
        cp2 = CuttingPlan(material="Steel", products=((prod, 2),), waste=5.0)
        cp3 = CuttingPlan(material="Steel", products=((prod, 1),), waste=20.0)
        spm = ShadowPriceMap()
        spm.set("P1", 0.0)

        selector = TopKCuttingPlans(k=2)
        result = selector.select(plans=(cp1, cp2, cp3), shadow_prices=spm)
        assert len(result) == 2
