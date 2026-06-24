"""线性三元组转储构建器 / Linear triad dump builders.

为线性规划模型提供 LP 格式导出功能。
Provides LP format export functionality for
linear programming models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.model.intermediate.linear_triad_model import (
        LinearTriadModel,
    )


class LinearTriadDumpBuilders:
    """线性三元组转储构建器 / Linear triad dump builders.

    将线性三元组中间模型转换为 LP 或 MPS 格式文本。
    Converts linear triad intermediate models to LP or MPS
    format text.

    Methods:
        build_lp: 构建 LP 格式文本 / Build LP format text.
        build_mps: 构建 MPS 格式文本 / Build MPS format text.
    """

    @staticmethod
    def build_lp(model: LinearTriadModel) -> str:
        """构建 LP 格式文本 / Build LP format text.

        Args:
            model: 线性三元组模型 / The linear triad model.

        Returns:
            LP 格式字符串 / The LP format string.
        """
        lines: list[str] = []
        lines.append(f"\\* {model.name} *\\")
        lines.append("")
        lines.append("Subject To")
        for name, row in model.constraints.items():
            coeff_str = " + ".join(f"{c} {v}" for v, c in row.items())
            lines.append(f"  {name}: {coeff_str}")
        lines.append("End")
        return "\n".join(lines)

    @staticmethod
    def build_mps(model: LinearTriadModel) -> str:
        """构建 MPS 格式文本 / Build MPS format text.

        Args:
            model: 线性三元组模型 / The linear triad model.

        Returns:
            MPS 格式字符串 / The MPS format string.
        """
        lines: list[str] = []
        lines.append(f"NAME          {model.name}")
        lines.append("ROWS")
        lines.append("COLUMNS")
        lines.append("RHS")
        lines.append("ENDATA")
        return "\n".join(lines)
