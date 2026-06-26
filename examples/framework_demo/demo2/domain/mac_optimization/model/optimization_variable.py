"""优化变量 / Optimization variable.

定义优化问题中的决策变量数据结构。
Defines the data structure for decision variables
in optimization problems.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizationVariable:
    """优化变量 / Optimization variable.

    描述一个具有上下界的连续决策变量。
    Describes a continuous decision variable with
    upper and lower bounds.

    Attributes:
        name: 变量名 / Variable name.
        lower: 下界 / Lower bound.
        upper: 上界 / Upper bound.
        value: 初始值 / Initial value.
    """

    name: str
    """变量名 / Variable name."""

    lower: float
    """下界 / Lower bound."""

    upper: float
    """上界 / Upper bound."""

    value: float
    """初始值 / Initial value."""

    @staticmethod
    def create(
        *,
        name: str,
        lower: float,
        upper: float,
        value: float,
    ) -> OptimizationVariable:
        """创建优化变量 / Create optimization variable.

        Args:
            name: 变量名 / Variable name.
            lower: 下界 / Lower bound.
            upper: 上界 / Upper bound.
            value: 初始值 / Initial value.

        Returns:
            优化变量实例 / Optimization variable instance.
        """
        return OptimizationVariable(
            name=name,
            lower=lower,
            upper=upper,
            value=value,
        )

    @staticmethod
    def non_negative(
        *,
        name: str,
        value: float = 0.0,
        upper: float = float("inf"),
    ) -> OptimizationVariable:
        """创建非负变量 / Create non-negative variable.

        Args:
            name: 变量名 / Variable name.
            value: 初始值，默认 0.0 / Initial value, default 0.0.
            upper: 上界，默认无穷大 / Upper bound, default inf.

        Returns:
            非负优化变量实例 / Non-negative variable instance.
        """
        return OptimizationVariable(
            name=name,
            lower=0.0,
            upper=upper,
            value=value,
        )

    @property
    def range(self) -> float:
        """变量范围（上界-下界）/ Variable range (upper - lower).

        Returns:
            变量允许的取值范围 / Variable allowable range.
        """
        return self.upper - self.lower

    @property
    def is_fixed(self) -> bool:
        """是否为固定变量 / Whether variable is fixed.

        上下界相等时变量为固定值。
        Variable is fixed when lower equals upper.

        Returns:
            固定变量返回 True / True if fixed.
        """
        return self.lower == self.upper

    @property
    def is_binary(self) -> bool:
        """是否为二值变量 / Whether binary variable.

        下界为 0、上界为 1 时视为二值变量。
        Binary when lower is 0 and upper is 1.

        Returns:
            二值变量返回 True / True if binary.
        """
        return self.lower == 0.0 and self.upper == 1.0

    def is_within_bounds(self, val: float) -> bool:
        """检查值是否在界内 / Check if value is within bounds.

        Args:
            val: 待检查的值 / Value to check.

        Returns:
            在界内返回 True / True if within bounds.
        """
        return self.lower <= val <= self.upper

    def with_value(self, value: float) -> OptimizationVariable:
        """更新初始值（返回新实例）。

        Update initial value (returns new instance).

        Args:
            value: 新初始值 / New initial value.

        Returns:
            更新后的新实例 / New updated instance.
        """
        return OptimizationVariable(
            name=self.name,
            lower=self.lower,
            upper=self.upper,
            value=value,
        )
