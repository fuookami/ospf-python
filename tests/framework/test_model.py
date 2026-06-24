"""Tests for framework model (Pipeline, ShadowPrice).

框架模型测试。
"""

from __future__ import annotations

import abc

import pytest

from ospf_python.framework.model.pipeline import Pipeline
from ospf_python.framework.model.shadow_price import ShadowPrice

# -- Pipeline --------------------------------------------------------


class TestPipelineExtra:
    """Test Pipeline edge cases."""

    def test_is_abstract(self) -> None:
        """是抽象类 / Is abstract class."""
        assert issubclass(Pipeline, abc.ABC)

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate directly."""
        with pytest.raises(TypeError):
            Pipeline()  # type: ignore[abstract]

    def test_has_execute_method(self) -> None:
        """有 execute 方法 / Has execute method."""
        assert hasattr(Pipeline, "execute")

    def test_has_reset_method(self) -> None:
        """有 reset 方法 / Has reset method."""
        assert hasattr(Pipeline, "reset")

    def test_concrete_subclass_works(self) -> None:
        """具体子类可用 / Concrete subclass works."""

        class MyPipeline(Pipeline[int, str]):
            def execute(self, input_data: int) -> str:
                return str(input_data)

            def reset(self) -> None:
                pass

        p = MyPipeline()
        assert p.execute(42) == "42"


# -- ShadowPrice -----------------------------------------------------


class TestShadowPriceExtra:
    """Test ShadowPrice edge cases."""

    def test_positive_value(self) -> None:
        """正值 / Positive value."""
        sp = ShadowPrice(constraint_name="c1", value=1.5)
        assert sp.value == pytest.approx(1.5)

    def test_negative_value(self) -> None:
        """负值 / Negative value."""
        sp = ShadowPrice(constraint_name="c1", value=-2.5)
        assert sp.value == pytest.approx(-2.5)

    def test_zero_value(self) -> None:
        """零值 / Zero value."""
        sp = ShadowPrice(constraint_name="c1", value=0.0)
        assert sp.value == pytest.approx(0.0)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        sp = ShadowPrice(constraint_name="c1", value=1.0)
        with pytest.raises(AttributeError):
            sp.value = 2.0  # type: ignore[misc]

    def test_equality(self) -> None:
        """相等性 / Equality."""
        a = ShadowPrice(constraint_name="c1", value=1.0)
        b = ShadowPrice(constraint_name="c1", value=1.0)
        assert a == b

    def test_inequality_name(self) -> None:
        """名称不同不相等 / Different name not equal."""
        a = ShadowPrice(constraint_name="c1", value=1.0)
        b = ShadowPrice(constraint_name="c2", value=1.0)
        assert a != b

    def test_large_value(self) -> None:
        """大值 / Large value."""
        sp = ShadowPrice(constraint_name="c1", value=1e15)
        assert sp.value == pytest.approx(1e15)
