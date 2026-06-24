"""bpp3d 框架额外测试 / Additional bpp3d framework tests.

覆盖 Bpp3dItemModelAsync, Bpp3dItemServiceAsync, ItemHeightCombinator,
ItemMerger, LoadingOrderCalculator, RendererDTO,
PwlRadiusSquaredApproximation 等类。
Covers Bpp3dItemModelAsync, Bpp3dItemServiceAsync,
ItemHeightCombinator, ItemMerger, LoadingOrderCalculator,
RendererDTO, PwlRadiusSquaredApproximation, etc.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.bpp3d.domain.item.aggregation import Aggregation
from ospf_python.framework.bpp3d.domain.item.model.bpp3d_item_model_async import (
    Bpp3dItemModelAsync,
)
from ospf_python.framework.bpp3d.domain.item.model.item import Item
from ospf_python.framework.bpp3d.domain.item.model.layer import Layer
from ospf_python.framework.bpp3d.domain.item.model.material import Material
from ospf_python.framework.bpp3d.domain.item.service.bpp3d_item_service_async import (
    Bpp3dItemServiceAsync,
)
from ospf_python.framework.bpp3d.domain.item.service.item_height_combinator import (
    ItemHeightCombinator,
)
from ospf_python.framework.bpp3d.domain.item.service.item_merger import (
    ItemMerger,
)
from ospf_python.framework.bpp3d.domain.item.service.loading_order_calculator import (
    LoadingOrderCalculator,
)
from ospf_python.framework.bpp3d.infrastructure.dto.renderer_dto import (
    RendererDTO,
)
from ospf_python.framework.bpp3d.infrastructure.orientation import Orientation
from ospf_python.framework.bpp3d.infrastructure.placement import Placement
from ospf_python.framework.bpp3d.infrastructure.projection import Projection
from ospf_python.framework.bpp3d.infrastructure.pwl_radius_approximation_config import (
    PwlRadiusApproximationConfig,
)
from ospf_python.framework.bpp3d.infrastructure.pwl_radius_squared_approximation import (
    PwlRadiusSquaredApproximation,
)
from ospf_python.framework.bpp3d.infrastructure.shadow_price_map import (
    ShadowPriceMap,
)

# ============================================================
# ABC tests
# ============================================================


class TestBpp3dItemModelAsync:
    """Bpp3dItemModelAsync ABC 测试 / ABC tests."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            Bpp3dItemModelAsync(model_id="m1")  # type: ignore[abstract]

    def test_has_solve_async(self) -> None:
        """有 solve_async 方法 / Has solve_async method."""
        assert hasattr(Bpp3dItemModelAsync, "solve_async")

    def test_has_get_status_async(self) -> None:
        """有 get_status_async 方法 / Has get_status_async."""
        assert hasattr(Bpp3dItemModelAsync, "get_status_async")


class TestBpp3dItemServiceAsync:
    """Bpp3dItemServiceAsync ABC 测试 / ABC tests."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            Bpp3dItemServiceAsync(service_id="s1")  # type: ignore[abstract]

    def test_has_get_items_async(self) -> None:
        """有 get_items_async 方法 / Has get_items_async."""
        assert hasattr(Bpp3dItemServiceAsync, "get_items_async")

    def test_has_solve_async(self) -> None:
        """有 solve_async 方法 / Has solve_async method."""
        assert hasattr(Bpp3dItemServiceAsync, "solve_async")


# ============================================================
# ItemHeightCombinator tests
# ============================================================


class TestItemHeightCombinator:
    """ItemHeightCombinator 测试 / Tests."""

    def test_create_default(self) -> None:
        """默认创建 / Create with defaults."""
        c = ItemHeightCombinator.create(container_height=10.0)
        assert c.container_height == 10.0
        assert c.tolerance == pytest.approx(1e-6)

    def test_create_custom_tolerance(self) -> None:
        """自定义容差 / Custom tolerance."""
        c = ItemHeightCombinator.create(
            container_height=5.0,
            tolerance=0.01,
        )
        assert c.tolerance == pytest.approx(0.01)

    def test_fits_height_within(self) -> None:
        """物品高度适合 / Item fits height."""
        c = ItemHeightCombinator.create(container_height=10.0)
        assert c.fits_height(9.0) is True

    def test_fits_height_equal(self) -> None:
        """物品高度等于容器 / Item height equals container."""
        c = ItemHeightCombinator.create(container_height=10.0)
        assert c.fits_height(10.0) is True

    def test_fits_height_exceeds(self) -> None:
        """物品高度超出 / Item exceeds height."""
        c = ItemHeightCombinator.create(container_height=10.0)
        assert c.fits_height(10.1) is False

    def test_remaining_height(self) -> None:
        """剩余高度计算 / Remaining height calculation."""
        c = ItemHeightCombinator.create(container_height=10.0)
        assert c.remaining_height(3.0) == pytest.approx(7.0)

    def test_remaining_height_zero(self) -> None:
        """剩余高度为零 / Remaining height zero."""
        c = ItemHeightCombinator.create(container_height=10.0)
        assert c.remaining_height(15.0) == pytest.approx(0.0)


# ============================================================
# ItemMerger tests
# ============================================================


class TestItemMerger:
    """ItemMerger 测试 / Tests."""

    def test_create_default(self) -> None:
        """默认创建 / Create with defaults."""
        m = ItemMerger.create()
        assert m.merge_threshold == pytest.approx(1e-6)

    def test_can_merge_same_dimensions(self) -> None:
        """相同尺寸可合并 / Same dimensions can merge."""
        m = ItemMerger.create()
        a = Item.create(
            item_key="a",
            width=1.0,
            height=2.0,
            depth=3.0,
        )
        b = Item.create(
            item_key="b",
            width=1.0,
            height=2.0,
            depth=3.0,
        )
        assert m.can_merge(a, b) is True

    def test_can_merge_different_dimensions(self) -> None:
        """不同尺寸不可合并 / Different dims cannot merge."""
        m = ItemMerger.create()
        a = Item.create(
            item_key="a",
            width=1.0,
            height=2.0,
            depth=3.0,
        )
        b = Item.create(
            item_key="b",
            width=1.5,
            height=2.0,
            depth=3.0,
        )
        assert m.can_merge(a, b) is False

    def test_merge_combines_quantity(self) -> None:
        """合并后数量相加 / Merge adds quantities."""
        m = ItemMerger.create()
        a = Item.create(
            item_key="a",
            width=1.0,
            height=2.0,
            depth=3.0,
            quantity=5,
        )
        b = Item.create(
            item_key="b",
            width=1.0,
            height=2.0,
            depth=3.0,
            quantity=3,
        )
        result = m.merge(a, b)
        assert result.quantity == 8
        assert result.item_key == "a"


# ============================================================
# LoadingOrderCalculator tests
# ============================================================


class TestLoadingOrderCalculator:
    """LoadingOrderCalculator 测试 / Tests."""

    def test_create_default(self) -> None:
        """默认创建 / Create with defaults."""
        c = LoadingOrderCalculator.create()
        assert c.prioritize_large is True

    def test_create_prioritize_small(self) -> None:
        """优先小物品 / Prioritize small items."""
        c = LoadingOrderCalculator.create(prioritize_large=False)
        assert c.prioritize_large is False

    def test_sort_key_large_first(self) -> None:
        """大物品优先排序键 / Large-first sort key."""
        c = LoadingOrderCalculator.create(prioritize_large=True)
        key = c.get_sort_key(2.0, 3.0, 4.0)
        assert key == pytest.approx(-24.0)

    def test_sort_key_small_first(self) -> None:
        """小物品优先排序键 / Small-first sort key."""
        c = LoadingOrderCalculator.create(prioritize_large=False)
        key = c.get_sort_key(2.0, 3.0, 4.0)
        assert key == pytest.approx(24.0)


# ============================================================
# Item and domain model tests
# ============================================================


class TestItem:
    """Item 测试 / Tests."""

    def test_create_default_quantity(self) -> None:
        """默认数量为 1 / Default quantity is 1."""
        item = Item.create(
            item_key="k1",
            width=1.0,
            height=2.0,
            depth=3.0,
        )
        assert item.quantity == 1

    def test_volume(self) -> None:
        """体积计算 / Volume calculation."""
        item = Item.create(
            item_key="k1",
            width=2.0,
            height=3.0,
            depth=4.0,
        )
        assert item.volume == pytest.approx(24.0)

    def test_total_volume(self) -> None:
        """总体积计算 / Total volume calculation."""
        item = Item.create(
            item_key="k1",
            width=2.0,
            height=3.0,
            depth=4.0,
            quantity=5,
        )
        assert item.total_volume == pytest.approx(120.0)

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        item = Item.create(
            item_key="k1",
            width=1.0,
            height=2.0,
            depth=3.0,
        )
        with pytest.raises(AttributeError):
            item.width = 5.0  # type: ignore[misc]


class TestMaterial:
    """Material 测试 / Tests."""

    def test_create(self) -> None:
        """创建材质 / Create material."""
        m = Material.create(
            material_id="m1",
            name="steel",
            density=7.8,
        )
        assert m.material_id == "m1"
        assert m.name == "steel"
        assert m.density == pytest.approx(7.8)

    def test_default_density(self) -> None:
        """默认密度为 0 / Default density is 0."""
        m = Material.create(material_id="m1", name="wood")
        assert m.density == pytest.approx(0.0)


class TestLayer:
    """Layer 测试 / Tests."""

    def test_create(self) -> None:
        """创建层 / Create layer."""
        l = Layer.create(
            layer_id="l1",
            height=5.0,
            item_keys=("a", "b"),
        )
        assert l.layer_id == "l1"
        assert l.height == pytest.approx(5.0)
        assert l.item_count == 2

    def test_item_count_empty(self) -> None:
        """空层物品数为 0 / Empty layer item count is 0."""
        l = Layer.create(layer_id="l1", height=5.0)
        assert l.item_count == 0


class TestAggregation:
    """Aggregation 测试 / Tests."""

    def test_create_default(self) -> None:
        """默认创建 / Create with defaults."""
        a = Aggregation.create(item_key="k1")
        assert a.item_key == "k1"
        assert a.count == 1

    def test_create_custom_count(self) -> None:
        """自定义数量 / Custom count."""
        a = Aggregation.create(item_key="k1", count=10)
        assert a.count == 10


# ============================================================
# Infrastructure tests
# ============================================================


class TestProjection:
    """Projection 测试 / Tests."""

    def test_area(self) -> None:
        """面积计算 / Area calculation."""
        p = Projection.create(width=3.0, height=4.0)
        assert p.area == pytest.approx(12.0)

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        p = Projection.create(width=3.0, height=4.0)
        with pytest.raises(AttributeError):
            p.width = 5.0  # type: ignore[misc]


class TestShadowPriceMap:
    """ShadowPriceMap 测试 / Tests."""

    def test_get_existing(self) -> None:
        """获取已存在价格 / Get existing price."""
        m = ShadowPriceMap.create(
            prices=(("c1", 1.5), ("c2", 2.5)),
        )
        assert m.get_price("c1") == pytest.approx(1.5)

    def test_get_missing(self) -> None:
        """获取不存在价格返回 0 / Missing price returns 0."""
        m = ShadowPriceMap.create(prices=(("c1", 1.5),))
        assert m.get_price("unknown") == pytest.approx(0.0)

    def test_size(self) -> None:
        """映射大小 / Map size."""
        m = ShadowPriceMap.create(
            prices=(("c1", 1.0), ("c2", 2.0), ("c3", 3.0)),
        )
        assert m.size == 3


class TestOrientation:
    """Orientation 枚举测试 / Enum tests."""

    def test_xyz_value(self) -> None:
        """XYZ 值 / XYZ value."""
        assert Orientation.XYZ.value == "xyz"

    def test_all_members(self) -> None:
        """六个方向成员 / Six orientation members."""
        assert len(Orientation) == 6


class TestPlacement:
    """Placement 测试 / Tests."""

    def test_create_default_orientation(self) -> None:
        """默认方向创建 / Default orientation."""
        p = Placement.create(x=1.0, y=2.0, z=3.0)
        assert p.orientation == Orientation.XYZ

    def test_create_custom_orientation(self) -> None:
        """自定义方向 / Custom orientation."""
        p = Placement.create(
            x=1.0,
            y=2.0,
            z=3.0,
            orientation=Orientation.ZYX,
        )
        assert p.orientation == Orientation.ZYX


class TestPwlRadiusApproximationConfig:
    """PwlRadiusApproximationConfig 测试 / Tests."""

    def test_create_default(self) -> None:
        """默认创建 / Create with defaults."""
        c = PwlRadiusApproximationConfig.create()
        assert c.segment_count == 8
        assert c.tolerance == pytest.approx(1e-6)

    def test_create_custom(self) -> None:
        """自定义参数 / Custom parameters."""
        c = PwlRadiusApproximationConfig.create(
            segment_count=16,
            tolerance=1e-4,
        )
        assert c.segment_count == 16


class TestPwlRadiusSquaredApproximation:
    """PwlRadiusSquaredApproximation 测试 / Tests."""

    def test_create(self) -> None:
        """创建近似实例 / Create approximation."""
        config = PwlRadiusApproximationConfig.create()
        approx = PwlRadiusSquaredApproximation.create(
            config=config,
            breakpoints=(0.0, 0.5, 1.0),
            slopes=(1.0, 2.0),
        )
        assert approx.config is config
        assert approx.segment_count == 2

    def test_segment_count(self) -> None:
        """分段数等于断点减一 / Segments = breakpoints - 1."""
        config = PwlRadiusApproximationConfig.create()
        approx = PwlRadiusSquaredApproximation.create(
            config=config,
            breakpoints=(0.0, 0.25, 0.5, 0.75, 1.0),
            slopes=(1.0, 2.0, 3.0, 4.0),
        )
        assert approx.segment_count == 4


class TestRendererDTO:
    """RendererDTO 测试 / Tests."""

    def test_create(self) -> None:
        """创建渲染 DTO / Create renderer DTO."""
        placement = Placement.create(x=0.0, y=0.0, z=0.0)
        dto = RendererDTO.create(
            item_id="item1",
            placement=placement,
            width=10.0,
            height=20.0,
            depth=30.0,
        )
        assert dto.item_id == "item1"
        assert dto.width == pytest.approx(10.0)
        assert dto.placement is placement

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        placement = Placement.create(x=0.0, y=0.0, z=0.0)
        dto = RendererDTO.create(
            item_id="item1",
            placement=placement,
            width=10.0,
            height=20.0,
            depth=30.0,
        )
        with pytest.raises(AttributeError):
            dto.item_id = "other"  # type: ignore[misc]
