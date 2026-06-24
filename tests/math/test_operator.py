"""运算符模块测试。

Operator module tests.

测试所有运算符函数：abs、contains、div、exp、log、minus、neg、plus。
Tests all operator functions: abs, contains, div, exp,
log, minus, neg, plus.
"""

from __future__ import annotations

import math

from ospf_python.math.operator.abs import abs_op
from ospf_python.math.operator.contains import contains_op
from ospf_python.math.operator.div import div_op
from ospf_python.math.operator.exp import exp2_op, exp10_op, exp_op
from ospf_python.math.operator.log import (
    log2_op,
    log10_op,
    log_op,
)
from ospf_python.math.operator.minus import minus_op
from ospf_python.math.operator.neg import neg_op
from ospf_python.math.operator.plus import plus_op

# ── abs_op ──────────────────────────────────────────────────────


class TestAbsOp:
    """绝对值运算符测试。"""

    def test_positive_int(self) -> None:
        """正整数绝对值。/ Positive int absolute value."""
        assert abs_op(5) == 5

    def test_negative_int(self) -> None:
        """负整数绝对值。/ Negative int absolute value."""
        assert abs_op(-3) == 3

    def test_zero_int(self) -> None:
        """零的绝对值。/ Zero absolute value."""
        assert abs_op(0) == 0

    def test_positive_float(self) -> None:
        """正浮点绝对值。/ Positive float absolute value."""
        assert abs_op(3.14) == 3.14

    def test_negative_float(self) -> None:
        """负浮点绝对值。/ Negative float absolute value."""
        assert abs_op(-2.5) == 2.5


# ── contains_op ─────────────────────────────────────────────────


class TestContainsOp:
    """包含运算符测试。"""

    def test_list_contains(self) -> None:
        """列表包含元素。/ List contains item."""
        assert contains_op([1, 2, 3], 2)

    def test_list_not_contains(self) -> None:
        """列表不包含元素。/ List does not contain item."""
        assert not contains_op([1, 2, 3], 5)

    def test_string_contains(self) -> None:
        """字符串包含子串。/ String contains substring."""
        assert contains_op("hello", "e")

    def test_set_contains(self) -> None:
        """集合包含元素。/ Set contains item."""
        assert contains_op({10, 20, 30}, 20)

    def test_empty_container(self) -> None:
        """空容器不包含任何元素。/ Empty container has no items."""
        assert not contains_op([], 1)


# ── div_op ──────────────────────────────────────────────────────


class TestDivOp:
    """整除运算符测试。"""

    def test_exact_division(self) -> None:
        """整除。/ Exact division."""
        assert div_op(10, 3) == 3

    def test_even_division(self) -> None:
        """整除无余数。/ Even division."""
        assert div_op(12, 4) == 3

    def test_negative_division(self) -> None:
        """负数整除。/ Negative division."""
        assert div_op(-7, 2) == -4

    def test_zero_dividend(self) -> None:
        """被除数为零。/ Zero dividend."""
        assert div_op(0, 5) == 0


# ── exp_op / exp2_op / exp10_op ─────────────────────────────────


class TestExpOp:
    """指数运算符测试。"""

    def test_exp_zero(self) -> None:
        """e^0 = 1。/ e^0 = 1."""
        assert exp_op(0.0) == 1.0

    def test_exp_one(self) -> None:
        """e^1 = e。/ e^1 = e."""
        assert math.isclose(exp_op(1.0), math.e)

    def test_exp2_zero(self) -> None:
        """2^0 = 1。/ 2^0 = 1."""
        assert exp2_op(0.0) == 1.0

    def test_exp2_ten(self) -> None:
        """2^10 = 1024。/ 2^10 = 1024."""
        assert exp2_op(10.0) == 1024.0

    def test_exp10_zero(self) -> None:
        """10^0 = 1。/ 10^0 = 1."""
        assert exp10_op(0.0) == 1.0

    def test_exp10_two(self) -> None:
        """10^2 = 100。/ 10^2 = 100."""
        assert exp10_op(2.0) == 100.0


# ── log_op / log2_op / log10_op ────────────────────────────────


class TestLogOp:
    """对数运算符测试。"""

    def test_log_one(self) -> None:
        """ln(1) = 0。/ ln(1) = 0."""
        assert log_op(1.0) == 0.0

    def test_log_e(self) -> None:
        """ln(e) = 1。/ ln(e) = 1."""
        assert math.isclose(log_op(math.e), 1.0)

    def test_log2_one(self) -> None:
        """log2(1) = 0。/ log2(1) = 0."""
        assert log2_op(1.0) == 0.0

    def test_log2_eight(self) -> None:
        """log2(8) = 3。/ log2(8) = 3."""
        assert log2_op(8.0) == 3.0

    def test_log10_one(self) -> None:
        """log10(1) = 0。/ log10(1) = 0."""
        assert log10_op(1.0) == 0.0

    def test_log10_thousand(self) -> None:
        """log10(1000) = 3。/ log10(1000) = 3."""
        assert log10_op(1000.0) == 3.0


# ── minus_op ────────────────────────────────────────────────────


class TestMinusOp:
    """减法运算符测试。"""

    def test_basic_subtraction(self) -> None:
        """基本减法。/ Basic subtraction."""
        assert minus_op(10, 3) == 7

    def test_result_zero(self) -> None:
        """结果为零。/ Result is zero."""
        assert minus_op(5, 5) == 0

    def test_negative_result(self) -> None:
        """负结果。/ Negative result."""
        assert minus_op(3, 7) == -4

    def test_float_subtraction(self) -> None:
        """浮点减法。/ Float subtraction."""
        assert minus_op(5.5, 2.3) == 3.2


# ── neg_op ──────────────────────────────────────────────────────


class TestNegOp:
    """取反运算符测试。"""

    def test_positive_negation(self) -> None:
        """正数取反。/ Positive negation."""
        assert neg_op(5) == -5

    def test_negative_negation(self) -> None:
        """负数取反。/ Negative negation."""
        assert neg_op(-3) == 3

    def test_zero_negation(self) -> None:
        """零取反。/ Zero negation."""
        assert neg_op(0) == 0

    def test_float_negation(self) -> None:
        """浮点取反。/ Float negation."""
        assert neg_op(2.5) == -2.5


# ── plus_op ─────────────────────────────────────────────────────


class TestPlusOp:
    """加法运算符测试。"""

    def test_basic_addition(self) -> None:
        """基本加法。/ Basic addition."""
        assert plus_op(3, 4) == 7

    def test_zero_addition(self) -> None:
        """加零。/ Add zero."""
        assert plus_op(5, 0) == 5

    def test_negative_addition(self) -> None:
        """负数加法。/ Negative addition."""
        assert plus_op(-3, -4) == -7

    def test_mixed_sign(self) -> None:
        """异号加法。/ Mixed sign addition."""
        assert plus_op(5, -3) == 2
