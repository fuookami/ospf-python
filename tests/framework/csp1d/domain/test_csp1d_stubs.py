"""CSP1D 桩类测试。

Tests for CSP1D domain stub dataclasses and Aggregation.
"""

from __future__ import annotations

import pytest

# ============================================================
# Cutting plan generation service stubs
# ============================================================


class TestCuttingPlanGenerationStubs:
    """切割计划生成桩类测试。/ Cutting plan stub tests."""

    def test_concurrent_generation_material_slice_template_cache(
        self,
    ) -> None:
        """导入并实例化。/ Import and instantiate."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.concurrent_generation_material_slice_template_cache import (
            ConcurrentGenerationMaterialSliceTemplateCache,
        )

        obj = ConcurrentGenerationMaterialSliceTemplateCache()
        assert obj is not None

    def test_costar_filler(self) -> None:
        """导入并实例化。/ Import and instantiate."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.costar_filler import (
            CostarFiller,
        )

        obj = CostarFiller()
        assert obj is not None

    def test_generation_material_slice_template_cache(self) -> None:
        """导入并实例化。/ Import and instantiate."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_material_slice_template_cache import (
            GenerationMaterialSliceTemplateCache,
        )

        obj = GenerationMaterialSliceTemplateCache()
        assert obj is not None

    def test_generation_material_width_index_cache(self) -> None:
        """导入并实例化。/ Import and instantiate."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_material_width_index_cache import (
            GenerationMaterialWidthIndexCache,
        )

        obj = GenerationMaterialWidthIndexCache()
        assert obj is not None

    def test_generation_material_width_range_key(self) -> None:
        """导入并实例化。/ Import and instantiate."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_material_width_range_key import (
            GenerationMaterialWidthRangeKey,
        )

        obj = GenerationMaterialWidthRangeKey()
        assert obj is not None

    def test_generation_quantity_cache(self) -> None:
        """导入并实例化。/ Import and instantiate."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_quantity_cache import (
            GenerationQuantityCache,
        )

        obj = GenerationQuantityCache()
        assert obj is not None

    def test_generation_slice_template_cache(self) -> None:
        """导入并实例化。/ Import and instantiate."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_slice_template_cache import (
            GenerationSliceTemplateCache,
        )

        obj = GenerationSliceTemplateCache()
        assert obj is not None

    def test_generation_template_reuse(self) -> None:
        """导入并实例化。/ Import and instantiate."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_template_reuse import (
            GenerationTemplateReuse,
        )

        obj = GenerationTemplateReuse()
        assert obj is not None

    def test_generation_width_index(self) -> None:
        """导入并实例化。/ Import and instantiate."""
        from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.generation_width_index import (
            GenerationWidthIndex,
        )

        obj = GenerationWidthIndex()
        assert obj is not None


# ============================================================
# Produce aggregation
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

        # Create a mock produce-like object
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
