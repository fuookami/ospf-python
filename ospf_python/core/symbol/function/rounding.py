"""四舍五入函数符号 / Rounding function symbol."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Rounding(FunctionSymbol):
    """四舍五入 / Rounding.

    四舍五入函数符号实现。
    Rounding function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        decimals: 小数位 / Decimal places.
    """

    name: str = "Rounding"
    """函数符号名称 / Function symbol name."""

    decimals: int = 0
    """小数位 / Decimal places."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        按十进制"四舍五入"（逢五远离零）取值，而不是 Python ``round`` 的银行家舍入。
        ``round(0.5) == 0``、``round(2.5) == 2``，与本类文档所写的四舍五入不符。
        Rounds half away from zero in the decimal sense rather than using Python ``round``'s
        banker's rounding: ``round(0.5) == 0`` and ``round(2.5) == 2`` contradict the
        half-up semantics this class documents.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args:
            return 0.0
        # 用最短十进制表示定位，再按 ROUND_HALF_UP 定点：这样 1.005 得 1.01，
        # 而不是先乘 100 得到 100.49999999999999 再取整。
        # Anchor on the shortest decimal representation, then quantise with ROUND_HALF_UP, so
        # 1.005 yields 1.01 instead of multiplying by 100 into 100.49999999999999 first.
        return float(
            Decimal(repr(float(args[0]))).quantize(
                Decimal(1).scaleb(-self.decimals), rounding=ROUND_HALF_UP
            )
        )

    @staticmethod
    def create(
        *,
        decimals: int = 0,
    ) -> Rounding:
        """创建四舍五入 / Create Rounding.

        Args:
            decimals: 小数位 / Decimal places.

        Returns:
            四舍五入实例 / Rounding instance.
        """
        return Rounding(decimals=decimals)
