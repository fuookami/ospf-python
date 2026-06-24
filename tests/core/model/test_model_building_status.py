"""ModelBuildingStatus 测试。

测试模型构建状态枚举的定义和值。
Tests ModelBuildingStatus enum definition and values.
"""

from __future__ import annotations

from ospf_python.core.model.basic.model_building_status import (
    ModelBuildingStatus,
)


class TestModelBuildingStatus:
    """枚举测试 / Enum tests."""

    def test_success_value(self) -> None:
        """SUCCESS 值为 0。/ SUCCESS is 0."""
        assert ModelBuildingStatus.SUCCESS.value == 0

    def test_infeasible_value(self) -> None:
        """INFEASIBLE 值为 2。/ INFEASIBLE is 2."""
        assert ModelBuildingStatus.INFEASIBLE.value == 2
