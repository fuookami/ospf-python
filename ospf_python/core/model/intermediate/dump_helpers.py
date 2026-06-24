"""转储辅助工具 / Dump helper utilities.

提供模型导出过程中的辅助函数。
Provides helper functions for model export processes.
"""

from __future__ import annotations


class DumpHelpers:
    """转储辅助工具类 / Dump helper utility class.

    集中管理模型导出过程中使用的通用工具方法。
    Centralizes common utility methods used during
    model export processes.

    Methods:
        format_coefficient: 格式化系数值 / Format a coefficient.
        format_sign: 格式化约束符号 / Format a constraint sign.
    """

    @staticmethod
    def format_coefficient(value: float) -> str:
        """格式化系数值 / Format a coefficient value.

        Args:
            value: 系数值 / The coefficient value.

        Returns:
            格式化后的字符串 / The formatted string.
        """
        if value == int(value):
            return str(int(value))
        return f"{value:.6g}"

    @staticmethod
    def format_sign(sign: str) -> str:
        """格式化约束符号 / Format a constraint sign.

        Args:
            sign: 约束符号 / The constraint sign.

        Returns:
            格式化后的符号 / The formatted sign.
        """
        mapping: dict[str, str] = {
            "<=": "<=",
            ">=": ">=",
            "==": "=",
        }
        return mapping.get(sign, sign)
