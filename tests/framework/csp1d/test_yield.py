"""Yield tests.

Test yield model and related context.
测试产出模型和相关上下文。

Note: the source package is named 'yield' which is a Python
keyword, so we use importlib to import from it.
注意：源包名为 'yield'，这是 Python 关键字，
因此使用 importlib 导入。
"""

from __future__ import annotations

import importlib

import pytest

# importlib workaround for 'yield' keyword in path
_YieldModel = importlib.import_module(
    "ospf_python.framework.csp1d.domain.yield.model.yield_model",
).YieldModel
_YieldModelingConfig = importlib.import_module(
    "ospf_python.framework.csp1d.domain.yield.model.yield_modeling_config",
).YieldModelingConfig
_YieldAggregation = importlib.import_module(
    "ospf_python.framework.csp1d.domain.yield.yield_aggregation",
).YieldAggregation
_YieldContext = importlib.import_module(
    "ospf_python.framework.csp1d.domain.yield.yield_context",
).YieldContext


class TestYieldModel:
    """YieldModel frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        assert _YieldModel() is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        m = _YieldModel()
        with pytest.raises(AttributeError):
            m.foo = "bar"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Two default instances are equal. / 两个默认实例相等。"""
        assert _YieldModel() == _YieldModel()

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        assert hash(_YieldModel()) is not None


class TestYieldModelingConfig:
    """YieldModelingConfig frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        assert _YieldModelingConfig() is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        c = _YieldModelingConfig()
        with pytest.raises(AttributeError):
            c.foo = "bar"  # type: ignore[misc]


class TestYieldAggregation:
    """YieldAggregation frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        assert _YieldAggregation() is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        a = _YieldAggregation()
        with pytest.raises(AttributeError):
            a.foo = "bar"  # type: ignore[misc]


class TestYieldContext:
    """YieldContext frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        assert _YieldContext() is not None

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        ctx = _YieldContext()
        with pytest.raises(AttributeError):
            ctx.foo = "bar"  # type: ignore[misc]
