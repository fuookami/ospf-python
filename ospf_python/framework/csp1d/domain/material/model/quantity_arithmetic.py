"""CSP1D 数量算术运算 / CSP1D quantity arithmetic."""

from __future__ import annotations

from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok, Result


class QuantityArithmetic:
    """数量算术工具 / Quantity arithmetic utility.

    提供安全的数量加减乘运算，避免负数和溢出。
    Provides safe quantity add/subtract/multiply
    operations, avoiding negatives and overflow.
    """

    @staticmethod
    def add(
        lhs: int,
        rhs: int,
    ) -> Result[int, str, object]:
        """安全加法 / Safe addition.

        Args:
            lhs: 左操作数 / Left operand.
            rhs: 右操作数 / Right operand.

        Returns:
            加法结果 / Addition result.
        """
        result = lhs + rhs
        if result < 0:
            return Failed(
                ErrorCode.ILLEGAL_ARGUMENT,
                f"加法结果为负数: {lhs} + {rhs} / "
                f"Addition result is negative: {lhs} + {rhs}",
            )
        return Ok(result)

    @staticmethod
    def subtract(
        lhs: int,
        rhs: int,
    ) -> Result[int, str, object]:
        """安全减法 / Safe subtraction.

        Args:
            lhs: 被减数 / Minuend.
            rhs: 减数 / Subtrahend.

        Returns:
            减法结果 / Subtraction result.
        """
        result = lhs - rhs
        if result < 0:
            return Failed(
                ErrorCode.ILLEGAL_ARGUMENT,
                f"减法结果为负数: {lhs} - {rhs} / "
                f"Subtraction result is negative: {lhs} - {rhs}",
            )
        return Ok(result)

    @staticmethod
    def multiply(
        lhs: int,
        rhs: int,
    ) -> Result[int, str, object]:
        """安全乘法 / Safe multiplication.

        Args:
            lhs: 左操作数 / Left operand.
            rhs: 右操作数 / Right operand.

        Returns:
            乘法结果 / Multiplication result.
        """
        result = lhs * rhs
        if result < 0:
            return Failed(
                ErrorCode.ILLEGAL_ARGUMENT,
                f"乘法结果为负数: {lhs} * {rhs} / "
                f"Multiplication result is negative: {lhs} * {rhs}",
            )
        return Ok(result)
