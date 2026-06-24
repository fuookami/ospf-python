"""BPP3D domain and infrastructure model tests.

覆盖 BPP3D 领域模型和基础设施层中 0% 覆盖率的文件。
Covers 0%-coverage files in BPP3D domain and infrastructure layers.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pytest

from ospf_python.framework.bpp3d.domain.item.aggregation import (
    Aggregation,
)
from ospf_python.framework.bpp3d.domain.item.error.bpp3d_errors import (
    Bpp3dErrors,
)
from ospf_python.framework.bpp3d.domain.item.item_context import (
    ItemContext,
)
from ospf_python.framework.bpp3d.domain.item.model.bin import Bin
from ospf_python.framework.bpp3d.domain.item.model.block import Block
from ospf_python.framework.bpp3d.domain.item.model.continuous_radius_model_component import (
    ContinuousRadiusModelComponent,
)
from ospf_python.framework.bpp3d.domain.item.model.continuous_radius_selection_extractor import (
    ContinuousRadiusSelectionExtractor,
)
from ospf_python.framework.bpp3d.domain.item.model.cylinder_shape_contract import (
    CylinderShapeContract,
)
from ospf_python.framework.bpp3d.domain.item.model.demand_reduced_cost import (
    DemandReducedCost,
)
from ospf_python.framework.bpp3d.domain.item.model.demand_statistics import (
    DemandStatistics,
)
from ospf_python.framework.bpp3d.domain.item.model.item import Item
from ospf_python.framework.bpp3d.domain.item.model.item_container import (
    ItemContainer,
)
from ospf_python.framework.bpp3d.domain.item.model.layer import Layer
from ospf_python.framework.bpp3d.domain.item.model.material import Material
from ospf_python.framework.bpp3d.domain.item.model.package_ import Package
from ospf_python.framework.bpp3d.domain.item.model.package_attribute import (
    PackageAttribute,
)
from ospf_python.framework.bpp3d.domain.item.model.pattern import Pattern
from ospf_python.framework.bpp3d.domain.item.model.placement_factory import (
    PlacementFactory,
)
from ospf_python.framework.bpp3d.domain.item.model.placement_typing import (
    PlacementTyping,
)
from ospf_python.framework.bpp3d.domain.item.model.quantity_demand_reduced_cost import (
    QuantityDemandReducedCost,
)
from ospf_python.framework.bpp3d.domain.item.model.quantity_demand_statistics import (
    QuantityDemandStatistics,
)
from ospf_python.framework.bpp3d.domain.item.model.quantity_domain_models import (
    QuantityDomainModels,
)
from ospf_python.framework.bpp3d.domain.item.model.schema import Schema
from ospf_python.framework.bpp3d.domain.item.model.shadow_price_map import (
    ItemShadowPriceMap,
)
from ospf_python.framework.bpp3d.infrastructure.conservative_radius_envelope import (
    ConservativeRadiusEnvelope,
)
from ospf_python.framework.bpp3d.infrastructure.container import Container
from ospf_python.framework.bpp3d.infrastructure.cuboid import Cuboid
from ospf_python.framework.bpp3d.infrastructure.cylinder import Cylinder
from ospf_python.framework.bpp3d.infrastructure.horizontal_cylinder_support_coverage import (
    HorizontalCylinderSupportCoverage,
)
from ospf_python.framework.bpp3d.infrastructure.orientation import (
    Orientation,
)
from ospf_python.framework.bpp3d.infrastructure.orientation_axis_permutation_mapping import (
    OrientationAxisPermutationMapping,
)
from ospf_python.framework.bpp3d.infrastructure.package_type import (
    PackageType,
)
from ospf_python.framework.bpp3d.infrastructure.packing_shape import (
    PackingShape,
)
from ospf_python.framework.bpp3d.infrastructure.placement import Placement
from ospf_python.framework.bpp3d.infrastructure.projection import Projection
from ospf_python.framework.bpp3d.infrastructure.projective_plane_geometry_mapping import (
    ProjectivePlaneGeometryMapping,
)
from ospf_python.framework.bpp3d.infrastructure.pwl_radius_approximation_config import (
    PwlRadiusApproximationConfig,
)
from ospf_python.framework.bpp3d.infrastructure.quantity_container_core import (
    QuantityContainerCore,
)
from ospf_python.framework.bpp3d.infrastructure.quantity_geometry_core import (
    QuantityGeometryCore,
)
from ospf_python.framework.bpp3d.infrastructure.semantic_parameter import (
    SemanticParameter,
)
from ospf_python.framework.bpp3d.infrastructure.shadow_price_map import (
    ShadowPriceMap,
)

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.domain.layer_assignment.model.layer_assignment_aliases import (
        ContainerId,
        LayerId,
        LayerIndex,
        Quantity,
    )

# ============================================================
# Item model tests
# ============================================================


class TestItem:
    """Item dataclass tests / Item 数据类测试."""

    def test_create_with_defaults(self) -> None:
        """Test default quantity. / 测试默认数量."""
        item = Item.create(item_key="box1", width=10.0, height=5.0, depth=3.0)
        assert item.quantity == 1

    def test_volume(self) -> None:
        """Test volume property. / 测试体积属性."""
        item = Item.create(item_key="box1", width=2.0, height=3.0, depth=4.0)
        assert item.volume == pytest.approx(24.0)

    def test_total_volume(self) -> None:
        """Test total volume with quantity. / 测试带数量的总体积."""
        item = Item.create(
            item_key="box1",
            width=2.0,
            height=3.0,
            depth=4.0,
            quantity=5,
        )
        assert item.total_volume == pytest.approx(120.0)

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        item = Item.create(item_key="box1", width=1.0, height=1.0, depth=1.0)
        with pytest.raises(AttributeError):
            item.width = 2.0  # type: ignore[misc]


# ============================================================
# Bin model tests
# ============================================================


class TestBin:
    """Bin dataclass tests / Bin 数据类测试."""

    def test_create(self) -> None:
        """Test bin creation. / 测试箱子创建."""
        container = Container.create(width=10.0, height=10.0, depth=10.0)
        bin_ = Bin.create(bin_id="bin-1", container=container)
        assert bin_.bin_id == "bin-1"

    def test_volume(self) -> None:
        """Test bin volume delegates to container. / 测试箱子体积委托."""
        container = Container.create(width=2.0, height=3.0, depth=4.0)
        bin_ = Bin.create(bin_id="bin-1", container=container)
        assert bin_.volume == pytest.approx(24.0)


# ============================================================
# Block model tests
# ============================================================


class TestBlock:
    """Block dataclass tests / Block 数据类测试."""

    def test_create_with_defaults(self) -> None:
        """Test default count. / 测试默认数量."""
        block = Block.create(block_id="b1", item_key="item1")
        assert block.count == 1

    def test_create_with_count(self) -> None:
        """Test custom count. / 测试自定义数量."""
        block = Block.create(block_id="b1", item_key="item1", count=10)
        assert block.count == 10


# ============================================================
# Layer model tests
# ============================================================


class TestLayer:
    """Layer dataclass tests / Layer 数据类测试."""

    def test_create_with_defaults(self) -> None:
        """Test default item_keys. / 测试默认物品键."""
        layer = Layer.create(layer_id="l1", height=5.0)
        assert layer.item_keys == ()

    def test_item_count(self) -> None:
        """Test item_count property. / 测试物品数量属性."""
        layer = Layer.create(
            layer_id="l1",
            height=5.0,
            item_keys=("a", "b", "c"),
        )
        assert layer.item_count == 3


# ============================================================
# Material model tests
# ============================================================


class TestMaterial:
    """Material dataclass tests / Material 数据类测试."""

    def test_create_with_defaults(self) -> None:
        """Test default density. / 测试默认密度."""
        mat = Material.create(material_id="m1", name="Steel")
        assert mat.density == 0.0

    def test_create_with_density(self) -> None:
        """Test custom density. / 测试自定义密度."""
        mat = Material.create(material_id="m1", name="Steel", density=7.85)
        assert mat.density == pytest.approx(7.85)


# ============================================================
# Package model tests
# ============================================================


class TestPackage:
    """Package dataclass tests / Package 数据类测试."""

    def test_create(self) -> None:
        """Test package creation. / 测试包裹创建."""
        pt = PackageType.create(name="small", width=1.0, height=1.0, depth=1.0)
        pkg = Package.create(
            package_id="pkg1",
            package_type=pt,
            item_keys=("item1",),
        )
        assert pkg.package_id == "pkg1"

    def test_volume(self) -> None:
        """Test package volume. / 测试包裹体积."""
        pt = PackageType.create(name="small", width=2.0, height=3.0, depth=4.0)
        pkg = Package.create(package_id="pkg1", package_type=pt)
        assert pkg.volume == pytest.approx(24.0)


# ============================================================
# PackageType model tests
# ============================================================


class TestPackageType:
    """PackageType dataclass tests / PackageType 数据类测试."""

    def test_create(self) -> None:
        """Test package type creation. / 测试包裹类型创建."""
        pt = PackageType.create(name="box", width=10.0, height=5.0, depth=3.0)
        assert pt.name == "box"

    def test_volume(self) -> None:
        """Test volume property. / 测试体积属性."""
        pt = PackageType.create(name="box", width=2.0, height=3.0, depth=4.0)
        assert pt.volume == pytest.approx(24.0)


# ============================================================
# Pattern model tests
# ============================================================


class TestPattern:
    """Pattern dataclass tests / Pattern 数据类测试."""

    def test_create_with_defaults(self) -> None:
        """Test default efficiency. / 测试默认效率."""
        pattern = Pattern.create(pattern_id="p1")
        assert pattern.efficiency == 0.0
        assert pattern.item_count == 0

    def test_item_count(self) -> None:
        """Test item_count property. / 测试物品数量属性."""
        pattern = Pattern.create(
            pattern_id="p1",
            item_keys=("a", "b"),
            efficiency=0.95,
        )
        assert pattern.item_count == 2


# ============================================================
# Container infrastructure tests
# ============================================================


class TestContainer:
    """Container dataclass tests / Container 数据类测试."""

    def test_create(self) -> None:
        """Test container creation. / 测试容器创建."""
        c = Container.create(width=10.0, height=20.0, depth=30.0)
        assert c.width == 10.0

    def test_volume(self) -> None:
        """Test volume property. / 测试体积属性."""
        c = Container.create(width=2.0, height=3.0, depth=4.0)
        assert c.volume == pytest.approx(24.0)


# ============================================================
# Cuboid infrastructure tests
# ============================================================


class TestCuboid:
    """Cuboid dataclass tests / Cuboid 数据类测试."""

    def test_create(self) -> None:
        """Test cuboid creation. / 测试长方体创建."""
        c = Cuboid.create(width=1.0, height=2.0, depth=3.0)
        assert c.depth == 3.0

    def test_volume(self) -> None:
        """Test volume property. / 测试体积属性."""
        c = Cuboid.create(width=2.0, height=3.0, depth=4.0)
        assert c.volume == pytest.approx(24.0)


# ============================================================
# Cylinder infrastructure tests
# ============================================================


class TestCylinder:
    """Cylinder dataclass tests / Cylinder 数据类测试."""

    def test_create(self) -> None:
        """Test cylinder creation. / 测试圆柱体创建."""
        c = Cylinder.create(radius=5.0, height=10.0)
        assert c.radius == 5.0

    def test_diameter(self) -> None:
        """Test diameter property. / 测试直径属性."""
        c = Cylinder.create(radius=3.0, height=10.0)
        assert c.diameter == pytest.approx(6.0)

    def test_volume(self) -> None:
        """Test volume property. / 测试体积属性."""
        c = Cylinder.create(radius=2.0, height=5.0)
        expected = math.pi * 4.0 * 5.0
        assert c.volume == pytest.approx(expected)


# ============================================================
# Placement infrastructure tests
# ============================================================


class TestPlacement:
    """Placement dataclass tests / Placement 数据类测试."""

    def test_create_with_defaults(self) -> None:
        """Test default orientation. / 测试默认方向."""
        p = Placement.create(x=1.0, y=2.0, z=3.0)
        assert p.orientation == Orientation.XYZ

    def test_create_with_orientation(self) -> None:
        """Test custom orientation. / 测试自定义方向."""
        p = Placement.create(
            x=0.0,
            y=0.0,
            z=0.0,
            orientation=Orientation.ZYX,
        )
        assert p.orientation == Orientation.ZYX


# ============================================================
# Orientation enum tests
# ============================================================


class TestOrientation:
    """Orientation enum tests / Orientation 枚举测试."""

    def test_all_values(self) -> None:
        """Test all six orientations exist. / 测试六种方向存在."""
        assert len(Orientation) == 6
        assert Orientation.XYZ.value == "xyz"
        assert Orientation.ZYX.value == "zyx"


# ============================================================
# PackingShape enum tests
# ============================================================


class TestPackingShape:
    """PackingShape enum tests / PackingShape 枚举测试."""

    def test_values(self) -> None:
        """Test enum values. / 测试枚举值."""
        assert PackingShape.CUBOID.value == "cuboid"
        assert PackingShape.CYLINDER.value == "cylinder"


# ============================================================
# PlacementTyping enum tests
# ============================================================


class TestPlacementTyping:
    """PlacementTyping enum tests / PlacementTyping 枚举测试."""

    def test_values(self) -> None:
        """Test enum values. / 测试枚举值."""
        assert PlacementTyping.FIXED.value == "fixed"
        assert PlacementTyping.FREE.value == "free"
        assert PlacementTyping.CONSTRAINED.value == "constrained"


# ============================================================
# Bpp3dErrors enum tests
# ============================================================


class TestBpp3dErrors:
    """Bpp3dErrors enum tests / Bpp3dErrors 枚举测试."""

    def test_values(self) -> None:
        """Test error code values. / 测试错误码值."""
        assert Bpp3dErrors.ITEM_NOT_FOUND.value == "item_not_found"
        assert Bpp3dErrors.CONTAINER_FULL.value == "container_full"
        assert Bpp3dErrors.NO_FEASIBLE_SOLUTION.value == ("no_feasible_solution")


# ============================================================
# Projection infrastructure tests
# ============================================================


class TestProjection:
    """Projection dataclass tests / Projection 数据类测试."""

    def test_create(self) -> None:
        """Test projection creation. / 测试投影创建."""
        p = Projection.create(width=10.0, height=20.0)
        assert p.width == 10.0

    def test_area(self) -> None:
        """Test area property. / 测试面积属性."""
        p = Projection.create(width=3.0, height=4.0)
        assert p.area == pytest.approx(12.0)


# ============================================================
# DemandStatistics model tests
# ============================================================


class TestDemandStatistics:
    """DemandStatistics tests / DemandStatistics 测试."""

    def test_create_with_defaults(self) -> None:
        """Test default fulfilled_demand. / 测试默认已满足需求."""
        ds = DemandStatistics.create(item_key="item1", total_demand=100)
        assert ds.fulfilled_demand == 0

    def test_remaining_demand(self) -> None:
        """Test remaining_demand property. / 测试剩余需求属性."""
        ds = DemandStatistics.create(
            item_key="item1",
            total_demand=100,
            fulfilled_demand=60,
        )
        assert ds.remaining_demand == 40

    def test_fulfillment_ratio(self) -> None:
        """Test fulfillment_ratio property. / 测试满足率属性."""
        ds = DemandStatistics.create(
            item_key="item1",
            total_demand=100,
            fulfilled_demand=75,
        )
        assert ds.fulfillment_ratio == pytest.approx(0.75)

    def test_fulfillment_ratio_zero_demand(self) -> None:
        """Test ratio with zero demand. / 测试零需求时的比率."""
        ds = DemandStatistics.create(item_key="item1", total_demand=0)
        assert ds.fulfillment_ratio == pytest.approx(0.0)


# ============================================================
# DemandReducedCost model tests
# ============================================================


class TestDemandReducedCost:
    """DemandReducedCost tests / DemandReducedCost 测试."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        drc = DemandReducedCost.create(item_key="item1", reduced_cost=-1.5)
        assert drc.reduced_cost == pytest.approx(-1.5)


# ============================================================
# QuantityDemandStatistics model tests
# ============================================================


class TestQuantityDemandStatistics:
    """QuantityDemandStatistics tests."""

    def test_remaining_quantity(self) -> None:
        """Test remaining quantity. / 测试剩余数量."""
        qds = QuantityDemandStatistics.create(
            item_key="item1",
            total_quantity=50,
            packed_quantity=30,
        )
        assert qds.remaining_quantity == 20

    def test_packing_ratio(self) -> None:
        """Test packing ratio. / 测试装箱率."""
        qds = QuantityDemandStatistics.create(
            item_key="item1",
            total_quantity=100,
            packed_quantity=80,
        )
        assert qds.packing_ratio == pytest.approx(0.8)

    def test_packing_ratio_zero(self) -> None:
        """Test packing ratio with zero total. / 测试零总量装箱率."""
        qds = QuantityDemandStatistics.create(item_key="item1", total_quantity=0)
        assert qds.packing_ratio == pytest.approx(0.0)


# ============================================================
# QuantityDemandReducedCost model tests
# ============================================================


class TestQuantityDemandReducedCost:
    """QuantityDemandReducedCost tests."""

    def test_total_reduced_cost(self) -> None:
        """Test total reduced cost. / 测试总缩减成本."""
        qdrc = QuantityDemandReducedCost.create(
            item_key="item1", quantity=10, reduced_cost=2.5
        )
        assert qdrc.total_reduced_cost == pytest.approx(25.0)


# ============================================================
# QuantityDomainModels tests
# ============================================================


class TestQuantityDomainModels:
    """QuantityDomainModels tests."""

    def test_create_with_defaults(self) -> None:
        """Test default values. / 测试默认值."""
        qdm = QuantityDomainModels.create(model_id="m1")
        assert qdm.item_count == 0
        assert qdm.total_quantity == 0


# ============================================================
# Schema model tests
# ============================================================


class TestSchema:
    """Schema dataclass tests / Schema 数据类测试."""

    def test_create_with_defaults(self) -> None:
        """Test default total_items. / 测试默认总物品数."""
        s = Schema.create(schema_id="s1", bin_count=5)
        assert s.total_items == 0

    def test_average_items_per_bin(self) -> None:
        """Test average items per bin. / 测试每箱平均物品数."""
        s = Schema.create(schema_id="s1", bin_count=4, total_items=20)
        assert s.average_items_per_bin == pytest.approx(5.0)

    def test_average_items_per_bin_zero(self) -> None:
        """Test average with zero bins. / 测试零箱子时的平均数."""
        s = Schema.create(schema_id="s1", bin_count=0)
        assert s.average_items_per_bin == pytest.approx(0.0)


# ============================================================
# ItemShadowPriceMap tests
# ============================================================


class TestItemShadowPriceMap:
    """ItemShadowPriceMap tests."""

    def test_create_and_get(self) -> None:
        """Test create and get_price. / 测试创建和获取价格."""
        spm = ItemShadowPriceMap.create(prices=(("item1", 1.5), ("item2", 2.0)))
        assert spm.get_price("item1") == pytest.approx(1.5)
        assert spm.get_price("item2") == pytest.approx(2.0)

    def test_get_price_missing(self) -> None:
        """Test missing key returns 0. / 测试缺失键返回 0."""
        spm = ItemShadowPriceMap.create(prices=())
        assert spm.get_price("missing") == pytest.approx(0.0)

    def test_item_count(self) -> None:
        """Test item_count property. / 测试物品数量属性."""
        spm = ItemShadowPriceMap.create(prices=(("a", 1.0), ("b", 2.0), ("c", 3.0)))
        assert spm.item_count == 3


# ============================================================
# PackageAttribute tests
# ============================================================


class TestPackageAttribute:
    """PackageAttribute tests."""

    def test_create_with_defaults(self) -> None:
        """Test default attribute_value. / 测试默认属性值."""
        pa = PackageAttribute.create(package_id="pkg1", attribute_name="color")
        assert pa.attribute_value == ""


# ============================================================
# ItemContainer tests
# ============================================================


class TestItemContainer:
    """ItemContainer tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        item = Item.create(item_key="i1", width=1.0, height=1.0, depth=1.0)
        ic = ItemContainer.create(item=item, container_key="c1")
        assert ic.container_key == "c1"


# ============================================================
# PlacementFactory tests
# ============================================================


class TestPlacementFactory:
    """PlacementFactory tests."""

    def test_create(self) -> None:
        """Test factory creation. / 测试工厂创建."""
        pf = PlacementFactory.create(
            container_width=10.0,
            container_height=20.0,
            container_depth=30.0,
        )
        assert pf.container_width == 10.0

    def test_create_origin_placement(self) -> None:
        """Test origin placement creation. / 测试原点放置创建."""
        pf = PlacementFactory.create(
            container_width=10.0,
            container_height=20.0,
            container_depth=30.0,
        )
        p = pf.create_origin_placement()
        assert p.x == 0.0
        assert p.y == 0.0
        assert p.z == 0.0
        assert p.orientation == Orientation.XYZ

    def test_create_origin_with_orientation(self) -> None:
        """Test origin with custom orientation. / 测试自定义方向."""
        pf = PlacementFactory.create(
            container_width=10.0,
            container_height=20.0,
            container_depth=30.0,
        )
        p = pf.create_origin_placement(orientation=Orientation.YXZ)
        assert p.orientation == Orientation.YXZ


# ============================================================
# OrientationAxisPermutationMapping tests
# ============================================================


class TestOrientationAxisPermutationMapping:
    """OrientationAxisPermutationMapping tests."""

    def test_from_xyz(self) -> None:
        """Test XYZ mapping. / 测试 XYZ 映射."""
        m = OrientationAxisPermutationMapping.from_orientation(Orientation.XYZ)
        assert m.x_index == 0
        assert m.y_index == 1
        assert m.z_index == 2

    def test_from_zyx(self) -> None:
        """Test ZYX mapping. / 测试 ZYX 映射."""
        m = OrientationAxisPermutationMapping.from_orientation(Orientation.ZYX)
        assert m.x_index == 2
        assert m.y_index == 1
        assert m.z_index == 0

    def test_all_orientations(self) -> None:
        """Test all orientations produce valid mappings. / 测试所有方向."""
        for orient in Orientation:
            m = OrientationAxisPermutationMapping.from_orientation(orient)
            indices = {m.x_index, m.y_index, m.z_index}
            assert indices == {0, 1, 2}


# ============================================================
# ConservativeRadiusEnvelope tests
# ============================================================


class TestConservativeRadiusEnvelope:
    """ConservativeRadiusEnvelope tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        cre = ConservativeRadiusEnvelope.create(radius=5.0, envelope_radius=5.5)
        assert cre.radius == 5.0

    def test_safety_margin(self) -> None:
        """Test safety_margin property. / 测试安全裕度属性."""
        cre = ConservativeRadiusEnvelope.create(radius=5.0, envelope_radius=5.5)
        assert cre.safety_margin == pytest.approx(0.5)


# ============================================================
# HorizontalCylinderSupportCoverage tests
# ============================================================


class TestHorizontalCylinderSupportCoverage:
    """HorizontalCylinderSupportCoverage tests."""

    def test_create(self) -> None:
        """Test creation with computed coverage. / 测试创建."""
        hcsc = HorizontalCylinderSupportCoverage.create(radius=3.0, length=10.0)
        assert hcsc.coverage_area == pytest.approx(60.0)

    def test_width(self) -> None:
        """Test width property. / 测试宽度属性."""
        hcsc = HorizontalCylinderSupportCoverage.create(radius=3.0, length=10.0)
        assert hcsc.width == pytest.approx(6.0)


# ============================================================
# PwlRadiusApproximationConfig tests
# ============================================================


class TestPwlRadiusApproximationConfig:
    """PwlRadiusApproximationConfig tests."""

    def test_create_with_defaults(self) -> None:
        """Test default values. / 测试默认值."""
        cfg = PwlRadiusApproximationConfig.create()
        assert cfg.segment_count == 8
        assert cfg.tolerance == pytest.approx(1e-6)

    def test_create_with_values(self) -> None:
        """Test custom values. / 测试自定义值."""
        cfg = PwlRadiusApproximationConfig.create(segment_count=16, tolerance=1e-8)
        assert cfg.segment_count == 16


# ============================================================
# QuantityContainerCore tests
# ============================================================


class TestQuantityContainerCore:
    """QuantityContainerCore tests."""

    def test_create_with_defaults(self) -> None:
        """Test default quantity. / 测试默认数量."""
        c = Container.create(width=2.0, height=3.0, depth=4.0)
        qcc = QuantityContainerCore.create(container=c)
        assert qcc.quantity == 1

    def test_volume(self) -> None:
        """Test volume property. / 测试体积属性."""
        c = Container.create(width=2.0, height=3.0, depth=4.0)
        qcc = QuantityContainerCore.create(container=c, quantity=5)
        assert qcc.volume == pytest.approx(24.0)


# ============================================================
# QuantityGeometryCore tests
# ============================================================


class TestQuantityGeometryCore:
    """QuantityGeometryCore tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        qgc = QuantityGeometryCore.create(
            shape=PackingShape.CUBOID,
            dimensions=(1.0, 2.0, 3.0),
            quantity=10,
        )
        assert qgc.quantity == 10

    def test_dimension_count(self) -> None:
        """Test dimension_count property. / 测试维度数量属性."""
        qgc = QuantityGeometryCore.create(
            shape=PackingShape.CYLINDER,
            dimensions=(5.0, 10.0),
        )
        assert qgc.dimension_count == 2


# ============================================================
# SemanticParameter tests
# ============================================================


class TestSemanticParameter:
    """SemanticParameter tests."""

    def test_create_with_defaults(self) -> None:
        """Test default description. / 测试默认描述."""
        sp = SemanticParameter.create(name="max_load", value=100.0)
        assert sp.description == ""


# ============================================================
# ShadowPriceMap (infrastructure) tests
# ============================================================


class TestShadowPriceMapInfra:
    """ShadowPriceMap infrastructure tests."""

    def test_create_and_get(self) -> None:
        """Test create and get_price. / 测试创建和获取价格."""
        spm = ShadowPriceMap.create(prices=(("c1", 1.0), ("c2", 2.0)))
        assert spm.get_price("c1") == pytest.approx(1.0)

    def test_get_price_missing(self) -> None:
        """Test missing key returns 0. / 测试缺失键返回 0."""
        spm = ShadowPriceMap.create(prices=())
        assert spm.get_price("missing") == pytest.approx(0.0)

    def test_size(self) -> None:
        """Test size property. / 测试大小属性."""
        spm = ShadowPriceMap.create(prices=(("a", 1.0), ("b", 2.0)))
        assert spm.size == 2


# ============================================================
# ProjectivePlaneGeometryMapping tests
# ============================================================


class TestProjectivePlaneGeometryMapping:
    """ProjectivePlaneGeometryMapping tests."""

    def test_create_with_defaults(self) -> None:
        """Test default offsets. / 测试默认偏移."""
        proj = Projection.create(width=10.0, height=20.0)
        ppm = ProjectivePlaneGeometryMapping.create(projection=proj)
        assert ppm.offset_x == 0.0
        assert ppm.offset_y == 0.0

    def test_center_x(self) -> None:
        """Test center_x property. / 测试中心 X 属性."""
        proj = Projection.create(width=10.0, height=20.0)
        ppm = ProjectivePlaneGeometryMapping.create(projection=proj, offset_x=5.0)
        assert ppm.center_x == pytest.approx(10.0)

    def test_center_y(self) -> None:
        """Test center_y property. / 测试中心 Y 属性."""
        proj = Projection.create(width=10.0, height=20.0)
        ppm = ProjectivePlaneGeometryMapping.create(projection=proj, offset_y=10.0)
        assert ppm.center_y == pytest.approx(20.0)


# ============================================================
# ContinuousRadiusModelComponent tests
# ============================================================


class TestContinuousRadiusModelComponent:
    """ContinuousRadiusModelComponent tests."""

    def test_create_with_defaults(self) -> None:
        """Test default is_integer. / 测试默认整数标志."""
        crmc = ContinuousRadiusModelComponent.create(
            radius_lower=1.0, radius_upper=10.0
        )
        assert crmc.is_integer is False

    def test_radius_range(self) -> None:
        """Test radius_range property. / 测试半径范围属性."""
        crmc = ContinuousRadiusModelComponent.create(radius_lower=2.0, radius_upper=8.0)
        assert crmc.radius_range == pytest.approx(6.0)


# ============================================================
# ContinuousRadiusSelectionExtractor tests
# ============================================================


class TestContinuousRadiusSelectionExtractor:
    """ContinuousRadiusSelectionExtractor tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        crse = ContinuousRadiusSelectionExtractor.create(
            item_key="cyl1", selected_radius=5.0
        )
        assert crse.selected_radius == pytest.approx(5.0)


# ============================================================
# CylinderShapeContract tests
# ============================================================


class TestCylinderShapeContract:
    """CylinderShapeContract tests."""

    def test_create_with_defaults(self) -> None:
        """Test default orientation flags. / 测试默认方向标志."""
        cyl = Cylinder.create(radius=5.0, height=10.0)
        csc = CylinderShapeContract.create(cylinder=cyl)
        assert csc.allow_horizontal is True
        assert csc.allow_vertical is True

    def test_create_with_flags(self) -> None:
        """Test custom orientation flags. / 测试自定义方向标志."""
        cyl = Cylinder.create(radius=5.0, height=10.0)
        csc = CylinderShapeContract.create(
            cylinder=cyl,
            allow_horizontal=False,
            allow_vertical=True,
        )
        assert csc.allow_horizontal is False


# ============================================================
# ItemContext tests
# ============================================================


class TestItemContext:
    """ItemContext tests."""

    def test_create_with_defaults(self) -> None:
        """Test default max_items. / 测试默认最大物品数."""
        c = Container.create(width=10.0, height=10.0, depth=10.0)
        ctx = ItemContext.create(container=c)
        assert ctx.max_items == 1000

    def test_create_with_custom(self) -> None:
        """Test custom max_items. / 测试自定义最大物品数."""
        c = Container.create(width=10.0, height=10.0, depth=10.0)
        ctx = ItemContext.create(container=c, max_items=500)
        assert ctx.max_items == 500


# ============================================================
# Aggregation tests
# ============================================================


class TestAggregation:
    """Aggregation tests / Aggregation 测试."""

    def test_create_with_defaults(self) -> None:
        """Test default count. / 测试默认数量."""
        agg = Aggregation.create(item_key="item1")
        assert agg.count == 1

    def test_create_with_count(self) -> None:
        """Test custom count. / 测试自定义数量."""
        agg = Aggregation.create(item_key="item1", count=50)
        assert agg.count == 50


# ============================================================
# PlacementPlaneMapping tests
# ============================================================


class TestPlacementPlaneMapping:
    """PlacementPlaneMapping tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        from ospf_python.framework.bpp3d.domain.item.model.placement_plane_mapping import (
            PlacementPlaneMapping,
        )

        p = Placement.create(x=1.0, y=2.0, z=3.0)
        proj = Projection.create(width=10.0, height=20.0)
        ppm = PlacementPlaneMapping.create(placement=p, projection=proj)
        assert ppm.plane == "xy"

    def test_create_with_plane(self) -> None:
        """Test custom plane. / 测试自定义平面."""
        from ospf_python.framework.bpp3d.domain.item.model.placement_plane_mapping import (
            PlacementPlaneMapping,
        )

        p = Placement.create(x=0.0, y=0.0, z=0.0)
        proj = Projection.create(width=5.0, height=5.0)
        ppm = PlacementPlaneMapping.create(placement=p, projection=proj, plane="xz")
        assert ppm.plane == "xz"


# ============================================================
# Type alias tests
# ============================================================


class TestLayerAssignmentAliases:
    """Layer assignment type alias tests."""

    def test_layer_id_alias(self) -> None:
        """Test LayerId is str. / 测试 LayerId 是 str."""
        lid: LayerId = "layer1"
        assert isinstance(lid, str)

    def test_container_id_alias(self) -> None:
        """Test ContainerId is str. / 测试 ContainerId 是 str."""
        cid: ContainerId = "container1"
        assert isinstance(cid, str)

    def test_layer_index_alias(self) -> None:
        """Test LayerIndex is int. / 测试 LayerIndex 是 int."""
        li: LayerIndex = 0
        assert isinstance(li, int)

    def test_quantity_alias(self) -> None:
        """Test Quantity is int. / 测试 Quantity 是 int."""
        q: Quantity = 100
        assert isinstance(q, int)
