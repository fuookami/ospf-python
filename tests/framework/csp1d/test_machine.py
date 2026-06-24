"""Machine tests.

Test Machine model creation, fields, and immutability.
测试机器模型创建、字段和不可变性。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.domain.material.model.machine import (
    Machine,
)


class TestMachine:
    """Machine frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        m = Machine(name="Cutter-1", max_width=200.0, cut_loss=2.0)
        assert m.name == "Cutter-1"
        assert m.max_width == 200.0
        assert m.cut_loss == 2.0

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        m = Machine(name="Cutter-1", max_width=200.0, cut_loss=2.0)
        with pytest.raises(AttributeError):
            m.name = "Cutter-2"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Same field values yield equality. / 相同字段值相等。"""
        a = Machine(name="Cutter-1", max_width=200.0, cut_loss=2.0)
        b = Machine(name="Cutter-1", max_width=200.0, cut_loss=2.0)
        assert a == b

    def test_inequality(self) -> None:
        """Different names yield inequality. / 不同名称不等。"""
        a = Machine(name="Cutter-1", max_width=200.0, cut_loss=2.0)
        b = Machine(name="Cutter-2", max_width=200.0, cut_loss=2.0)
        assert a != b

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        m = Machine(name="Cutter-1", max_width=200.0, cut_loss=2.0)
        assert hash(m) is not None

    def test_is_dataclass(self) -> None:
        """Instance is a dataclass. / 实例是数据类。"""
        import dataclasses

        m = Machine(name="Cutter-1", max_width=200.0, cut_loss=2.0)
        assert dataclasses.is_dataclass(m)
