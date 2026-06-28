"""CSP1D generation service behavioral tests.

Covers:
- GenerationMaterialWidthRangeKey
- GenerationWidthIndex
- GenerationTemplateReuse
- ConcurrentGenerationMaterialSliceTemplateCache
- YieldModel
"""

from __future__ import annotations

import importlib

import pytest

from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.concurrent_generation_material_slice_template_cache import (
    ConcurrentGenerationMaterialSliceTemplateCache,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_material_width_range_key import (
    GenerationMaterialWidthRangeKey,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_template_reuse import (
    GenerationTemplateReuse,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_width_index import (
    GenerationWidthIndex,
)

# importlib workaround for 'yield' keyword in path
_YieldModel = importlib.import_module(
    "ospf_python.framework.csp1d.domain.yield.model.yield_model",
).YieldModel


# ============================================================
# GenerationMaterialWidthRangeKey tests
# ============================================================


class TestGenerationMaterialWidthRangeKey:
    """GenerationMaterialWidthRangeKey behavioral tests."""

    def test_default_creation(self) -> None:
        """Test default creation. / 测试默认创建."""
        key = GenerationMaterialWidthRangeKey()
        assert key.min_width == 0.0
        assert key.max_width == 0.0
        assert key.precision == pytest.approx(1e-8)

    def test_contains_within_range(self) -> None:
        """Test contains returns True for width within range. / 测试范围内宽度返回 True."""
        key = GenerationMaterialWidthRangeKey(min_width=10.0, max_width=50.0)
        assert key.contains(10.0) is True
        assert key.contains(50.0) is True
        assert key.contains(30.0) is True

    def test_contains_outside_range(self) -> None:
        """Test contains returns False for width outside range. / 测试范围外宽度返回 False."""
        key = GenerationMaterialWidthRangeKey(min_width=10.0, max_width=50.0)
        assert key.contains(9.9) is False
        assert key.contains(50.1) is False

    def test_contains_respects_precision(self) -> None:
        """Test contains respects precision tolerance. / 测试 contains 考虑精度容差."""
        key = GenerationMaterialWidthRangeKey(
            min_width=10.0, max_width=50.0, precision=0.5,
        )
        assert key.contains(9.6) is True
        assert key.contains(50.4) is True
        assert key.contains(9.4) is False
        assert key.contains(50.6) is False

    def test_range_span(self) -> None:
        """Test range_span property. / 测试 range_span 属性."""
        key = GenerationMaterialWidthRangeKey(min_width=10.0, max_width=50.0)
        assert key.range_span == pytest.approx(40.0)

    def test_range_span_zero(self) -> None:
        """Test range_span is 0 for equal min and max. / 测试相等时 range_span 为 0."""
        key = GenerationMaterialWidthRangeKey(min_width=25.0, max_width=25.0)
        assert key.range_span == pytest.approx(0.0)

    def test_is_valid_normal(self) -> None:
        """Test is_valid for normal range. / 测试正常范围 is_valid."""
        key = GenerationMaterialWidthRangeKey(min_width=10.0, max_width=50.0)
        assert key.is_valid is True

    def test_is_valid_equal_bounds(self) -> None:
        """Test is_valid when min equals max. / 测试 min 等于 max 时 is_valid."""
        key = GenerationMaterialWidthRangeKey(min_width=25.0, max_width=25.0)
        assert key.is_valid is True

    def test_is_valid_negative_min(self) -> None:
        """Test is_valid with negative min_width. / 测试负 min_width 时 is_valid."""
        key = GenerationMaterialWidthRangeKey(min_width=-5.0, max_width=50.0)
        assert key.is_valid is False

    def test_is_valid_min_greater_than_max(self) -> None:
        """Test is_valid when min > max. / 测试 min > max 时 is_valid."""
        key = GenerationMaterialWidthRangeKey(min_width=60.0, max_width=50.0)
        assert key.is_valid is False

    def test_is_valid_zero_min(self) -> None:
        """Test is_valid with zero min_width. / 测试 min_width 为 0 时 is_valid."""
        key = GenerationMaterialWidthRangeKey(min_width=0.0, max_width=50.0)
        assert key.is_valid is True

    def test_overlaps_true(self) -> None:
        """Test overlaps returns True for overlapping ranges. / 测试重叠范围返回 True."""
        key1 = GenerationMaterialWidthRangeKey(min_width=10.0, max_width=50.0)
        key2 = GenerationMaterialWidthRangeKey(min_width=30.0, max_width=70.0)
        assert key1.overlaps(key2) is True
        assert key2.overlaps(key1) is True

    def test_overlaps_adjacent(self) -> None:
        """Test overlaps returns True for adjacent ranges. / 测试相邻范围返回 True."""
        key1 = GenerationMaterialWidthRangeKey(min_width=10.0, max_width=50.0)
        key2 = GenerationMaterialWidthRangeKey(min_width=50.0, max_width=90.0)
        assert key1.overlaps(key2) is True

    def test_overlaps_false(self) -> None:
        """Test overlaps returns False for non-overlapping ranges. / 测试不重叠范围返回 False."""
        key1 = GenerationMaterialWidthRangeKey(min_width=10.0, max_width=40.0)
        key2 = GenerationMaterialWidthRangeKey(min_width=50.0, max_width=90.0)
        assert key1.overlaps(key2) is False

    def test_overlaps_with_precision(self) -> None:
        """Test overlaps respects precision. / 测试 overlaps 考虑精度."""
        key1 = GenerationMaterialWidthRangeKey(
            min_width=10.0, max_width=49.5, precision=1.0,
        )
        key2 = GenerationMaterialWidthRangeKey(
            min_width=50.0, max_width=90.0, precision=1.0,
        )
        assert key1.overlaps(key2) is True

    def test_from_width_no_tolerance(self) -> None:
        """Test from_width with zero tolerance. / 测试零容差创建."""
        key = GenerationMaterialWidthRangeKey.from_width(width=100.0)
        assert key.min_width == pytest.approx(100.0)
        assert key.max_width == pytest.approx(100.0)

    def test_from_width_with_tolerance(self) -> None:
        """Test from_width with tolerance. / 测试带容差创建."""
        key = GenerationMaterialWidthRangeKey.from_width(
            width=100.0, tolerance=5.0,
        )
        assert key.min_width == pytest.approx(95.0)
        assert key.max_width == pytest.approx(105.0)

    def test_from_width_clamps_min_to_zero(self) -> None:
        """Test from_width clamps min_width to 0. / 测试 min_width 不小于 0."""
        key = GenerationMaterialWidthRangeKey.from_width(
            width=3.0, tolerance=5.0,
        )
        assert key.min_width == pytest.approx(0.0)
        assert key.max_width == pytest.approx(8.0)

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        key = GenerationMaterialWidthRangeKey(min_width=10.0, max_width=50.0)
        with pytest.raises(AttributeError):
            key.min_width = 20.0  # type: ignore[misc]

    def test_usable_as_dict_key(self) -> None:
        """Test usable as dictionary key (frozen dataclass). / 测试可作为字典键."""
        key1 = GenerationMaterialWidthRangeKey(min_width=10.0, max_width=50.0)
        key2 = GenerationMaterialWidthRangeKey(min_width=10.0, max_width=50.0)
        d = {key1: "value"}
        assert d[key2] == "value"


# ============================================================
# GenerationWidthIndex tests
# ============================================================


class TestGenerationWidthIndex:
    """GenerationWidthIndex behavioral tests."""

    def test_default_creation(self) -> None:
        """Test default creation. / 测试默认创建."""
        idx = GenerationWidthIndex()
        assert idx.entries == ()
        assert idx.total_keys == 0
        assert idx.width_count == 0

    def test_get_keys_at_found(self) -> None:
        """Test get_keys_at returns keys for known width. / 测试已知宽度返回键."""
        idx = GenerationWidthIndex(entries=((100.0, ("mat1", "mat2")), (200.0, ("mat3",))))
        result = idx.get_keys_at(100.0)
        assert result == ("mat1", "mat2")

    def test_get_keys_at_not_found(self) -> None:
        """Test get_keys_at returns empty for unknown width. / 测试未知宽度返回空."""
        idx = GenerationWidthIndex(entries=((100.0, ("mat1",)),))
        assert idx.get_keys_at(999.0) == ()

    def test_get_keys_at_respects_precision(self) -> None:
        """Test get_keys_at respects precision. / 测试 get_keys_at 考虑精度."""
        idx = GenerationWidthIndex(
            entries=((100.0, ("mat1",)),),
            precision=0.5,
        )
        assert idx.get_keys_at(100.3) == ("mat1",)
        assert idx.get_keys_at(100.6) == ()

    def test_get_keys_in_range(self) -> None:
        """Test get_keys_in_range returns all keys in range. / 测试范围内键查询."""
        idx = GenerationWidthIndex(
            entries=(
                (50.0, ("narrow",)),
                (100.0, ("mid1", "mid2")),
                (200.0, ("wide",)),
            ),
        )
        result = idx.get_keys_in_range(80.0, 150.0)
        assert "mid1" in result
        assert "mid2" in result
        assert "narrow" not in result
        assert "wide" not in result

    def test_get_keys_in_range_inclusive_bounds(self) -> None:
        """Test get_keys_in_range includes boundary widths. / 测试范围包含边界."""
        idx = GenerationWidthIndex(
            entries=((50.0, ("A",)), (100.0, ("B",)), (150.0, ("C",))),
        )
        result = idx.get_keys_in_range(50.0, 150.0)
        assert "A" in result
        assert "B" in result
        assert "C" in result

    def test_get_keys_in_range_empty(self) -> None:
        """Test get_keys_in_range returns empty when no match. / 测试无匹配返回空."""
        idx = GenerationWidthIndex(entries=((50.0, ("A",)),))
        assert idx.get_keys_in_range(200.0, 300.0) == ()

    def test_add_new_width(self) -> None:
        """Test add creates new width entry. / 测试添加新宽度条目."""
        idx = GenerationWidthIndex()
        idx2 = idx.add(100.0, "mat1")
        assert idx is not idx2
        assert idx.total_keys == 0
        assert idx2.total_keys == 1
        assert idx2.get_keys_at(100.0) == ("mat1",)

    def test_add_key_to_existing_width(self) -> None:
        """Test add appends key to existing width. / 测试向已有宽度追加键."""
        idx = GenerationWidthIndex(entries=((100.0, ("mat1",)),))
        idx2 = idx.add(100.0, "mat2")
        assert idx2.total_keys == 2
        assert idx2.get_keys_at(100.0) == ("mat1", "mat2")

    def test_add_duplicate_key_ignored(self) -> None:
        """Test add ignores duplicate key at same width. / 测试忽略重复键."""
        idx = GenerationWidthIndex(entries=((100.0, ("mat1",)),))
        idx2 = idx.add(100.0, "mat1")
        assert idx2 is idx

    def test_add_preserves_precision(self) -> None:
        """Test add preserves precision. / 测试 add 保留精度."""
        idx = GenerationWidthIndex(precision=0.5)
        idx2 = idx.add(100.0, "mat1")
        assert idx2.precision == pytest.approx(0.5)

    def test_contains_key_true(self) -> None:
        """Test contains_key returns True for existing key. / 测试包含键返回 True."""
        idx = GenerationWidthIndex(entries=((100.0, ("mat1", "mat2")),))
        assert idx.contains_key("mat1") is True
        assert idx.contains_key("mat2") is True

    def test_contains_key_false(self) -> None:
        """Test contains_key returns False for missing key. / 测试不包含键返回 False."""
        idx = GenerationWidthIndex(entries=((100.0, ("mat1",)),))
        assert idx.contains_key("mat3") is False

    def test_total_keys(self) -> None:
        """Test total_keys property. / 测试 total_keys 属性."""
        idx = GenerationWidthIndex(
            entries=((100.0, ("A", "B")), (200.0, ("C",))),
        )
        assert idx.total_keys == 3

    def test_width_count(self) -> None:
        """Test width_count property. / 测试 width_count 属性."""
        idx = GenerationWidthIndex(
            entries=((100.0, ("A",)), (200.0, ("B",)), (300.0, ("C",))),
        )
        assert idx.width_count == 3

    def test_sorted_widths(self) -> None:
        """Test sorted_widths property. / 测试 sorted_widths 属性."""
        idx = GenerationWidthIndex(
            entries=((200.0, ("B",)), (100.0, ("A",)), (300.0, ("C",))),
        )
        assert idx.sorted_widths == (200.0, 100.0, 300.0)

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        idx = GenerationWidthIndex()
        with pytest.raises(AttributeError):
            idx.entries = ()  # type: ignore[misc]


# ============================================================
# GenerationTemplateReuse tests
# ============================================================


class TestGenerationTemplateReuse:
    """GenerationTemplateReuse behavioral tests."""

    def test_default_creation(self) -> None:
        """Test default creation. / 测试默认创建."""
        reuse = GenerationTemplateReuse()
        assert reuse.reuse_map == ()
        assert reuse.registered_templates == ()
        assert reuse.total_registered == 0
        assert reuse.reuse_link_count == 0

    def test_register_template(self) -> None:
        """Test register adds template. / 测试注册模板."""
        reuse = GenerationTemplateReuse()
        template = {"P1": 3, "P2": 2}
        reuse2 = reuse.register("Steel", template)
        assert reuse is not reuse2
        assert reuse.total_registered == 0
        assert reuse2.total_registered == 1
        assert reuse2.registered_templates[0] == ("Steel", template)

    def test_register_multiple_templates(self) -> None:
        """Test register accumulates templates. / 测试累积注册模板."""
        reuse = GenerationTemplateReuse()
        reuse2 = reuse.register("Steel", {"P1": 3})
        reuse3 = reuse2.register("Aluminum", {"P2": 2})
        assert reuse3.total_registered == 2

    def test_add_reuse_link_new_source(self) -> None:
        """Test add_reuse_link for new source material. / 测试新源材料复用链接."""
        reuse = GenerationTemplateReuse()
        reuse2 = reuse.add_reuse_link("Steel", "Aluminum")
        assert reuse.reuse_link_count == 0
        assert reuse2.reuse_link_count == 1
        assert reuse2.get_targets("Steel") == ("Aluminum",)

    def test_add_reuse_link_existing_source(self) -> None:
        """Test add_reuse_link appends to existing source. / 测试追加到已有源材料."""
        reuse = GenerationTemplateReuse()
        reuse2 = reuse.add_reuse_link("Steel", "Aluminum")
        reuse3 = reuse2.add_reuse_link("Steel", "Copper")
        assert reuse3.reuse_link_count == 2
        targets = reuse3.get_targets("Steel")
        assert "Aluminum" in targets
        assert "Copper" in targets

    def test_add_reuse_link_duplicate_target_ignored(self) -> None:
        """Test add_reuse_link ignores duplicate target. / 测试忽略重复目标."""
        reuse = GenerationTemplateReuse()
        reuse2 = reuse.add_reuse_link("Steel", "Aluminum")
        reuse3 = reuse2.add_reuse_link("Steel", "Aluminum")
        assert reuse3.reuse_link_count == 1
        assert reuse3.get_targets("Steel") == ("Aluminum",)

    def test_get_targets_found(self) -> None:
        """Test get_targets returns targets for known source. / 测试已知源返回目标."""
        reuse = GenerationTemplateReuse(
            reuse_map=(("Steel", ("Aluminum", "Copper")),),
        )
        assert reuse.get_targets("Steel") == ("Aluminum", "Copper")

    def test_get_targets_not_found(self) -> None:
        """Test get_targets returns empty for unknown source. / 测试未知源返回空."""
        reuse = GenerationTemplateReuse()
        assert reuse.get_targets("Steel") == ()

    def test_get_templates_for_found(self) -> None:
        """Test get_templates_for returns templates for material. / 测试已知材料返回模板."""
        tpl1 = {"P1": 3}
        tpl2 = {"P2": 2}
        reuse = GenerationTemplateReuse(
            registered_templates=(
                ("Steel", tpl1),
                ("Aluminum", tpl2),
                ("Steel", {"P3": 1}),
            ),
        )
        templates = reuse.get_templates_for("Steel")
        assert len(templates) == 2
        assert tpl1 in templates

    def test_get_templates_for_not_found(self) -> None:
        """Test get_templates_for returns empty for unknown material. / 测试未知材料返回空."""
        reuse = GenerationTemplateReuse()
        assert reuse.get_templates_for("Steel") == ()

    def test_can_reuse_true(self) -> None:
        """Test can_reuse returns True for linked materials. / 测试已链接材料返回 True."""
        reuse = GenerationTemplateReuse(
            reuse_map=(("Steel", ("Aluminum", "Copper")),),
        )
        assert reuse.can_reuse("Steel", "Aluminum") is True
        assert reuse.can_reuse("Steel", "Copper") is True

    def test_can_reuse_false(self) -> None:
        """Test can_reuse returns False for unlinked materials. / 测试未链接材料返回 False."""
        reuse = GenerationTemplateReuse(
            reuse_map=(("Steel", ("Aluminum",)),),
        )
        assert reuse.can_reuse("Steel", "Copper") is False
        assert reuse.can_reuse("Aluminum", "Steel") is False

    def test_total_registered(self) -> None:
        """Test total_registered property. / 测试 total_registered 属性."""
        reuse = GenerationTemplateReuse(
            registered_templates=(("Steel", {"P1": 3}), ("Aluminum", {"P2": 2})),
        )
        assert reuse.total_registered == 2

    def test_reuse_link_count(self) -> None:
        """Test reuse_link_count property. / 测试 reuse_link_count 属性."""
        reuse = GenerationTemplateReuse(
            reuse_map=(("Steel", ("Aluminum", "Copper")), ("Aluminum", ("Copper",))),
        )
        assert reuse.reuse_link_count == 3

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        reuse = GenerationTemplateReuse()
        with pytest.raises(AttributeError):
            reuse.reuse_map = ()  # type: ignore[misc]


# ============================================================
# ConcurrentGenerationMaterialSliceTemplateCache tests
# ============================================================


class TestConcurrentGenerationMaterialSliceTemplateCache:
    """ConcurrentGenerationMaterialSliceTemplateCache behavioral tests."""

    def test_default_creation(self) -> None:
        """Test default creation. / 测试默认创建."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        assert cache.is_empty is True
        assert cache.size == 0
        assert cache.hit_count == 0
        assert cache.miss_count == 0
        assert cache.total_lookups == 0
        assert cache.hit_rate == pytest.approx(0.0)

    def test_get_miss(self) -> None:
        """Test get returns None for missing material. / 测试缺失材料返回 None."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        assert cache.get("mat1") is None

    def test_put_then_get_hit(self) -> None:
        """Test put then get returns templates. / 测试 put 后 get 命中."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        templates = ({"P1": 3, "P2": 2},)
        cache2 = cache.put("mat1", templates)
        result = cache2.get("mat1")
        assert result is not None
        assert len(result) == 1

    def test_put_returns_new_instance(self) -> None:
        """Test put returns new instance (immutable). / 测试 put 返回新实例."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        cache2 = cache.put("mat1", ())
        assert cache is not cache2
        assert cache.is_empty is True
        assert cache2.size == 1

    def test_contains(self) -> None:
        """Test contains check. / 测试 contains 检查."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        assert cache.contains("mat1") is False
        cache2 = cache.put("mat1", ())
        assert cache2.contains("mat1") is True

    def test_record_hit(self) -> None:
        """Test record_hit increments hit_count. / 测试 record_hit 增加命中计数."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        cache2 = cache.record_hit()
        assert cache.hit_count == 0
        assert cache2.hit_count == 1
        assert cache2.miss_count == 0

    def test_record_miss(self) -> None:
        """Test record_miss increments miss_count. / 测试 record_miss 增加未命中计数."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        cache2 = cache.record_miss()
        assert cache.miss_count == 0
        assert cache2.miss_count == 1
        assert cache2.hit_count == 0

    def test_total_lookups(self) -> None:
        """Test total_lookups sums hit and miss counts. / 测试 total_lookups 汇总."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        cache2 = cache.record_hit().record_hit().record_miss()
        assert cache2.total_lookups == 3

    def test_hit_rate_with_lookups(self) -> None:
        """Test hit_rate with some lookups. / 测试有查询时的命中率."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        cache2 = cache.record_hit().record_hit().record_hit().record_miss()
        assert cache2.hit_rate == pytest.approx(0.75)

    def test_hit_rate_no_lookups(self) -> None:
        """Test hit_rate is 0.0 when no lookups. / 测试无查询时命中率为 0."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        assert cache.hit_rate == pytest.approx(0.0)

    def test_hit_rate_all_hits(self) -> None:
        """Test hit_rate is 1.0 when all hits. / 测试全部命中时命中率为 1."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        cache2 = cache.record_hit().record_hit()
        assert cache2.hit_rate == pytest.approx(1.0)

    def test_hit_rate_all_misses(self) -> None:
        """Test hit_rate is 0.0 when all misses. / 测试全部未命中时命中率为 0."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        cache2 = cache.record_miss().record_miss()
        assert cache2.hit_rate == pytest.approx(0.0)

    def test_size(self) -> None:
        """Test size property. / 测试 size 属性."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        cache2 = cache.put("mat1", ())
        cache3 = cache2.put("mat2", ())
        assert cache3.size == 2

    def test_is_empty(self) -> None:
        """Test is_empty property. / 测试 is_empty 属性."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        assert cache.is_empty is True
        cache2 = cache.put("mat1", ())
        assert cache2.is_empty is False

    def test_record_hit_preserves_cache(self) -> None:
        """Test record_hit preserves underlying cache. / 测试 record_hit 保留底层缓存."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        templates = ({"P1": 2},)
        cache2 = cache.put("mat1", templates)
        cache3 = cache2.record_hit()
        assert cache3.get("mat1") is not None
        assert cache3.size == 1

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""
        cache = ConcurrentGenerationMaterialSliceTemplateCache()
        with pytest.raises(AttributeError):
            cache.hit_count = 5  # type: ignore[misc]


# ============================================================
# _YieldModel tests
# ============================================================


class TestYieldModelBehavioral:
    """YieldModel behavioral tests. / YieldModel 行为测试."""

    def test_default_creation(self) -> None:
        """Test default creation with lazy config. / 测试默认创建."""
        model = _YieldModel()
        assert model.product_yields == ()
        assert model.material_inputs == ()

    def test_create_with_config(self) -> None:
        """Test create factory with config. / 测试带配置的工厂方法."""

        class MockConfig:
            precision = 1e-8

        model = _YieldModel.create(config=MockConfig())
        assert model.config is not None

    def test_with_product_yields(self) -> None:
        """Test with_product_yields returns new instance. / 测试 with_product_yields 返回新实例."""

        class MockConfig:
            precision = 1e-8

        model = _YieldModel.create(config=MockConfig())
        yields = (("P1", 80.0, 100.0), ("P2", 60.0, 100.0))
        model2 = model.with_product_yields(yields=yields)
        assert model is not model2
        assert model.product_yields == ()
        assert model2.product_yields == yields

    def test_get_yield_ratio_found(self) -> None:
        """Test get_yield_ratio for known product. / 测试已知产品产出率."""

        class MockConfig:
            precision = 1e-8

        model = _YieldModel.create(config=MockConfig())
        model2 = model.with_product_yields(
            yields=(("P1", 80.0, 100.0), ("P2", 60.0, 100.0)),
        )
        assert model2.get_yield_ratio("P1") == pytest.approx(0.8)
        assert model2.get_yield_ratio("P2") == pytest.approx(0.6)

    def test_get_yield_ratio_not_found(self) -> None:
        """Test get_yield_ratio returns 0.0 for unknown product. / 测试未知产品产出率为 0."""

        class MockConfig:
            precision = 1e-8

        model = _YieldModel.create(config=MockConfig())
        model2 = model.with_product_yields(yields=(("P1", 80.0, 100.0),))
        assert model2.get_yield_ratio("P3") == pytest.approx(0.0)

    def test_get_yield_ratio_zero_input(self) -> None:
        """Test get_yield_ratio returns 0.0 when input is zero. / 测试零投入产出率为 0."""

        class MockConfig:
            precision = 1e-8

        model = _YieldModel.create(config=MockConfig())
        model2 = model.with_product_yields(yields=(("P1", 50.0, 0.0),))
        assert model2.get_yield_ratio("P1") == pytest.approx(0.0)

    def test_get_yield_ratio_tiny_input(self) -> None:
        """Test get_yield_ratio returns 0.0 when input is below precision. / 测试极小投入产出率为 0."""

        class MockConfig:
            precision = 1e-4

        model = _YieldModel.create(config=MockConfig())
        model2 = model.with_product_yields(yields=(("P1", 50.0, 1e-8),))
        assert model2.get_yield_ratio("P1") == pytest.approx(0.0)

    def test_overall_yield_ratio(self) -> None:
        """Test overall_yield_ratio property. / 测试总体产出率."""

        class MockConfig:
            precision = 1e-8

        model = _YieldModel.create(config=MockConfig())
        model2 = model.with_product_yields(
            yields=(("P1", 80.0, 100.0), ("P2", 60.0, 100.0)),
        )
        assert model2.overall_yield_ratio == pytest.approx(0.7)

    def test_overall_yield_ratio_no_yields(self) -> None:
        """Test overall_yield_ratio is 0.0 when no yields. / 测试无产出时总体产出率为 0."""

        class MockConfig:
            precision = 1e-8

        model = _YieldModel.create(config=MockConfig())
        assert model.overall_yield_ratio == pytest.approx(0.0)

    def test_overall_yield_ratio_zero_total_input(self) -> None:
        """Test overall_yield_ratio is 0.0 when total input is zero. / 测试零总投入时总体产出率为 0."""

        class MockConfig:
            precision = 1e-8

        model = _YieldModel.create(config=MockConfig())
        model2 = model.with_product_yields(
            yields=(("P1", 0.0, 0.0),),
        )
        assert model2.overall_yield_ratio == pytest.approx(0.0)

    def test_config_precision_from_default(self) -> None:
        """Test default config has precision attribute. / 测试默认配置有 precision 属性."""
        model = _YieldModel()
        assert hasattr(model.config, "precision")

    def test_frozen(self) -> None:
        """Test immutability. / 测试不可变性."""

        class MockConfig:
            precision = 1e-8

        model = _YieldModel.create(config=MockConfig())
        with pytest.raises(AttributeError):
            model.product_yields = ()  # type: ignore[misc]
