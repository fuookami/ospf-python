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
        assert p.product_key == ""
        assert p.quantity == 0

    def test_create_with_values(self) -> None:
        """Test creation with values. / 测试带值创建."""
        p = Production.create(
            product_key="P1",
            material_key="M1",
            machine_key="C1",
            quantity=10,
            length=200.0,
        )
        assert p.product_key == "P1"
        assert p.quantity == 10
        assert p.is_valid

    def test_with_quantity(self) -> None:
        """Test with_quantity. / 测试更新数量."""
        p = Production.create(
            product_key="P1",
            material_key="M1",
            machine_key="C1",
            quantity=5,
        )
        p2 = p.with_quantity(10)
        assert p2.quantity == 10
        assert p.quantity == 5

    def test_total_length(self) -> None:
        """Test total_length property. / 测试总长度属性."""
        p = Production.create(
            product_key="P1",
            material_key="M1",
            machine_key="C1",
            quantity=3,
            length=200.0,
        )
        assert p.total_length == 600.0

    def test_frozen(self) -> None:
        """Test is frozen dataclass. / 测试是冻结数据类."""
        p = Production()
        with pytest.raises(AttributeError):
            p.quantity = 10  # type: ignore[misc]


# ============================================================
# CuttingPlanDemandContribution tests
# ============================================================


class TestCuttingPlanDemandContribution:
    """CuttingPlanDemandContribution tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        cpdc = CuttingPlanDemandContribution()
        assert cpdc is not None

    def test_create_with_contributions(self) -> None:
        """Test create factory with contributions. / 测试带贡献的工厂方法."""
        cpdc = CuttingPlanDemandContribution.create(
            contributions=(("P1", "plan1", 5), ("P2", "plan1", 3)),
        )
        assert cpdc.total_contributed == 8
        assert len(cpdc.contributions) == 2

    def test_create_empty(self) -> None:
        """Test create with no contributions. / 测试无贡献的工厂方法."""
        cpdc = CuttingPlanDemandContribution.create()
        assert cpdc.total_contributed == 0
        assert cpdc.contributions == ()

    def test_add_returns_new_instance(self) -> None:
        """Test add returns a new instance (immutable). / 测试 add 返回新实例."""
        cpdc = CuttingPlanDemandContribution()
        cpdc2 = cpdc.add("P1", "plan1", 4)
        assert cpdc is not cpdc2
        assert cpdc.total_contributed == 0
        assert cpdc2.total_contributed == 4

    def test_add_accumulates_total(self) -> None:
        """Test add accumulates total_contributed. / 测试 add 累加 total_contributed."""
        cpdc = CuttingPlanDemandContribution.create(
            contributions=(("P1", "plan1", 5),),
        )
        cpdc2 = cpdc.add("P2", "plan2", 3)
        assert cpdc2.total_contributed == 8

    def test_contribution_for_product(self) -> None:
        """Test contribution_for_product sums correctly. / 测试产品贡献汇总."""
        cpdc = CuttingPlanDemandContribution.create(
            contributions=(
                ("P1", "plan1", 5),
                ("P1", "plan2", 3),
                ("P2", "plan1", 7),
            ),
        )
        assert cpdc.contribution_for_product("P1") == 8
        assert cpdc.contribution_for_product("P2") == 7
        assert cpdc.contribution_for_product("P3") == 0

    def test_contribution_for_plan(self) -> None:
        """Test contribution_for_plan sums correctly. / 测试方案贡献汇总."""
        cpdc = CuttingPlanDemandContribution.create(
            contributions=(
                ("P1", "plan1", 5),
                ("P2", "plan1", 3),
                ("P1", "plan2", 7),
            ),
        )
        assert cpdc.contribution_for_plan("plan1") == 8
        assert cpdc.contribution_for_plan("plan2") == 7
        assert cpdc.contribution_for_plan("plan3") == 0

    def test_product_keys_deduplicated(self) -> None:
        """Test product_keys returns deduplicated keys. / 测试产品键去重."""
        cpdc = CuttingPlanDemandContribution.create(
            contributions=(
                ("P1", "plan1", 5),
                ("P2", "plan2", 3),
                ("P1", "plan3", 2),
            ),
        )
        keys = cpdc.product_keys()
        assert "P1" in keys
        assert "P2" in keys
        assert len(keys) == 2

    def test_product_keys_preserves_order(self) -> None:
        """Test product_keys preserves insertion order. / 测试产品键保持插入顺序."""
        cpdc = CuttingPlanDemandContribution.create(
            contributions=(
                ("P3", "plan1", 1),
                ("P1", "plan2", 2),
                ("P2", "plan3", 3),
            ),
        )
        keys = cpdc.product_keys()
        assert keys == ("P3", "P1", "P2")

    def test_product_keys_empty(self) -> None:
        """Test product_keys returns empty for no contributions. / 测试无贡献时产品键为空."""
        cpdc = CuttingPlanDemandContribution()
        assert cpdc.product_keys() == ()

    def test_has_contributions(self) -> None:
        """Test has_contributions property. / 测试 has_contributions 属性."""
        empty = CuttingPlanDemandContribution()
        assert empty.has_contributions is False
        with_data = CuttingPlanDemandContribution.create(
            contributions=(("P1", "plan1", 1),),
        )
        assert with_data.has_contributions is True

    def test_unique_products(self) -> None:
        """Test unique_products property. / 测试 unique_products 属性."""
        cpdc = CuttingPlanDemandContribution.create(
            contributions=(
                ("P1", "plan1", 5),
                ("P1", "plan2", 3),
                ("P2", "plan1", 7),
            ),
        )
        assert cpdc.unique_products == 2

    def test_unique_products_empty(self) -> None:
        """Test unique_products is 0 when empty. / 测试空时 unique_products 为 0."""
        cpdc = CuttingPlanDemandContribution()
        assert cpdc.unique_products == 0

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        cpdc = CuttingPlanDemandContribution()
        with pytest.raises(AttributeError):
            cpdc.total_contributed = 10  # type: ignore[misc]


# ============================================================
# DomainValueConversion tests
# ============================================================


class TestDomainValueConversion:
    """DomainValueConversion tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        dvc = DomainValueConversion()
        assert dvc is not None

    def test_from_materials_sorts_by_width(self) -> None:
        """Test from_materials sorts materials by width ascending. / 测试按宽度排序."""
        dvc = DomainValueConversion.from_materials(
            materials=(("wide", 200.0), ("narrow", 50.0), ("mid", 100.0)),
        )
        assert dvc.width_to_index[0] == (50.0, 0)
        assert dvc.width_to_index[1] == (100.0, 1)
        assert dvc.width_to_index[2] == (200.0, 2)
        assert dvc.name_to_width[0] == ("narrow", 50.0)

    def test_from_materials_empty(self) -> None:
        """Test from_materials with no materials. / 测试空材料列表."""
        dvc = DomainValueConversion.from_materials(materials=())
        assert dvc.width_to_index == ()
        assert dvc.name_to_width == ()

    def test_width_of_found(self) -> None:
        """Test width_of returns width for known name. / 测试已知名称返回宽度."""
        dvc = DomainValueConversion.from_materials(
            materials=(("matA", 120.0), ("matB", 80.0)),
        )
        assert dvc.width_of("matA") == pytest.approx(120.0)
        assert dvc.width_of("matB") == pytest.approx(80.0)

    def test_width_of_missing(self) -> None:
        """Test width_of returns None for unknown name. / 测试未知名称返回 None."""
        dvc = DomainValueConversion.from_materials(
            materials=(("matA", 120.0),),
        )
        assert dvc.width_of("unknown") is None

    def test_index_of_width_found(self) -> None:
        """Test index_of_width returns index for known width. / 测试已知宽度返回索引."""
        dvc = DomainValueConversion.from_materials(
            materials=(("wide", 200.0), ("narrow", 50.0)),
        )
        assert dvc.index_of_width(50.0) == 0
        assert dvc.index_of_width(200.0) == 1

    def test_index_of_width_missing(self) -> None:
        """Test index_of_width returns None for unknown width. / 测试未知宽度返回 None."""
        dvc = DomainValueConversion.from_materials(
            materials=(("matA", 100.0),),
        )
        assert dvc.index_of_width(999.0) is None

    def test_name_for_index_found(self) -> None:
        """Test name_for_index returns name for valid index. / 测试有效索引返回名称."""
        dvc = DomainValueConversion.from_materials(
            materials=(("narrow", 50.0), ("wide", 200.0)),
        )
        assert dvc.name_for_index(0) == "narrow"
        assert dvc.name_for_index(1) == "wide"

    def test_name_for_index_out_of_range(self) -> None:
        """Test name_for_index returns None for out-of-range index. / 测试越界索引返回 None."""
        dvc = DomainValueConversion.from_materials(
            materials=(("matA", 100.0),),
        )
        assert dvc.name_for_index(-1) is None
        assert dvc.name_for_index(1) is None

    def test_size(self) -> None:
        """Test size property. / 测试 size 属性."""
        dvc = DomainValueConversion.from_materials(
            materials=(("A", 10.0), ("B", 20.0), ("C", 30.0)),
        )
        assert dvc.size == 3

    def test_is_empty(self) -> None:
        """Test is_empty property. / 测试 is_empty 属性."""
        empty = DomainValueConversion()
        assert empty.is_empty is True
        dvc = DomainValueConversion.from_materials(materials=(("A", 10.0),))
        assert dvc.is_empty is False

    def test_sorted_widths(self) -> None:
        """Test sorted_widths returns ascending widths. / 测试排序后宽度."""
        dvc = DomainValueConversion.from_materials(
            materials=(("C", 300.0), ("A", 100.0), ("B", 200.0)),
        )
        assert dvc.sorted_widths() == (100.0, 200.0, 300.0)

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        dvc = DomainValueConversion()
        with pytest.raises(AttributeError):
            dvc.width_to_index = ()  # type: ignore[misc]


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

    def test_register_material(self) -> None:
        """Test register_material returns new context. / 测试注册材料返回新上下文."""
        ctx = MaterialContext()
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        ctx2 = ctx.register_material(mat)
        assert ctx is not ctx2
        assert ctx.material_count == 0
        assert ctx2.material_count == 1
        assert ctx2.materials[0].name == "Steel"

    def test_register_product(self) -> None:
        """Test register_product returns new context. / 测试注册产品返回新上下文."""
        ctx = MaterialContext()
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        ctx2 = ctx.register_product(prod)
        assert ctx.product_count == 0
        assert ctx2.product_count == 1
        assert ctx2.products[0].name == "P1"

    def test_register_machine(self) -> None:
        """Test register_machine returns new context. / 测试注册机器返回新上下文."""
        ctx = MaterialContext()
        mch = Machine(name="C1", max_width=200.0, cut_loss=2.0)
        ctx2 = ctx.register_machine(mch)
        assert ctx.machine_count == 0
        assert ctx2.machine_count == 1
        assert ctx2.machines[0].name == "C1"

    def test_select_material(self) -> None:
        """Test select_material updates current_material. / 测试选择材料更新当前材料."""
        ctx = MaterialContext()
        ctx2 = ctx.select_material("Aluminum")
        assert ctx.current_material == ""
        assert ctx2.current_material == "Aluminum"

    def test_get_material_found(self) -> None:
        """Test get_material returns material by name. / 测试按名称获取材料."""
        mat1 = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        mat2 = Material(name="Aluminum", width=80.0, length=500.0, cost=40.0)
        ctx = MaterialContext(materials=(mat1, mat2))
        result = ctx.get_material("Steel")
        assert result is not None
        assert result.name == "Steel"
        assert result.width == pytest.approx(100.0)

    def test_get_material_not_found(self) -> None:
        """Test get_material returns None for unknown name. / 测试未知名称返回 None."""
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        ctx = MaterialContext(materials=(mat,))
        assert ctx.get_material("Gold") is None

    def test_get_product_found(self) -> None:
        """Test get_product returns product by name. / 测试按名称获取产品."""
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        ctx = MaterialContext(products=(prod,))
        result = ctx.get_product("P1")
        assert result is not None
        assert result.demand == 10

    def test_get_product_not_found(self) -> None:
        """Test get_product returns None for unknown name. / 测试未知名称返回 None."""
        ctx = MaterialContext()
        assert ctx.get_product("missing") is None

    def test_get_machine_found(self) -> None:
        """Test get_machine returns machine by name. / 测试按名称获取机器."""
        mch = Machine(name="C1", max_width=200.0, cut_loss=2.0)
        ctx = MaterialContext(machines=(mch,))
        result = ctx.get_machine("C1")
        assert result is not None
        assert result.max_width == pytest.approx(200.0)

    def test_get_machine_not_found(self) -> None:
        """Test get_machine returns None for unknown name. / 测试未知名称返回 None."""
        ctx = MaterialContext()
        assert ctx.get_machine("missing") is None

    def test_contains_material(self) -> None:
        """Test contains_material. / 测试 contains_material."""
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        ctx = MaterialContext(materials=(mat,))
        assert ctx.contains_material("Steel") is True
        assert ctx.contains_material("Gold") is False

    def test_contains_product(self) -> None:
        """Test contains_product. / 测试 contains_product."""
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        ctx = MaterialContext(products=(prod,))
        assert ctx.contains_product("P1") is True
        assert ctx.contains_product("P2") is False

    def test_material_count(self) -> None:
        """Test material_count property. / 测试 material_count 属性."""
        mat1 = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        mat2 = Material(name="Aluminum", width=80.0, length=500.0, cost=40.0)
        ctx = MaterialContext(materials=(mat1, mat2))
        assert ctx.material_count == 2

    def test_product_count(self) -> None:
        """Test product_count property. / 测试 product_count 属性."""
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        ctx = MaterialContext(products=(prod,))
        assert ctx.product_count == 1

    def test_machine_count(self) -> None:
        """Test machine_count property. / 测试 machine_count 属性."""
        mch = Machine(name="C1", max_width=200.0, cut_loss=2.0)
        ctx = MaterialContext(machines=(mch,))
        assert ctx.machine_count == 1

    def test_is_empty(self) -> None:
        """Test is_empty property. / 测试 is_empty 属性."""
        empty = MaterialContext()
        assert empty.is_empty is True
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        non_empty = MaterialContext(materials=(mat,))
        assert non_empty.is_empty is False

    def test_register_preserves_other_registries(self) -> None:
        """Test registering one type preserves others. / 测试注册一种类型保留其他类型."""
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        mch = Machine(name="C1", max_width=200.0, cut_loss=2.0)
        ctx = MaterialContext(materials=(mat,), products=(prod,), machines=(mch,))
        ctx2 = ctx.register_material(
            Material(name="Aluminum", width=80.0, length=500.0, cost=40.0),
        )
        assert len(ctx2.materials) == 2
        assert len(ctx2.products) == 1
        assert len(ctx2.machines) == 1
        assert ctx2.current_material == ctx.current_material

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        ctx = MaterialContext()
        with pytest.raises(AttributeError):
            ctx.current_material = "test"  # type: ignore[misc]


# ============================================================
# Aggregation tests
# ============================================================


class TestAggregation:
    """Aggregation tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        agg = Aggregation()
        assert agg is not None

    def test_create_factory(self) -> None:
        """Test create static factory. / 测试 create 工厂方法."""
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        mch = Machine(name="C1", max_width=200.0, cut_loss=2.0)
        agg = Aggregation.create(
            materials=(mat,), products=(prod,), machines=(mch,),
        )
        assert agg.material_count == 1
        assert agg.product_count == 1
        assert agg.machine_count == 1

    def test_create_factory_empty(self) -> None:
        """Test create with defaults. / 测试默认创建."""
        agg = Aggregation.create()
        assert agg.is_empty is True

    def test_with_materials(self) -> None:
        """Test with_materials returns new instance. / 测试 with_materials 返回新实例."""
        agg = Aggregation()
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        agg2 = agg.with_materials(materials=(mat,))
        assert agg is not agg2
        assert agg.material_count == 0
        assert agg2.material_count == 1

    def test_with_products(self) -> None:
        """Test with_products returns new instance. / 测试 with_products 返回新实例."""
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        agg = Aggregation()
        agg2 = agg.with_products(products=(prod,))
        assert agg.product_count == 0
        assert agg2.product_count == 1

    def test_with_machines(self) -> None:
        """Test with_machines returns new instance. / 测试 with_machines 返回新实例."""
        mch = Machine(name="C1", max_width=200.0, cut_loss=2.0)
        agg = Aggregation()
        agg2 = agg.with_machines(machines=(mch,))
        assert agg.machine_count == 0
        assert agg2.machine_count == 1

    def test_get_material_found(self) -> None:
        """Test get_material by name. / 测试按名称获取材料."""
        mat1 = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        mat2 = Material(name="Aluminum", width=80.0, length=500.0, cost=40.0)
        agg = Aggregation(materials=(mat1, mat2))
        result = agg.get_material("Steel")
        assert result is not None
        assert result.name == "Steel"

    def test_get_material_not_found(self) -> None:
        """Test get_material returns None for unknown. / 测试未知材料返回 None."""
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        agg = Aggregation(materials=(mat,))
        assert agg.get_material("Gold") is None

    def test_get_product_found(self) -> None:
        """Test get_product by name. / 测试按名称获取产品."""
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        agg = Aggregation(products=(prod,))
        result = agg.get_product("P1")
        assert result is not None
        assert result.demand == 10

    def test_get_product_not_found(self) -> None:
        """Test get_product returns None for unknown. / 测试未知产品返回 None."""
        agg = Aggregation()
        assert agg.get_product("missing") is None

    def test_get_machine_found(self) -> None:
        """Test get_machine by name. / 测试按名称获取机器."""
        mch = Machine(name="C1", max_width=200.0, cut_loss=2.0)
        agg = Aggregation(machines=(mch,))
        result = agg.get_machine("C1")
        assert result is not None
        assert result.max_width == pytest.approx(200.0)

    def test_get_machine_not_found(self) -> None:
        """Test get_machine returns None for unknown. / 测试未知机器返回 None."""
        agg = Aggregation()
        assert agg.get_machine("missing") is None

    def test_material_count(self) -> None:
        """Test material_count property. / 测试 material_count 属性."""
        mat1 = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        mat2 = Material(name="Aluminum", width=80.0, length=500.0, cost=40.0)
        agg = Aggregation(materials=(mat1, mat2))
        assert agg.material_count == 2

    def test_product_count(self) -> None:
        """Test product_count property. / 测试 product_count 属性."""
        prod1 = Product(name="P1", width=30.0, length=200.0, demand=10)
        prod2 = Product(name="P2", width=25.0, length=150.0, demand=5)
        agg = Aggregation(products=(prod1, prod2))
        assert agg.product_count == 2

    def test_machine_count(self) -> None:
        """Test machine_count property. / 测试 machine_count 属性."""
        mch = Machine(name="C1", max_width=200.0, cut_loss=2.0)
        agg = Aggregation(machines=(mch,))
        assert agg.machine_count == 1

    def test_total_demand(self) -> None:
        """Test total_demand sums product demands. / 测试 total_demand 汇总需求."""
        prod1 = Product(name="P1", width=30.0, length=200.0, demand=10)
        prod2 = Product(name="P2", width=25.0, length=150.0, demand=5)
        prod3 = Product(name="P3", width=20.0, length=100.0, demand=8)
        agg = Aggregation(products=(prod1, prod2, prod3))
        assert agg.total_demand == 23

    def test_total_demand_empty(self) -> None:
        """Test total_demand is 0 when no products. / 测试无产品时 total_demand 为 0."""
        agg = Aggregation()
        assert agg.total_demand == 0

    def test_is_empty(self) -> None:
        """Test is_empty property. / 测试 is_empty 属性."""
        empty = Aggregation()
        assert empty.is_empty is True
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        non_empty = Aggregation(materials=(mat,))
        assert non_empty.is_empty is False

    def test_with_materials_preserves_others(self) -> None:
        """Test with_materials preserves products and machines. / 测试 with_materials 保留产品和机器."""
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        mch = Machine(name="C1", max_width=200.0, cut_loss=2.0)
        agg = Aggregation(products=(prod,), machines=(mch,))
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        agg2 = agg.with_materials(materials=(mat,))
        assert agg2.products == (prod,)
        assert agg2.machines == (mch,)

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        agg = Aggregation()
        with pytest.raises(AttributeError):
            agg.materials = ()  # type: ignore[misc]


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

    def test_map_material(self) -> None:
        """Test map_material produces correct dict. / 测试 map_material 生成正确字典."""
        rm = RenderMappers(precision=2)
        mat = Material(name="Steel", width=100.0, length=600.0, cost=50.0)
        result = rm.map_material(mat)
        assert result["name"] == "Steel"
        assert result["label"] == "Steel"
        assert result["width"] == pytest.approx(100.0)
        assert result["length"] == pytest.approx(600.0)
        assert result["cost"] == pytest.approx(50.0)

    def test_map_material_with_custom_label(self) -> None:
        """Test map_material with custom label. / 测试带自定义标签的材料映射."""
        rm = RenderMappers(
            material_labels=(("Steel", "Steel Plate"),),
            precision=3,
        )
        mat = Material(name="Steel", width=100.333, length=600.777, cost=50.111)
        result = rm.map_material(mat)
        assert result["label"] == "Steel Plate"
        assert result["width"] == pytest.approx(100.333, abs=0.001)
        assert result["length"] == pytest.approx(600.777, abs=0.001)

    def test_map_product(self) -> None:
        """Test map_product produces correct dict. / 测试 map_product 生成正确字典."""
        rm = RenderMappers(precision=2)
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        result = rm.map_product(prod)
        assert result["name"] == "P1"
        assert result["label"] == "P1"
        assert result["width"] == pytest.approx(30.0)
        assert result["length"] == pytest.approx(200.0)
        assert result["demand"] == 10

    def test_map_product_with_custom_label(self) -> None:
        """Test map_product with custom label. / 测试带自定义标签的产品映射."""
        rm = RenderMappers(
            product_labels=(("P1", "Panel Type A"),),
            precision=1,
        )
        prod = Product(name="P1", width=30.25, length=200.75, demand=5)
        result = rm.map_product(prod)
        assert result["label"] == "Panel Type A"
        assert result["width"] == pytest.approx(30.2, abs=0.1)

    def test_map_cutting_plan(self) -> None:
        """Test map_cutting_plan produces correct dict. / 测试 map_cutting_plan 生成正确字典."""
        rm = RenderMappers(precision=2)
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        plan = CuttingPlan(material="Steel", products=((prod, 3),), waste=5.0)
        result = rm.map_cutting_plan(plan)
        assert result["material"] == "Steel"
        assert result["material_label"] == "Steel"
        assert result["waste"] == pytest.approx(5.0)
        assert len(result["products"]) == 1
        assert result["products"][0]["name"] == "P1"
        assert result["products"][0]["quantity"] == 3

    def test_map_cutting_plan_with_labels(self) -> None:
        """Test map_cutting_plan with custom labels. / 测试带标签的切割方案映射."""
        rm = RenderMappers(
            material_labels=(("Steel", "Steel Plate"),),
            product_labels=(("P1", "Panel A"),),
            precision=1,
        )
        prod = Product(name="P1", width=30.0, length=200.0, demand=10)
        plan = CuttingPlan(material="Steel", products=((prod, 2),), waste=3.5)
        result = rm.map_cutting_plan(plan)
        assert result["material_label"] == "Steel Plate"
        assert result["products"][0]["label"] == "Panel A"

    def test_map_cutting_plan_multiple_products(self) -> None:
        """Test map_cutting_plan with multiple products. / 测试多产品切割方案映射."""
        rm = RenderMappers()
        p1 = Product(name="P1", width=30.0, length=200.0, demand=10)
        p2 = Product(name="P2", width=20.0, length=150.0, demand=5)
        plan = CuttingPlan(material="Steel", products=((p1, 2), (p2, 3)), waste=5.0)
        result = rm.map_cutting_plan(plan)
        assert len(result["products"]) == 2

    def test_get_material_label_found(self) -> None:
        """Test get_material_label returns custom label. / 测试自定义材料标签."""
        rm = RenderMappers(material_labels=(("Steel", "Steel Plate"),))
        assert rm.get_material_label("Steel") == "Steel Plate"

    def test_get_material_label_fallback(self) -> None:
        """Test get_material_label returns name when no custom label. / 测试无自定义标签时返回名称."""
        rm = RenderMappers()
        assert rm.get_material_label("Steel") == "Steel"

    def test_get_product_label_found(self) -> None:
        """Test get_product_label returns custom label. / 测试自定义产品标签."""
        rm = RenderMappers(product_labels=(("P1", "Panel A"),))
        assert rm.get_product_label("P1") == "Panel A"

    def test_get_product_label_fallback(self) -> None:
        """Test get_product_label returns name when no custom label. / 测试无自定义标签时返回名称."""
        rm = RenderMappers()
        assert rm.get_product_label("P1") == "P1"

    def test_with_material_labels(self) -> None:
        """Test with_material_labels returns new instance. / 测试 with_material_labels 返回新实例."""
        rm = RenderMappers(precision=3)
        labels = (("Steel", "Steel Plate"), ("Aluminum", "Alu Sheet"))
        rm2 = rm.with_material_labels(labels=labels)
        assert rm is not rm2
        assert rm.material_labels == ()
        assert rm2.material_labels == labels
        assert rm2.precision == 3

    def test_with_product_labels(self) -> None:
        """Test with_product_labels returns new instance. / 测试 with_product_labels 返回新实例."""
        rm = RenderMappers(precision=2)
        labels = (("P1", "Panel A"),)
        rm2 = rm.with_product_labels(labels=labels)
        assert rm.product_labels == ()
        assert rm2.product_labels == labels
        assert rm2.precision == 2

    def test_with_precision(self) -> None:
        """Test with_precision returns new instance. / 测试 with_precision 返回新实例."""
        rm = RenderMappers(precision=2)
        rm2 = rm.with_precision(precision=4)
        assert rm.precision == 2
        assert rm2.precision == 4

    def test_precision_affects_rounding(self) -> None:
        """Test precision affects rounding in map_material. / 测试精度影响舍入."""
        rm0 = RenderMappers(precision=0)
        mat = Material(name="Steel", width=100.555, length=600.777, cost=50.333)
        result0 = rm0.map_material(mat)
        assert result0["width"] == pytest.approx(101.0, abs=1.0)

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        rm = RenderMappers()
        with pytest.raises(AttributeError):
            rm.precision = 5  # type: ignore[misc]


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
