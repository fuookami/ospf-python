"""Waste minimization tests.

Test waste model and minimization config.
测试废料模型和最小化配置。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.application.service.waste_minimization_config import (
    WasteMinimizationConfig,
)
from ospf_python.framework.csp1d.domain.wasting_minimization.model.waste_model import (
    WasteModel,
)
from ospf_python.framework.csp1d.domain.wasting_minimization.waste_aggregation import (
    WasteAggregation,
)
from ospf_python.framework.csp1d.domain.wasting_minimization.wasting_minimization_context import (
    WastingMinimizationContext,
)


class TestWasteModel:
    """WasteModel frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        assert WasteModel() is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        m = WasteModel()
        with pytest.raises(AttributeError):
            m.foo = "bar"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Two default instances are equal. / 两个默认实例相等。"""
        assert WasteModel() == WasteModel()


class TestWasteAggregation:
    """WasteAggregation frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        assert WasteAggregation() is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        a = WasteAggregation()
        with pytest.raises(AttributeError):
            a.foo = "bar"  # type: ignore[misc]


class TestWastingMinimizationContext:
    """WastingMinimizationContext frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        assert WastingMinimizationContext() is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        ctx = WastingMinimizationContext()
        with pytest.raises(AttributeError):
            ctx.foo = "bar"  # type: ignore[misc]


class TestWasteMinimizationConfig:
    """WasteMinimizationConfig frozen dataclass tests."""

    def test_defaults(self) -> None:
        """Default values. / 默认值。"""
        c = WasteMinimizationConfig()
        assert c.enabled is True
        assert c.weight == 1.0
        assert c.max_iterations == 100
        assert c.tolerance == 1e-6

    def test_custom_values(self) -> None:
        """Custom values. / 自定义值。"""
        c = WasteMinimizationConfig(enabled=False, weight=2.0, max_iterations=50)
        assert c.enabled is False
        assert c.weight == 2.0

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        c = WasteMinimizationConfig()
        with pytest.raises(AttributeError):
            c.enabled = False  # type: ignore[misc]
