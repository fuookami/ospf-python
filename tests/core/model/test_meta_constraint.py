"""MetaConstraint 测试。

测试元约束的创建和默认优先级。
Tests MetaConstraint creation and default priority.
"""

from __future__ import annotations

import pytest

from ospf_python.core.model.basic.constraint_priority import (
    ConstraintPriority,
)
from ospf_python.core.model.basic.constraint_sign import (
    ConstraintSign,
)
from ospf_python.core.model.mechanism.meta_constraint import (
    MetaConstraint,
)


class TestMetaConstraint:
    """冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        mc = MetaConstraint(
            name="mc1",
            expr=None,
            sign=ConstraintSign.LE,
            rhs=10.0,
        )
        with pytest.raises(AttributeError):
            mc.name = "new"  # type: ignore[misc]

    def test_default_priority(self) -> None:
        """默认优先级为 REQUIRED。/ Default priority is REQUIRED."""
        mc = MetaConstraint(
            name="mc1",
            expr=None,
            sign=ConstraintSign.LE,
            rhs=10.0,
        )
        assert mc.priority == ConstraintPriority.REQUIRED
