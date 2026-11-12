"""ResourceShadowPriceMap model tests / 资源影子价格映射模型测试.

Exercises ResourceShadowPriceMap queries and builder methods.
覆盖 ResourceShadowPriceMap 的查询和构建方法。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_shadow_price_map import (
    ResourceShadowPriceMap,
)


class TestResourceShadowPriceMap:
    """ResourceShadowPriceMap tests."""

    def test_get_price_default(self) -> None:
        """Default price is 0.0. / 默认价格为 0.0."""
        m = ResourceShadowPriceMap()
        assert m.get_price("c1") == pytest.approx(0.0)

    def test_with_price(self) -> None:
        """Add price entry. / 添加价格条目."""
        m = ResourceShadowPriceMap()
        m2 = m.with_price(constraint_name="c1", price=3.5)
        assert m2.get_price("c1") == pytest.approx(3.5)
        assert m.get_price("c1") == pytest.approx(0.0)

    def test_get_resource_price_default(self) -> None:
        """Default resource price is 0.0. / 默认资源价格为 0.0."""
        m = ResourceShadowPriceMap()
        assert m.get_resource_price(
            resource_key="r1",
            window_start=0.0,
            window_end=10.0,
        ) == pytest.approx(0.0)

    def test_with_resource_price(self) -> None:
        """Add resource price entry. / 添加资源价格条目."""
        m = ResourceShadowPriceMap()
        m2 = m.with_resource_price(
            resource_key="r1",
            window_start=0.0,
            window_end=10.0,
            price=5.0,
        )
        assert m2.get_resource_price(
            resource_key="r1",
            window_start=0.0,
            window_end=10.0,
        ) == pytest.approx(5.0)

    def test_total_pricing_cost(self) -> None:
        """Total pricing cost computation. / 总定价成本计算."""
        m = ResourceShadowPriceMap()
        m = m.with_resource_price(
            resource_key="r1",
            window_start=0.0,
            window_end=10.0,
            price=2.0,
        )
        m = m.with_resource_price(
            resource_key="r2",
            window_start=0.0,
            window_end=10.0,
            price=3.0,
        )
        demands = (
            ("r1", 0.0, 10.0, 5.0),
            ("r2", 0.0, 10.0, 2.0),
        )
        cost = m.total_pricing_cost(demands)
        # 2.0 * 5.0 + 3.0 * 2.0 = 16.0
        assert cost == pytest.approx(16.0)

    def test_total_pricing_cost_missing_resource(self) -> None:
        """Missing resource contributes 0. / 缺失资源贡献 0."""
        m = ResourceShadowPriceMap()
        demands = (("r1", 0.0, 10.0, 5.0),)
        assert m.total_pricing_cost(demands) == pytest.approx(0.0)

    def test_frozen(self) -> None:
        """Immutable. / 不可变."""
        m = ResourceShadowPriceMap()
        with pytest.raises(AttributeError):
            m.prices = ()  # type: ignore[misc]


def test_price_lookup_tolerates_window_values_that_differ_only_in_bits() -> None:
    """同值不同位的时间窗必须命中，否则定价成本静默归零。

    按 0.3 登记、按 0.1 + 0.2 查询时，精确元组相等会 miss 返回 0.0，
    列生成会以为所有候选列都零成本。
    Windows equal in value but not in bits must match; under exact tuple equality a 0.3
    registration queried as 0.1 + 0.2 misses and returns 0.0, so column generation treats
    every candidate as free.
    """
    mapping = ResourceShadowPriceMap().with_resource_price(
        resource_key="M1", window_start=0.3, window_end=1.3, price=2.5
    )
    assert mapping.get_resource_price(
        resource_key="M1", window_start=0.1 + 0.2, window_end=1.3
    ) == pytest.approx(2.5)
    assert mapping.get_resource_price(
        resource_key="R9", window_start=0.3, window_end=1.3
    ) == pytest.approx(0.0)
