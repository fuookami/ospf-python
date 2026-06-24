"""二次四元组转储构建器 / Quadratic tetrad dump builders.

为二次规划模型提供导出功能。
Provides export functionality for quadratic
programming models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.model.intermediate.quadratic_tetrad_model import (
        QuadraticTetradModel,
    )


class QuadraticTetradDumpBuilders:
    """二次四元组转储构建器 / Quadratic tetrad dump builders.

    将二次四元组中间模型转换为 QP 格式文本。
    Converts quadratic tetrad intermediate models to QP
    format text.

    Methods:
        build_qp: 构建 QP 格式文本 / Build QP format text.
    """

    @staticmethod
    def build_qp(model: QuadraticTetradModel) -> str:
        """构建 QP 格式文本 / Build QP format text.

        Args:
            model: 二次四元组模型 / The quadratic tetrad model.

        Returns:
            QP 格式字符串 / The QP format string.
        """
        lines: list[str] = []
        lines.append(f"\\* {model.name} *\\")
        lines.append("")
        lines.append("Subject To")
        for name, row in model.linear_constraints.items():
            coeff_str = " + ".join(f"{c} {v}" for v, c in row.items())
            lines.append(f"  {name}: {coeff_str}")
        lines.append("End")
        return "\n".join(lines)
