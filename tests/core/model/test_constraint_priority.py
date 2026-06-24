"""ConstraintPriority 测试。

测试约束优先级枚举的定义和值。
Tests ConstraintPriority enum definition and values.
"""

from __future__ import annotations

from ospf_python.core.model.basic.constraint_priority import (
    ConstraintPriority,
)


class TestConstraintPriority:
    """枚举测试 / Enum tests."""

    def test_required_value(self) -> None:
        """REQUIRED 值为 0。/ REQUIRED is 0."""
        assert ConstraintPriority.REQUIRED.value == 0

    def test_preferred_value(self) -> None:
        """PREFERRED 值为 1。/ PREFERRED is 1."""
        assert ConstraintPriority.PREFERRED.value == 1

    def test_optional_value(self) -> None:
        """OPTIONAL 值为 2。/ OPTIONAL is 2."""
        assert ConstraintPriority.OPTIONAL.value == 2

    def test_member_count(self) -> None:
        """共有 3 个成员。/ Has 3 members."""
        assert len(ConstraintPriority) == 3
