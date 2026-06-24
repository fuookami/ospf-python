"""MetaModelExportSupport 测试。

测试元模型导出支持的导出方法。
Tests MetaModelExportSupport export method.
"""

from __future__ import annotations

from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.model.mechanism.meta_model_export_support import (
    MetaModelExportSupport,
)


class TestMetaModelExportSupport:
    """元模型导出支持测试 / MetaModelExportSupport tests."""

    def test_export_contains_model_name(self) -> None:
        """导出包含模型名称。/ Export contains model name."""
        m = MetaModel(name="test_model")
        result = MetaModelExportSupport.export(m, "lp")
        assert "test_model" in result

    def test_export_contains_variable_count(self) -> None:
        """导出包含变量数量。/ Export contains variable count."""
        m = MetaModel()
        m.register_variable("x1", object())
        m.register_variable("x2", object())
        result = MetaModelExportSupport.export(m, "lp")
        assert "Variables: 2" in result

    def test_export_contains_constraint_count(self) -> None:
        """导出包含约束数量。/ Export contains constraint count."""
        m = MetaModel()
        m.register_constraint("c1", object())
        result = MetaModelExportSupport.export(m, "lp")
        assert "Constraints: 1" in result

    def test_export_contains_objective_count(self) -> None:
        """导出包含目标数量。/ Export contains objective count."""
        m = MetaModel()
        m.register_objective("obj1", object())
        result = MetaModelExportSupport.export(m, "lp")
        assert "Objectives: 1" in result

    def test_export_empty_model(self) -> None:
        """导出空模型。/ Export empty model."""
        m = MetaModel()
        result = MetaModelExportSupport.export(m, "lp")
        assert "Variables: 0" in result
        assert "Constraints: 0" in result
        assert "Objectives: 0" in result

    def test_export_multiline(self) -> None:
        """导出为多行文本。/ Export is multiline text."""
        m = MetaModel(name="m")
        result = MetaModelExportSupport.export(m, "lp")
        lines = result.strip().split("\n")
        assert len(lines) == 4
