"""AbstractVariableItem 抽象基类测试。

测试抽象变量项基类的接口和行为。
Tests AbstractVariableItem ABC interface and behaviour.
"""

from __future__ import annotations

import pytest

from ospf_python.core.variable.abstract_variable_item import (
    AbstractVariableItem,
)
from ospf_python.core.variable.type import VariableType


class TestAbstractVariableItemABC:
    """抽象基类测试 / ABC tests."""

    def test_is_dataclass(self) -> None:
        """是数据类。/ Is a dataclass."""
        import dataclasses

        assert dataclasses.is_dataclass(AbstractVariableItem)

    def test_has_required_fields(self) -> None:
        """具有必需字段。/ Has required fields."""
        import dataclasses

        fields = {f.name for f in dataclasses.fields(AbstractVariableItem)}
        assert "name" in fields
        assert "type" in fields
        assert "index" in fields

    def test_str_format(self) -> None:
        """字符串格式正确。/ String format correct."""

        class Concrete(AbstractVariableItem):
            pass

        v = Concrete(
            name="x",
            type=VariableType.CONTINUOUS,
            index=5,
        )
        assert str(v) == "x[5](continuous)"

    def test_subclass_can_instantiate(self) -> None:
        """子类可以实例化。/ Subclass can instantiate."""

        class Concrete(AbstractVariableItem):
            pass

        v = Concrete(
            name="x",
            type=VariableType.CONTINUOUS,
            index=0,
        )
        assert v.name == "x"
        assert v.index == 0

    def test_frozen(self) -> None:
        """不可变。/ Frozen."""

        class Concrete(AbstractVariableItem):
            pass

        v = Concrete(
            name="x",
            type=VariableType.CONTINUOUS,
            index=0,
        )
        with pytest.raises(AttributeError):
            v.name = "changed"  # type: ignore[misc]

    def test_subclass_with_integer_type(self) -> None:
        """子类使用整数类型。/ Subclass with integer type."""

        class Concrete(AbstractVariableItem):
            pass

        v = Concrete(
            name="y",
            type=VariableType.INTEGER,
            index=1,
        )
        assert v.type is VariableType.INTEGER
