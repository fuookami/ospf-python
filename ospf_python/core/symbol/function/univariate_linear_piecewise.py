"""单变量线性分段函数符号 / UnivariateLinearPiecewise function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class UnivariateLinearPiecewise(FunctionSymbol):
    """单变量线性分段 / UnivariateLinearPiecewise.

    单变量线性分段函数符号实现。
    UnivariateLinearPiecewise function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        slope: 斜率 / Slope.
        intercept: 截距 / Intercept.
    """

    name: str = "UnivariateLinearPiecewise"
    """函数符号名称 / Function symbol name."""

    slope: float = 1.0
    """斜率 / Slope."""

    intercept: float = 0.0
    """截距 / Intercept."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args:
            return self.intercept
        return self.slope * args[0] + self.intercept

    @staticmethod
    def create(
        *,
        slope: float = 1.0,
        intercept: float = 0.0,
    ) -> UnivariateLinearPiecewise:
        """创建单变量线性分段 / Create UnivariateLinearPiecewise.

        Args:
            slope: 斜率 / Slope.
            intercept: 截距 / Intercept.

        Returns:
            单变量线性分段实例 / UnivariateLinearPiecewise instance.
        """
        return UnivariateLinearPiecewise(slope=slope, intercept=intercept)
