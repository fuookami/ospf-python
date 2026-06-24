"""MathInequalityDsl 测试。

测试数学不等式 DSL 的链式语法。
Tests MathInequalityDsl fluent API.
"""

from __future__ import annotations

from ospf_python.core.model.mechanism.math_inequality_dsl import (
    MathInequalityDsl,
)


class TestMathInequalityDsl:
    """不等式 DSL 测试 / MathInequalityDsl tests."""

    def test_init(self) -> None:
        """初始化设置 lhs。/ Init sets lhs."""
        dsl = MathInequalityDsl("expr")
        assert dsl.lhs == "expr"
        assert dsl.sign is None
        assert dsl.rhs == 0.0

    def test_le_sets_sign_and_rhs(self) -> None:
        """le 设置符号和右端值。/ le sets sign and rhs."""
        dsl = MathInequalityDsl("x")
        result = dsl.le(10.0)
        assert dsl.sign == "<="
        assert dsl.rhs == 10.0
        assert result is dsl

    def test_ge_sets_sign_and_rhs(self) -> None:
        """ge 设置符号和右端值。/ ge sets sign and rhs."""
        dsl = MathInequalityDsl("x")
        result = dsl.ge(5.0)
        assert dsl.sign == ">="
        assert dsl.rhs == 5.0
        assert result is dsl

    def test_eq_sets_sign_and_rhs(self) -> None:
        """eq 设置符号和右端值。/ eq sets sign and rhs."""
        dsl = MathInequalityDsl("x")
        result = dsl.eq(3.0)
        assert dsl.sign == "=="
        assert dsl.rhs == 3.0
        assert result is dsl

    def test_chaining(self) -> None:
        """链式调用覆盖前值。/ Chaining overwrites previous."""
        dsl = MathInequalityDsl("x")
        dsl.le(10.0).ge(5.0)
        assert dsl.sign == ">="
        assert dsl.rhs == 5.0

    def test_le_returns_self(self) -> None:
        """le 返回自身。/ le returns self."""
        dsl = MathInequalityDsl("x")
        assert dsl.le(1.0) is dsl

    def test_ge_returns_self(self) -> None:
        """ge 返回自身。/ ge returns self."""
        dsl = MathInequalityDsl("x")
        assert dsl.ge(1.0) is dsl

    def test_eq_returns_self(self) -> None:
        """eq 返回自身。/ eq returns self."""
        dsl = MathInequalityDsl("x")
        assert dsl.eq(1.0) is dsl
