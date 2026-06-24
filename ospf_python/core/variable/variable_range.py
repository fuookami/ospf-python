"""变量范围定义 / Variable range definition."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VariableRange:
    """变量取值范围 / Variable value range.

    描述变量的上下界。
    Describes the upper and lower bounds of a variable.

    Attributes:
        lower: 下界 / Lower bound.
        upper: 上界 / Upper bound.
    """

    lower: float = float("-inf")
    """下界 / Lower bound."""

    upper: float = float("inf")
    """上界 / Upper bound."""

    def __post_init__(self) -> None:
        """验证范围有效性 / Validate range validity."""
        if self.lower > self.upper:
            object.__setattr__(self, "lower", self.upper)

    def contains(self, value: float) -> bool:
        """判断值是否在范围内 / Check if value is within range.

        Args:
            value: 待检查的值 / Value to check.

        Returns:
            是否在范围内 / Whether the value is in range.
        """
        return self.lower <= value <= self.upper

    def is_empty(self) -> bool:
        """判断范围是否为空 / Check if range is empty.

        Returns:
            范围是否为空 / Whether the range is empty.
        """
        return self.lower > self.upper

    def is_unbounded(self) -> bool:
        """判断范围是否无界 / Check if range is unbounded.

        Returns:
            范围是否无界 / Whether the range is unbounded.
        """
        return self.lower == float("-inf") and self.upper == float("inf")

    @property
    def width(self) -> float:
        """获取范围宽度 / Get range width.

        Returns:
            范围宽度 / Range width.
        """
        return self.upper - self.lower

    @staticmethod
    def create(
        *,
        lower: float = float("-inf"),
        upper: float = float("inf"),
    ) -> VariableRange:
        """创建变量范围 / Create variable range.

        Args:
            lower: 下界，默认负无穷 / Lower bound, default -inf.
            upper: 上界，默认正无穷 / Upper bound, default +inf.

        Returns:
            变量范围实例 / Variable range instance.
        """
        return VariableRange(lower=lower, upper=upper)

    @staticmethod
    def non_negative() -> VariableRange:
        """创建非负范围 / Create non-negative range.

        Returns:
            [0, +inf) 范围 / [0, +inf) range.
        """
        return VariableRange(lower=0.0, upper=float("inf"))

    @staticmethod
    def unit() -> VariableRange:
        """创建单位范围 [0, 1] / Create unit range [0, 1].

        Returns:
            [0, 1] 范围 / [0, 1] range.
        """
        return VariableRange(lower=0.0, upper=1.0)

    @staticmethod
    def fixed(value: float) -> VariableRange:
        """创建固定值范围 / Create fixed-value range.

        Args:
            value: 固定值 / Fixed value.

        Returns:
            [value, value] 范围 / [value, value] range.
        """
        return VariableRange(lower=value, upper=value)
