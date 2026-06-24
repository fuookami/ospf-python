"""元模型导出支持 / Meta model export support.

为元模型提供导出功能支持。
Provides export functionality support for meta models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.model.basic.model_file_format import (
        ModelFileFormat,
    )
    from ospf_python.core.model.mechanism.meta_model import (
        MetaModel,
    )


class MetaModelExportSupport:
    """元模型导出支持 / Meta model export support.

    辅助将元模型导出为中间模型或文件格式。
    Assists in exporting meta models to intermediate models
    or file formats.

    Methods:
        export: 导出模型 / Export the model.
    """

    @staticmethod
    def export(
        model: MetaModel,
        format_: ModelFileFormat,
    ) -> str:
        """导出模型为文本 / Export model as text.

        Args:
            model: 元模型 / The meta model.
            format_: 目标格式 / The target format.

        Returns:
            导出的文本内容 / The exported text content.
        """
        lines: list[str] = []
        lines.append(f"Model: {model.name}")
        lines.append(f"Variables: {len(model.variables)}")
        lines.append(f"Constraints: {len(model.constraints)}")
        lines.append(f"Objectives: {len(model.objectives)}")
        return "\n".join(lines)
