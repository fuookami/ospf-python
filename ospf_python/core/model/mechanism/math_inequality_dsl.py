"""数学不等式 DSL / Math inequality DSL.

提供链式语法构建不等式约束。
Provides a fluent API for building inequality constraints.
"""

from __future__ import annotations


class MathInequalityDsl:
    """数学不等式 DSL / Math inequality DSL.

    允许通过链式调用构建不等式约束表达式。
    Allows building inequality constraint expressions
    through chained method calls.

    Attributes:
        lhs: 左端表达式 / The left-hand side expression.
        sign: 不等式符号 / The inequality sign.
        rhs: 右端值 / The right-hand side value.
    """

    def __init__(self, lhs: object) -> None:
        """初始化 / Initialize.

        Args:
            lhs: 左端表达式 / The left-hand side expression.
        """
        self.lhs = lhs
        self.sign: str | None = None
        self.rhs: float = 0.0

    def le(self, value: float) -> MathInequalityDsl:
        """设置小于等于 / Set less than or equal to.

        Args:
            value: 右端值 / The right-hand side value.

        Returns:
            自身，用于链式调用 / Self for chaining.
        """
        self.sign = "<="
        self.rhs = value
        return self

    def ge(self, value: float) -> MathInequalityDsl:
        """设置大于等于 / Set greater than or equal to.

        Args:
            value: 右端值 / The right-hand side value.

        Returns:
            自身，用于链式调用 / Self for chaining.
        """
        self.sign = ">="
        self.rhs = value
        return self

    def eq(self, value: float) -> MathInequalityDsl:
        """设置等于 / Set equal to.

        Args:
            value: 右端值 / The right-hand side value.

        Returns:
            自身，用于链式调用 / Self for chaining.
        """
        self.sign = "=="
        self.rhs = value
        return self
