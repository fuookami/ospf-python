"""CSP1D 行为测试。

Behavioral tests for CSP1D domain services:
CostarFiller, generation caches, aggregation.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.costar_filler import (
    CostarFiller,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_material_slice_template_cache import (
    GenerationMaterialSliceTemplateCache,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_material_width_index_cache import (
    GenerationMaterialWidthIndexCache,
)

# ============================================================
# CostarFiller behavioral tests
# ============================================================


class TestCostarFillerBehavior:
    """CostarFiller 行为测试。/ CostarFiller behavioral tests."""

    def test_rest_width_zero_returns_original_plans(self) -> None:
        """剩余宽度为 0 返回原方案。/ rest_width==0 returns original plans."""
        filler = CostarFiller(
            material_width=100.0,
            costars=(("A", "B", False),),
            cut_loss=2.0,
        )
        plans = ({"A": 2, "C": 1}, {"B": 3, "D": 1})
        result = filler.fill_costars(plans, rest_width=0.0)
        assert result == plans

    def test_rest_width_negative_returns_original_plans(self) -> None:
        """剩余宽度为负返回原方案。/ Negative rest_width returns original plans."""
        filler = CostarFiller(
            material_width=100.0,
            costars=(("A", "B", False),),
        )
        plans = ({"A": 2},)
        result = filler.fill_costars(plans, rest_width=-5.0)
        assert result == plans

    def test_empty_costars_returns_original_plans(self) -> None:
        """空 costar 返回原方案。/ Empty costars returns original plans."""
        filler = CostarFiller(material_width=100.0, costars=())
        plans = ({"A": 2, "B": 3},)
        result = filler.fill_costars(plans)
        assert result == plans

    def test_incompatible_pair_filtered(self) -> None:
        """不兼容对被过滤。/ Incompatible pair is filtered out."""
        filler = CostarFiller(
            material_width=100.0,
            costars=(("A", "B", False),),
        )
        # A 和 B 不兼容 → 包含两者的方案被过滤
        # A and B incompatible → plan with both is filtered
        plan_ok = {"A": 2, "C": 1}
        plan_bad = {"A": 2, "B": 3}
        result = filler.fill_costars((plan_ok, plan_bad))
        assert len(result) == 1
        assert result[0] == plan_ok

    def test_compatible_pair_kept(self) -> None:
        """兼容对保留。/ Compatible pair is kept."""
        filler = CostarFiller(
            material_width=100.0,
            costars=(("A", "B", True),),
        )
        plan = {"A": 2, "B": 3}
        result = filler.fill_costars((plan,))
        assert len(result) == 1

    def test_validate_positive_width(self) -> None:
        """正宽度验证通过。/ Positive width validates."""
        filler = CostarFiller(material_width=100.0)
        assert filler.validate() is True

    def test_validate_zero_width(self) -> None:
        """零宽度验证失败。/ Zero width fails validation."""
        filler = CostarFiller(material_width=0.0)
        assert filler.validate() is False

    def test_effective_width(self) -> None:
        """有效宽度计算。/ Effective width calculation."""
        filler = CostarFiller(material_width=100.0, cut_loss=2.0)
        assert filler.effective_width == pytest.approx(98.0)

    def test_incompatible_pairs(self) -> None:
        """获取不兼容对。/ Get incompatible pairs."""
        filler = CostarFiller(
            material_width=100.0,
            costars=(("A", "B", False), ("C", "D", True), ("E", "F", False)),
        )
        pairs = filler.incompatible_pairs()
        assert len(pairs) == 2
        assert ("A", "B") in pairs
        assert ("E", "F") in pairs


# ============================================================
# SliceTemplateCache behavioral tests
# ============================================================


class TestSliceTemplateCacheBehavior:
    """切片模板缓存行为测试。/ Slice template cache behavioral tests."""

    def test_empty_cache_miss(self) -> None:
        """空缓存查询返回 None。/ Empty cache miss returns None."""
        cache = GenerationMaterialSliceTemplateCache()
        assert cache.get("mat1") is None
        assert cache.is_empty is True

    def test_put_then_get_hit(self) -> None:
        """put 后 get 命中。/ put then get returns value."""
        cache = GenerationMaterialSliceTemplateCache()
        templates = ({"A": 2}, {"B": 3})
        cache2 = cache.put("mat1", templates)
        result = cache2.get("mat1")
        assert result is not None
        assert len(result) == 2

    def test_put_returns_new_instance(self) -> None:
        """put 返回新实例（不可变）。/ put returns new instance (immutable)."""
        cache = GenerationMaterialSliceTemplateCache()
        cache2 = cache.put("mat1", ({"A": 1},))
        assert cache is not cache2
        assert cache.is_empty is True
        assert cache2.size == 1

    def test_put_overwrites_existing(self) -> None:
        """put 覆盖已有条目。/ put overwrites existing entry."""
        cache = GenerationMaterialSliceTemplateCache()
        cache2 = cache.put("mat1", ({"A": 1},))
        cache3 = cache2.put("mat1", ({"B": 2},))
        assert cache3.size == 1
        result = cache3.get("mat1")
        assert result is not None
        assert len(result) == 1

    def test_contains(self) -> None:
        """contains 检查。/ contains check."""
        cache = GenerationMaterialSliceTemplateCache()
        assert cache.contains("mat1") is False
        cache2 = cache.put("mat1", ())
        assert cache2.contains("mat1") is True

    def test_size(self) -> None:
        """缓存大小。/ Cache size."""
        cache = GenerationMaterialSliceTemplateCache()
        cache2 = cache.put("mat1", ())
        cache3 = cache2.put("mat2", ())
        assert cache3.size == 2


# ============================================================
# WidthIndexCache behavioral tests
# ============================================================


class TestWidthIndexCacheBehavior:
    """宽度索引缓存行为测试。/ Width index cache behavioral tests."""

    def test_empty_cache_miss(self) -> None:
        """空缓存查询返回 None。/ Empty cache miss returns None."""
        cache = GenerationMaterialWidthIndexCache()
        assert cache.get_width("mat1") is None
        assert cache.get_index("mat1") is None

    def test_put_then_get_hit(self) -> None:
        """put 后 get 命中。/ put then get returns value."""
        cache = GenerationMaterialWidthIndexCache()
        cache2 = cache.put("mat1", 100.0, 0)
        assert cache2.get_width("mat1") == pytest.approx(100.0)
        assert cache2.get_index("mat1") == 0

    def test_put_returns_new_instance(self) -> None:
        """put 返回新实例（不可变）。/ put returns new instance (immutable)."""
        cache = GenerationMaterialWidthIndexCache()
        cache2 = cache.put("mat1", 100.0, 0)
        assert cache is not cache2
        assert cache.size == 0
        assert cache2.size == 1

    def test_put_overwrites_existing(self) -> None:
        """put 覆盖已有条目。/ put overwrites existing entry."""
        cache = GenerationMaterialWidthIndexCache()
        cache2 = cache.put("mat1", 100.0, 0)
        cache3 = cache2.put("mat1", 200.0, 1)
        assert cache3.size == 1
        assert cache3.get_width("mat1") == pytest.approx(200.0)

    def test_contains(self) -> None:
        """contains 检查。/ contains check."""
        cache = GenerationMaterialWidthIndexCache()
        assert cache.contains("mat1") is False
        cache2 = cache.put("mat1", 100.0, 0)
        assert cache2.contains("mat1") is True

    def test_sorted_by_width(self) -> None:
        """按宽度排序。/ Sort by width."""
        cache = GenerationMaterialWidthIndexCache()
        cache2 = cache.put("wide", 200.0, 1)
        cache3 = cache2.put("narrow", 50.0, 0)
        sorted_items = cache3.sorted_by_width()
        assert sorted_items[0][0] == "narrow"
        assert sorted_items[1][0] == "wide"


# ============================================================
# Aggregation behavioral tests (kept from original)
# ============================================================


class TestAggregation:
    """Aggregation 测试。/ Aggregation tests."""

    def test_default_creation(self) -> None:
        """默认创建。/ Default creation."""
        from ospf_python.framework.csp1d.domain.produce.aggregation import (
            Aggregation,
        )

        a = Aggregation()
        assert a.productions == ()
        assert a.total_quantity == 0
        assert a.product_count == 0

    def test_with_productions(self) -> None:
        """with_productions 创建新实例。/ with_productions."""
        from ospf_python.framework.csp1d.domain.produce.aggregation import (
            Aggregation,
        )

        a = Aggregation()

        class MockProduce:
            def __init__(self, quantity: int, product_key: str) -> None:
                self.quantity = quantity
                self.product_key = product_key

        p1 = MockProduce(10, "A")
        p2 = MockProduce(20, "B")
        p3 = MockProduce(5, "A")

        b = a.with_productions(
            productions=(p1, p2, p3),  # type: ignore[arg-type]
        )
        assert b.total_quantity == 35
        assert b.product_count == 2

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        from ospf_python.framework.csp1d.domain.produce.aggregation import (
            Aggregation,
        )

        a = Aggregation()
        with pytest.raises(AttributeError):
            a.productions = ()  # type: ignore[misc]
