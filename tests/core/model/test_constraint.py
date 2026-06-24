"""Constraint 测试。

测试约束的创建和不可变性。
Tests Constraint creation and immutability.
"""

from __future__ import annotations

import pytest

from ospf_python.core.model.basic.constraint_sign import (
    ConstraintSign,
)
from ospf_python.core.model.mechanism.constraint import Constraint


class TestConstraint:
    """冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        c = Constraint(
            name="c1",
            expr=None,
            sign=ConstraintSign.LE,
            rhs=10.0,
        )
        with pytest.raises(AttributeError):
            c.rhs = 20.0  # type: ignore[misc]

    def test_values(self) -> None:
        """正确存储值。/ Correctly stores values."""
        c = Constraint(
            name="c2",
            expr="expr",
            sign=ConstraintSign.GE,
            rhs=5.0,
        )
        assert c.name == "c2"
        assert c.sign == ConstraintSign.GE
        assert c.rhs == 5.0
