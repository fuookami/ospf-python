"""Length assignment tests.

Test length assignment aggregation and context.
测试长度分配聚合和上下文。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.domain.length_assignment.length_aggregation import (
    LengthAggregation,
)
from ospf_python.framework.csp1d.domain.length_assignment.length_assignment_context import (
    LengthAssignmentContext,
)
from ospf_python.framework.csp1d.domain.length_assignment.model.length_assignment_modeling_config import (
    LengthAssignmentModelingConfig,
)


class TestLengthAssignmentModelingConfig:
    """LengthAssignmentModelingConfig tests."""

    def test_defaults(self) -> None:
        """Default values. / 默认值。"""
        c = LengthAssignmentModelingConfig()
        assert c.min_length == 0.0
        assert c.max_length == float("inf")
        assert c.length_step == 1.0
        assert c.allow_shortfall is False
        assert c.shortfall_penalty == 1000.0
        assert c.waste_penalty == 1.0

    def test_default_factory(self) -> None:
        """Default factory method. / 默认工厂方法。"""
        c = LengthAssignmentModelingConfig.default()
        assert c.min_length == 0.0

    def test_with_length_range(self) -> None:
        """With length range factory. / 带长度范围工厂。"""
        c = LengthAssignmentModelingConfig.with_length_range(
            min_length=10.0, max_length=500.0
        )
        assert c.min_length == 10.0
        assert c.max_length == 500.0

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        c = LengthAssignmentModelingConfig()
        with pytest.raises(AttributeError):
            c.min_length = 5.0  # type: ignore[misc]


class TestLengthAggregation:
    """LengthAggregation frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with defaults. / 默认创建。"""
        a = LengthAggregation()
        assert a.model is not None
        assert a.config is not None
        assert a.shadow_prices == ()

    def test_with_shadow_prices(self) -> None:
        """Create new aggregation with shadow prices. / 带影子价格创建。"""
        a = LengthAggregation()
        b = a.with_shadow_prices(prices={"P1": 5.0, "P2": 3.0})
        assert b.get_shadow_price("P1") == 5.0
        assert b.get_shadow_price("P2") == 3.0
        # Original unchanged
        assert a.get_shadow_price("P1") == 0.0

    def test_get_shadow_price_missing(self) -> None:
        """Missing product returns 0.0. / 缺失产品返回 0.0。"""
        a = LengthAggregation()
        assert a.get_shadow_price("no_such") == 0.0

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        a = LengthAggregation()
        with pytest.raises(AttributeError):
            a.shadow_prices = ()  # type: ignore[misc]


class TestLengthAssignmentContext:
    """LengthAssignmentContext frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with defaults. / 默认创建。"""
        ctx = LengthAssignmentContext()
        assert ctx.config is not None
        assert ctx.constraint_pipeline is not None
        assert ctx.objective_pipeline is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        ctx = LengthAssignmentContext()
        with pytest.raises(AttributeError):
            ctx.config = LengthAssignmentModelingConfig()  # type: ignore[misc]
