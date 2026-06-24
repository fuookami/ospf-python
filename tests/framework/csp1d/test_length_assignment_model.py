"""Length assignment model tests.

Test LengthAssignmentModel creation.
测试长度分配模型创建。
"""

from __future__ import annotations

from ospf_python.framework.csp1d.domain.length_assignment.model.length_assignment_model import (
    LengthAssignmentModel,
)


class TestLengthAssignmentModel:
    """LengthAssignmentModel frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create a default instance. / 创建默认实例。"""
        m = LengthAssignmentModel()
        assert m is not None

    def test_is_dataclass(self) -> None:
        """Instance is a dataclass. / 实例是数据类。"""
        import dataclasses

        assert dataclasses.is_dataclass(LengthAssignmentModel())
