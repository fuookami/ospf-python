"""机制模型 Flt64 转换 / Mechanism model Flt64 conversion.

将机制模型中的值转换为 64 位浮点表示。
Converts values in mechanism models to 64-bit
floating-point representation.
"""

from __future__ import annotations


class MechanismModelFlt64Conversion:
    """机制模型 Flt64 转换器 / Mechanism model Flt64 converter.

    确保模型中所有数值为 64 位浮点类型。
    Ensures all numerical values in the model are 64-bit
    floating-point type.

    Methods:
        convert_value: 转换单个值 / Convert a single value.
        convert_coefficients: 转换系数字典 / Convert a
            coefficient dictionary.
    """

    @staticmethod
    def convert_value(value: object) -> float:
        """转换为 Flt64 / Convert to Flt64.

        Args:
            value: 待转换的值 / The value to convert.

        Returns:
            64 位浮点值 / The 64-bit float value.
        """
        return float(value)  # type: ignore[arg-type]

    @staticmethod
    def convert_coefficients(
        coefficients: dict[str, float],
    ) -> dict[str, float]:
        """转换系数字典 / Convert coefficient dictionary.

        Args:
            coefficients: 原始系数 / The original coefficients.

        Returns:
            转换后的系数 / The converted coefficients.
        """
        return {k: float(v) for k, v in coefficients.items()}
