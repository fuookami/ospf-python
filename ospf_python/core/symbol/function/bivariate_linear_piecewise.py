"""双变量线性分段函数符号 / BivariateLinearPiecewise function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class BivariateLinearPiecewise(FunctionSymbol):
    """双变量线性分段 / BivariateLinearPiecewise.

    双变量线性分段函数符号实现。
    BivariateLinearPiecewise function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        slope_x: X斜率 / X slope.
        slope_y: Y斜率 / Y slope.
        intercept: 截距 / Intercept.
    """

    name: str = "BivariateLinearPiecewise"
    """函数符号名称 / Function symbol name."""

    slope_x: float = 1.0
    """X斜率 / X slope."""

    slope_y: float = 1.0
    """Y斜率 / Y slope."""

    intercept: float = 0.0
    """截距 / Intercept."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if len(args) < 2:
            return 0.0
        return self.slope_x * args[0] + self.slope_y * args[1] + self.intercept

    @staticmethod
    def create(
        *,
        slope_x: float = 1.0,
        slope_y: float = 1.0,
        intercept: float = 0.0,
    ) -> BivariateLinearPiecewise:
        """创建双变量线性分段 / Create BivariateLinearPiecewise.

        Args:
            slope_x: X斜率 / X slope.
            slope_y: Y斜率 / Y slope.
            intercept: 截距 / Intercept.

        Returns:
            双变量线性分段实例 / BivariateLinearPiecewise instance.
        """
        return BivariateLinearPiecewise(
            slope_x=slope_x,
            slope_y=slope_y,
            intercept=intercept,
        )
