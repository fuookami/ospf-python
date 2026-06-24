"""ModelBuildingStage 测试。

测试模型构建阶段枚举的定义和值。
Tests ModelBuildingStage enum definition and values.
"""

from __future__ import annotations

from ospf_python.core.model.basic.model_building_stage import (
    ModelBuildingStage,
)


class TestModelBuildingStage:
    """枚举测试 / Enum tests."""

    def test_init_value(self) -> None:
        """INIT 值为 0。/ INIT is 0."""
        assert ModelBuildingStage.INIT.value == 0

    def test_extracting_value(self) -> None:
        """EXTRACTING 值为 4。/ EXTRACTING is 4."""
        assert ModelBuildingStage.EXTRACTING.value == 4
