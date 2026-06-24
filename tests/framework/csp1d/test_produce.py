"""Produce tests.

Test produce model and related context.
测试生产模型和相关上下文。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.domain.produce.model.csp1d_aggregation import (
    Csp1dAggregation,
)
from ospf_python.framework.csp1d.domain.produce.model.csp1d_model_context import (
    Csp1dModelContext,
)
from ospf_python.framework.csp1d.domain.produce.model.produce import (
    Produce,
)
from ospf_python.framework.csp1d.domain.produce.produce_aggregation import (
    ProduceAggregation,
)


class TestProduce:
    """Produce frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        p = Produce()
        assert p is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        p = Produce()
        with pytest.raises(AttributeError):
            p.foo = "bar"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Two default instances are equal. / 两个默认实例相等。"""
        assert Produce() == Produce()

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        assert hash(Produce()) is not None


class TestCsp1dAggregation:
    """Csp1dAggregation frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        assert Csp1dAggregation() is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        a = Csp1dAggregation()
        with pytest.raises(AttributeError):
            a.foo = "bar"  # type: ignore[misc]


class TestCsp1dModelContext:
    """Csp1dModelContext frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        assert Csp1dModelContext() is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        ctx = Csp1dModelContext()
        with pytest.raises(AttributeError):
            ctx.foo = "bar"  # type: ignore[misc]


class TestProduceAggregation:
    """ProduceAggregation frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        assert ProduceAggregation() is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        a = ProduceAggregation()
        with pytest.raises(AttributeError):
            a.foo = "bar"  # type: ignore[misc]
