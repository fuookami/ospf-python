"""符号模块测试。

测试函数符号、中间符号、展平工具和符号组合。
Tests function symbols, intermediate symbols,
flatten utilities, and symbol combinations.
"""

from __future__ import annotations

import math

import pytest

from ospf_python.core.symbol import (
    IntermediateSymbol,
    IntermediateSymbolExpressionSupport,
    QuantitySymbolConversion,
    SolverBoundaryCasts,
    SymbolCombination,
)
from ospf_python.core.symbol.flatten import FlattenUtility
from ospf_python.core.symbol.function import (
    Abs,
    And,
    BalanceTernaryzation,
    BigM,
    Binaryzation,
    BivariateLinearPiecewise,
    Ceiling,
    Cos,
    First,
    Floor,
    FunctionSymbol,
    If,
    IfIn,
    IfThen,
    Imply,
    Inequality,
    InStepRange,
    Masking,
    Max,
    MinMax,
    Mod,
    OneOf,
    Product,
    QuadraticInStepRange,
    QuadraticLinear,
    QuadraticMaskingRange,
    QuadraticMin,
    Rounding,
    SameAs,
    SatisfiedAmount,
    SatisfiedAmountInequality,
    Semi,
    Sigmoid,
    Sin,
    Slack,
    SlackRange,
    UnivariateLinearPiecewise,
)
from ospf_python.core.token.token import Token
from ospf_python.core.variable.type import VariableType

# ---------------------------------------------------------------------------
# FunctionSymbol 基类测试
# ---------------------------------------------------------------------------


class TestFunctionSymbolBase:
    """函数符号基类测试 / Function symbol base tests."""

    def test_abs_is_function_symbol(self) -> None:
        """Abs 是 FunctionSymbol 子类。/ Abs is subclass."""
        s = Abs()
        assert isinstance(s, FunctionSymbol)

    def test_str_returns_name(self) -> None:
        """字符串返回名称。/ str returns name."""
        s = Abs()
        assert str(s) == "Abs"

    def test_frozen(self) -> None:
        """符号不可变。/ Symbol is frozen."""
        s = Abs()
        with pytest.raises(AttributeError):
            s.name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 简单函数符号测试
# ---------------------------------------------------------------------------


class TestAbs:
    """绝对值测试 / Abs tests."""

    def test_positive(self) -> None:
        """正数绝对值。/ Positive abs."""
        assert Abs().evaluate((5.0,)) == 5.0

    def test_negative(self) -> None:
        """负数绝对值。/ Negative abs."""
        assert Abs().evaluate((-3.0,)) == 3.0

    def test_zero(self) -> None:
        """零的绝对值。/ Zero abs."""
        assert Abs().evaluate((0.0,)) == 0.0

    def test_empty_args(self) -> None:
        """空参数。/ Empty args."""
        assert Abs().evaluate(()) == 0.0

    def test_create_factory(self) -> None:
        """工厂方法创建。/ Factory method create."""
        s = Abs.create()
        assert s.name == "Abs"


class TestAnd:
    """逻辑与测试 / And tests."""

    def test_all_true(self) -> None:
        """全真。/ All true."""
        assert And().evaluate((1.0, 1.0, 1.0)) == 1.0

    def test_one_false(self) -> None:
        """一个假。/ One false."""
        assert And().evaluate((1.0, 0.0, 1.0)) == 0.0

    def test_all_false(self) -> None:
        """全假。/ All false."""
        assert And().evaluate((0.0, 0.0)) == 0.0

    def test_empty(self) -> None:
        """空参数为真。/ Empty is true."""
        assert And().evaluate(()) == 1.0


class TestCeiling:
    """向上取整测试 / Ceiling tests."""

    def test_fraction(self) -> None:
        """小数向上取整。/ Fraction ceiling."""
        assert Ceiling().evaluate((2.3,)) == 3.0

    def test_integer(self) -> None:
        """整数不变。/ Integer unchanged."""
        assert Ceiling().evaluate((5.0,)) == 5.0

    def test_negative(self) -> None:
        """负数向上取整。/ Negative ceiling."""
        assert Ceiling().evaluate((-2.3,)) == -2


class TestFloor:
    """向下取整测试 / Floor tests."""

    def test_fraction(self) -> None:
        """小数向下取整。/ Fraction floor."""
        assert Floor().evaluate((2.7,)) == 2.0

    def test_integer(self) -> None:
        """整数不变。/ Integer unchanged."""
        assert Floor().evaluate((5.0,)) == 5.0

    def test_negative(self) -> None:
        """负数向下取整。/ Negative floor."""
        assert Floor().evaluate((-2.7,)) == -3


class TestCos:
    """余弦测试 / Cos tests."""

    def test_zero(self) -> None:
        """cos(0) = 1。/ cos(0) = 1."""
        assert Cos().evaluate((0.0,)) == pytest.approx(1.0)

    def test_pi(self) -> None:
        """cos(pi) = -1。/ cos(pi) = -1."""
        assert Cos().evaluate((math.pi,)) == pytest.approx(-1.0)


class TestSin:
    """正弦测试 / Sin tests."""

    def test_zero(self) -> None:
        """sin(0) = 0。/ sin(0) = 0."""
        assert Sin().evaluate((0.0,)) == pytest.approx(0.0)

    def test_half_pi(self) -> None:
        """sin(pi/2) = 1。/ sin(pi/2) = 1."""
        assert Sin().evaluate((math.pi / 2,)) == pytest.approx(1.0)


class TestFirst:
    """取首元素测试 / First tests."""

    def test_returns_first(self) -> None:
        """返回首元素。/ Returns first."""
        assert First().evaluate((10.0, 20.0)) == 10.0

    def test_empty(self) -> None:
        """空参数。/ Empty args."""
        assert First().evaluate(()) == 0.0


class TestMax:
    """最大值测试 / Max tests."""

    def test_multiple_args(self) -> None:
        """多参数最大值。/ Multiple args max."""
        assert Max().evaluate((1.0, 5.0, 3.0)) == 5.0

    def test_single_arg(self) -> None:
        """单参数。/ Single arg."""
        assert Max().evaluate((7.0,)) == 7.0

    def test_empty(self) -> None:
        """空参数。/ Empty args."""
        assert Max().evaluate(()) == 0.0


class TestProduct:
    """乘积测试 / Product tests."""

    def test_multiple(self) -> None:
        """多参数乘积。/ Multiple args product."""
        assert Product().evaluate((2.0, 3.0, 4.0)) == 24.0

    def test_single(self) -> None:
        """单参数。/ Single arg."""
        assert Product().evaluate((5.0,)) == 5.0

    def test_empty(self) -> None:
        """空参数。/ Empty args."""
        assert Product().evaluate(()) == 1.0

    def test_with_zero(self) -> None:
        """含零乘积。/ Product with zero."""
        assert Product().evaluate((2.0, 0.0, 5.0)) == 0.0


class TestSlack:
    """松弛测试 / Slack tests."""

    def test_positive(self) -> None:
        """正数松弛。/ Positive slack."""
        assert Slack().evaluate((5.0,)) == 5.0

    def test_negative(self) -> None:
        """负数松弛为零。/ Negative slack is zero."""
        assert Slack().evaluate((-3.0,)) == 0.0

    def test_zero(self) -> None:
        """零松弛。/ Zero slack."""
        assert Slack().evaluate((0.0,)) == 0.0

    def test_empty(self) -> None:
        """空参数。/ Empty args."""
        assert Slack().evaluate(()) == 0.0


# ---------------------------------------------------------------------------
# 带参数函数符号测试
# ---------------------------------------------------------------------------


class TestBinaryzation:
    """二值化测试 / Binaryzation tests."""

    def test_above_threshold(self) -> None:
        """高于阈值为 1。/ Above threshold is 1."""
        s = Binaryzation(threshold=0.5)
        assert s.evaluate((0.7,)) == 1.0

    def test_below_threshold(self) -> None:
        """低于阈值为 0。/ Below threshold is 0."""
        s = Binaryzation(threshold=0.5)
        assert s.evaluate((0.3,)) == 0.0

    def test_equal_threshold(self) -> None:
        """等于阈值为 0。/ Equal threshold is 0."""
        s = Binaryzation(threshold=0.5)
        assert s.evaluate((0.5,)) == 0.0

    def test_empty(self) -> None:
        """空参数。/ Empty args."""
        s = Binaryzation()
        assert s.evaluate(()) == 0.0

    def test_create_factory(self) -> None:
        """工厂方法创建。/ Factory method create."""
        s = Binaryzation.create(threshold=0.8)
        assert s.threshold == 0.8


class TestBigM:
    """大M法测试 / BigM tests."""

    def test_nonzero(self) -> None:
        """非零返回 M 值。/ Non-zero returns M."""
        s = BigM(m_value=1000.0)
        assert s.evaluate((1.0,)) == 1000.0

    def test_zero(self) -> None:
        """零返回 0。/ Zero returns 0."""
        s = BigM(m_value=1000.0)
        assert s.evaluate((0.0,)) == 0.0


class TestIfIn:
    """范围内条件测试 / IfIn tests."""

    def test_in_range(self) -> None:
        """范围内为 1。/ In range is 1."""
        s = IfIn(lower=0.0, upper=10.0)
        assert s.evaluate((5.0,)) == 1.0

    def test_out_of_range(self) -> None:
        """范围外为 0。/ Out of range is 0."""
        s = IfIn(lower=0.0, upper=10.0)
        assert s.evaluate((15.0,)) == 0.0

    def test_boundary(self) -> None:
        """边界值为 1。/ Boundary is 1."""
        s = IfIn(lower=0.0, upper=10.0)
        assert s.evaluate((0.0,)) == 1.0
        assert s.evaluate((10.0,)) == 1.0


class TestInequality:
    """不等式测试 / Inequality tests."""

    def test_satisfied(self) -> None:
        """满足不等式。/ Inequality satisfied."""
        s = Inequality(rhs=10.0)
        assert s.evaluate((5.0,)) == 1.0

    def test_violated(self) -> None:
        """违反不等式。/ Inequality violated."""
        s = Inequality(rhs=10.0)
        assert s.evaluate((15.0,)) == 0.0

    def test_boundary_with_tolerance(self) -> None:
        """边界带容差。/ Boundary with tolerance."""
        s = Inequality(rhs=10.0, tolerance=0.1)
        assert s.evaluate((10.05,)) == 1.0


class TestMinMax:
    """最小最大值测试 / MinMax tests."""

    def test_within_range(self) -> None:
        """范围内保持原值。/ In range unchanged."""
        s = MinMax(lower_cap=0.0, upper_cap=10.0)
        assert s.evaluate((5.0,)) == 5.0

    def test_below_lower(self) -> None:
        """低于下限取下限。/ Below lower cap."""
        s = MinMax(lower_cap=0.0, upper_cap=10.0)
        assert s.evaluate((-5.0,)) == 0.0

    def test_above_upper(self) -> None:
        """高于上限取上限。/ Above upper cap."""
        s = MinMax(lower_cap=0.0, upper_cap=10.0)
        assert s.evaluate((15.0,)) == 10.0


class TestMod:
    """取模测试 / Mod tests."""

    def test_basic(self) -> None:
        """基本取模。/ Basic mod."""
        s = Mod(divisor=3.0)
        assert s.evaluate((7.0,)) == pytest.approx(1.0)

    def test_exact(self) -> None:
        """整除取模。/ Exact division."""
        s = Mod(divisor=3.0)
        assert s.evaluate((6.0,)) == pytest.approx(0.0)

    def test_zero_divisor(self) -> None:
        """零除数返回 0。/ Zero divisor returns 0."""
        s = Mod(divisor=0.0)
        assert s.evaluate((5.0,)) == 0.0


class TestSigmoid:
    """S型函数测试 / Sigmoid tests."""

    def test_zero_input(self) -> None:
        """零输入返回 0.5。/ Zero input returns 0.5."""
        s = Sigmoid()
        assert s.evaluate((0.0,)) == pytest.approx(0.5)

    def test_large_positive(self) -> None:
        """大正数趋近 1。/ Large positive near 1."""
        s = Sigmoid()
        assert s.evaluate((100.0,)) == pytest.approx(1.0)

    def test_large_negative(self) -> None:
        """大负数趋近 0。/ Large negative near 0."""
        s = Sigmoid()
        assert s.evaluate((-100.0,)) == pytest.approx(0.0, abs=1e-10)


class TestRounding:
    """四舍五入测试 / Rounding tests."""

    def test_zero_decimals(self) -> None:
        """零小数位。/ Zero decimals."""
        s = Rounding(decimals=0)
        assert s.evaluate((2.6,)) == 3.0

    def test_two_decimals(self) -> None:
        """两位小数。/ Two decimals."""
        s = Rounding(decimals=2)
        assert s.evaluate((2.655,)) == pytest.approx(2.66)


class TestImply:
    """蕴含测试 / Imply tests."""

    def test_true_implies_true(self) -> None:
        """真蕴含真为真。/ T implies T is T."""
        assert Imply().evaluate((1.0, 1.0)) == 1.0

    def test_true_implies_false(self) -> None:
        """真蕴含假为假。/ T implies F is F."""
        assert Imply().evaluate((1.0, 0.0)) == 0.0

    def test_false_implies_any(self) -> None:
        """假蕴含任意为真。/ F implies any is T."""
        assert Imply().evaluate((0.0, 0.0)) == 1.0
        assert Imply().evaluate((0.0, 1.0)) == 1.0


class TestIf:
    """条件测试 / If tests."""

    def test_condition_true(self) -> None:
        """条件为真取第二参数。/ True takes second."""
        assert If().evaluate((1.0, 10.0, 20.0)) == 10.0

    def test_condition_false(self) -> None:
        """条件为假取第三参数。/ False takes third."""
        assert If().evaluate((0.0, 10.0, 20.0)) == 20.0

    def test_insufficient_args(self) -> None:
        """参数不足返回 0。/ Insufficient returns 0."""
        assert If().evaluate((1.0,)) == 0.0


class TestSameAs:
    """等同于测试 / SameAs tests."""

    def test_equal(self) -> None:
        """相等返回 1。/ Equal returns 1."""
        assert SameAs().evaluate((5.0, 5.0)) == 1.0

    def test_not_equal(self) -> None:
        """不等返回 0。/ Not equal returns 0."""
        assert SameAs().evaluate((5.0, 3.0)) == 0.0

    def test_insufficient(self) -> None:
        """参数不足返回 1。/ Insufficient returns 1."""
        assert SameAs().evaluate((5.0,)) == 1.0


class TestOneOf:
    """其中之一测试 / OneOf tests."""

    def test_exactly_one(self) -> None:
        """恰好一个非零。/ Exactly one non-zero."""
        assert OneOf().evaluate((0.0, 1.0, 0.0)) == 1.0

    def test_two_nonzero(self) -> None:
        """两个非零。/ Two non-zero."""
        assert OneOf().evaluate((1.0, 1.0, 0.0)) == 0.0

    def test_none_nonzero(self) -> None:
        """全零。/ All zero."""
        assert OneOf().evaluate((0.0, 0.0)) == 0.0


class TestSatisfiedAmount:
    """满足数量测试 / SatisfiedAmount tests."""

    def test_count(self) -> None:
        """计数非零。/ Count non-zero."""
        s = SatisfiedAmount()
        assert s.evaluate((1.0, 0.0, 1.0, 0.0)) == 2.0

    def test_all_satisfied(self) -> None:
        """全部满足。/ All satisfied."""
        s = SatisfiedAmount()
        assert s.evaluate((1.0, 1.0, 1.0)) == 3.0

    def test_none_satisfied(self) -> None:
        """无满足。/ None satisfied."""
        s = SatisfiedAmount()
        assert s.evaluate((0.0, 0.0)) == 0.0


class TestSemi:
    """半连续测试 / Semi tests."""

    def test_zero_returns_zero(self) -> None:
        """零返回零。/ Zero returns zero."""
        s = Semi(lower=1.0, upper=10.0)
        assert s.evaluate((0.0,)) == 0.0

    def test_in_range(self) -> None:
        """范围内返回原值。/ In range returns value."""
        s = Semi(lower=1.0, upper=10.0)
        assert s.evaluate((5.0,)) == 5.0

    def test_below_lower(self) -> None:
        """低于下界取下界。/ Below lower cap."""
        s = Semi(lower=1.0, upper=10.0)
        assert s.evaluate((0.5,)) == 1.0


class TestBalanceTernaryzation:
    """平衡三值化测试 / BalanceTernaryzation tests."""

    def test_positive_above_threshold(self) -> None:
        """正数超阈值。/ Positive above threshold."""
        s = BalanceTernaryzation(threshold=0.5)
        assert s.evaluate((1.0,)) == 1.0

    def test_negative_below_threshold(self) -> None:
        """负数低于阈值。/ Negative below threshold."""
        s = BalanceTernaryzation(threshold=0.5)
        assert s.evaluate((-1.0,)) == -1.0

    def test_within_threshold(self) -> None:
        """阈值范围内。/ Within threshold."""
        s = BalanceTernaryzation(threshold=0.5)
        assert s.evaluate((0.3,)) == 0.0


class TestQuadraticLinear:
    """二次线性测试 / QuadraticLinear tests."""

    def test_basic(self) -> None:
        """基本二次线性。/ Basic quadratic linear."""
        s = QuadraticLinear(
            quadratic_coeff=1.0,
            linear_coeff=2.0,
            intercept=3.0,
        )
        # 1*4 + 2*2 + 3 = 11
        assert s.evaluate((2.0,)) == pytest.approx(11.0)

    def test_empty(self) -> None:
        """空参数。/ Empty args."""
        s = QuadraticLinear()
        assert s.evaluate(()) == 0.0


class TestUnivariateLinearPiecewise:
    """单变量线性分段测试 / UnivariateLinearPiecewise tests."""

    def test_basic(self) -> None:
        """基本线性。/ Basic linear."""
        s = UnivariateLinearPiecewise(slope=2.0, intercept=3.0)
        assert s.evaluate((4.0,)) == pytest.approx(11.0)

    def test_empty(self) -> None:
        """空参数返回截距。/ Empty returns intercept."""
        s = UnivariateLinearPiecewise(intercept=5.0)
        assert s.evaluate(()) == pytest.approx(5.0)


class TestBivariateLinearPiecewise:
    """双变量线性分段测试 / BivariateLinearPiecewise tests."""

    def test_basic(self) -> None:
        """基本双变量线性。/ Basic bivariate linear."""
        s = BivariateLinearPiecewise(slope_x=2.0, slope_y=3.0, intercept=1.0)
        # 2*4 + 3*5 + 1 = 24
        assert s.evaluate((4.0, 5.0)) == pytest.approx(24.0)

    def test_insufficient_args(self) -> None:
        """参数不足返回 0。/ Insufficient returns 0."""
        s = BivariateLinearPiecewise()
        assert s.evaluate((1.0,)) == 0.0


class TestQuadraticMaskingRange:
    """二次掩码范围测试 / QuadraticMaskingRange tests."""

    def test_in_range(self) -> None:
        """范围内二次。/ In range quadratic."""
        s = QuadraticMaskingRange(lower=0.0, upper=10.0, coeff=2.0)
        assert s.evaluate((3.0,)) == pytest.approx(18.0)

    def test_out_of_range(self) -> None:
        """范围外为 0。/ Out of range is 0."""
        s = QuadraticMaskingRange(lower=0.0, upper=10.0)
        assert s.evaluate((15.0,)) == 0.0


class TestQuadraticMin:
    """二次最小值测试 / QuadraticMin tests."""

    def test_picks_minimum(self) -> None:
        """取最小二次值。/ Picks minimum quadratic."""
        s = QuadraticMin(coeff=1.0)
        # min(1*1, 1*4, 1*9) = 1
        assert s.evaluate((1.0, 2.0, 3.0)) == pytest.approx(1.0)


class TestIfThen:
    """蕴含条件测试 / IfThen tests."""

    def test_condition_true(self) -> None:
        """条件为真返回第二参数。/ True returns second."""
        assert IfThen().evaluate((1.0, 10.0)) == 10.0

    def test_condition_false(self) -> None:
        """条件为假返回 0。/ False returns 0."""
        assert IfThen().evaluate((0.0, 10.0)) == 0.0

    def test_insufficient(self) -> None:
        """参数不足返回 0。/ Insufficient returns 0."""
        assert IfThen().evaluate((1.0,)) == 0.0


class TestInStepRange:
    """步进范围内测试 / InStepRange tests."""

    def test_on_step(self) -> None:
        """在步进点上。/ On step point."""
        s = InStepRange(step=2.0, lower=0.0, upper=10.0)
        assert s.evaluate((4.0,)) == 1.0

    def test_off_step(self) -> None:
        """不在步进点上。/ Off step point."""
        s = InStepRange(step=2.0, lower=0.0, upper=10.0)
        assert s.evaluate((3.0,)) == 0.0

    def test_out_of_range(self) -> None:
        """超出范围。/ Out of range."""
        s = InStepRange(step=2.0, lower=0.0, upper=10.0)
        assert s.evaluate((15.0,)) == 0.0


class TestMasking:
    """掩码测试 / Masking tests."""

    def test_nonzero_passthrough(self) -> None:
        """非零透传。/ Non-zero passthrough."""
        s = Masking(mask_value=-1.0)
        assert s.evaluate((5.0,)) == 5.0

    def test_zero_masked(self) -> None:
        """零被掩码。/ Zero is masked."""
        s = Masking(mask_value=-1.0)
        assert s.evaluate((0.0,)) == -1.0

    def test_empty(self) -> None:
        """空参数返回掩码值。/ Empty returns mask."""
        s = Masking(mask_value=99.0)
        assert s.evaluate(()) == 99.0


class TestQuadraticInStepRange:
    """二次步进范围内测试 / QuadraticInStepRange tests."""

    def test_basic(self) -> None:
        """基本二次步进。/ Basic quadratic step."""
        s = QuadraticInStepRange(step=1.0, coeff=2.0)
        # idx=3, coeff*idx*idx = 2*9 = 18
        assert s.evaluate((3.0,)) == pytest.approx(18.0)

    def test_zero_step(self) -> None:
        """零步长返回 0。/ Zero step returns 0."""
        s = QuadraticInStepRange(step=0.0)
        assert s.evaluate((5.0,)) == 0.0


class TestSatisfiedAmountInequality:
    """不等式满足数量测试 / SatisfiedAmountInequality tests."""

    def test_count(self) -> None:
        """计数满足不等式的。/ Count satisfied."""
        s = SatisfiedAmountInequality(rhs=5.0)
        # args <= 5.0: 1.0, 3.0, 5.0 = 3 items
        assert s.evaluate((1.0, 3.0, 5.0, 7.0)) == 3.0

    def test_none_satisfied(self) -> None:
        """无满足。/ None satisfied."""
        s = SatisfiedAmountInequality(rhs=0.0)
        assert s.evaluate((1.0, 2.0)) == 0.0


class TestSlackRange:
    """松弛范围测试 / SlackRange tests."""

    def test_within_range(self) -> None:
        """范围内松弛等于范围宽度。/ In range slack equals width."""
        s = SlackRange(lower=0.0, upper=10.0)
        # max(0, 5) + max(0, 5) = 10
        assert s.evaluate((5.0,)) == pytest.approx(10.0)

    def test_below_lower(self) -> None:
        """低于下界。/ Below lower."""
        s = SlackRange(lower=0.0, upper=10.0)
        # max(0, -3) + max(0, 13) = 13
        assert s.evaluate((-3.0,)) == pytest.approx(13.0)

    def test_above_upper(self) -> None:
        """高于上限。/ Above upper."""
        s = SlackRange(lower=0.0, upper=10.0)
        # max(0, 15) + max(0, -5) = 15
        assert s.evaluate((15.0,)) == pytest.approx(15.0)


# ---------------------------------------------------------------------------
# 中间符号测试
# ---------------------------------------------------------------------------


class TestIntermediateSymbol:
    """中间符号测试 / IntermediateSymbol tests."""

    def test_create(self) -> None:
        """创建中间符号。/ Create intermediate symbol."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(token=t, expression_name="sum_x")
        assert s.name == "x"
        assert s.index == 0
        assert s.expression_name == "sum_x"

    def test_str(self) -> None:
        """字符串格式。/ String format."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(token=t, expression_name="sum")
        assert str(s) == "sum(x[0])"

    def test_frozen(self) -> None:
        """不可变。/ Frozen."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(token=t, expression_name="sum")
        with pytest.raises(AttributeError):
            s.expression_name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 中间符号表达式支持测试
# ---------------------------------------------------------------------------


class TestIntermediateSymbolExpressionSupport:
    """表达式支持测试 / Expression support tests."""

    def test_register_and_resolve(self) -> None:
        """注册并解析。/ Register and resolve."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(token=t, expression_name="sum")
        support = IntermediateSymbolExpressionSupport()
        support.register(s, "x + 1")
        assert support.resolve(s) == "x + 1"

    def test_resolve_missing(self) -> None:
        """解析不存在返回 None。/ Resolve missing."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(token=t, expression_name="sum")
        support = IntermediateSymbolExpressionSupport()
        assert support.resolve(s) is None

    def test_is_registered(self) -> None:
        """判断已注册。/ Check registered."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(token=t, expression_name="sum")
        support = IntermediateSymbolExpressionSupport()
        assert support.is_registered(s) is False
        support.register(s, "x + 1")
        assert support.is_registered(s) is True

    def test_count(self) -> None:
        """计数。/ Count."""
        support = IntermediateSymbolExpressionSupport()
        assert support.count == 0
        t = Token(name="x", index=0)
        s = IntermediateSymbol(token=t, expression_name="sum")
        support.register(s, "x + 1")
        assert support.count == 1

    def test_clear(self) -> None:
        """清空。/ Clear."""
        t = Token(name="x", index=0)
        s = IntermediateSymbol(token=t, expression_name="sum")
        support = IntermediateSymbolExpressionSupport()
        support.register(s, "x + 1")
        support.clear()
        assert support.count == 0


# ---------------------------------------------------------------------------
# 量符号转换测试
# ---------------------------------------------------------------------------


class TestQuantitySymbolConversion:
    """量符号转换测试 / Quantity symbol conversion tests."""

    def test_convert_value(self) -> None:
        """转换值。/ Convert value."""
        conv = QuantitySymbolConversion.create(scale=2.0, offset=3.0)
        assert conv.convert_value(5.0) == pytest.approx(13.0)

    def test_default_params(self) -> None:
        """默认参数不变。/ Default params unchanged."""
        conv = QuantitySymbolConversion()
        assert conv.convert_value(5.0) == pytest.approx(5.0)

    def test_register_and_resolve(self) -> None:
        """注册并解析量。/ Register and resolve quantity."""
        conv = QuantitySymbolConversion()
        t = Token(name="temp", index=0)
        conv.register_quantity("temperature", t)
        assert conv.resolve_quantity("temperature") == t

    def test_resolve_missing(self) -> None:
        """解析不存在返回 None。/ Resolve missing."""
        conv = QuantitySymbolConversion()
        assert conv.resolve_quantity("unknown") is None

    def test_registered_count(self) -> None:
        """已注册数量。/ Registered count."""
        conv = QuantitySymbolConversion()
        assert conv.registered_count == 0
        conv.register_quantity("a", Token(name="a", index=0))
        assert conv.registered_count == 1


# ---------------------------------------------------------------------------
# 求解器边界类型转换测试
# ---------------------------------------------------------------------------


class TestSolverBoundaryCasts:
    """边界类型转换测试 / Boundary cast tests."""

    def test_register_and_lookup(self) -> None:
        """注册并查找。/ Register and lookup."""
        casts = SolverBoundaryCasts()
        casts.register_cast("x", VariableType.INTEGER)
        assert casts.lookup_cast("x") is VariableType.INTEGER

    def test_lookup_missing(self) -> None:
        """查找不存在返回 None。/ Lookup missing."""
        casts = SolverBoundaryCasts()
        assert casts.lookup_cast("unknown") is None

    def test_has_cast(self) -> None:
        """判断有转换。/ Check has cast."""
        casts = SolverBoundaryCasts()
        assert casts.has_cast("x") is False
        casts.register_cast("x", VariableType.BINARY)
        assert casts.has_cast("x") is True

    def test_rule_count(self) -> None:
        """规则数量。/ Rule count."""
        casts = SolverBoundaryCasts()
        assert casts.rule_count == 0
        casts.register_cast("a", VariableType.INTEGER)
        casts.register_cast("b", VariableType.BINARY)
        assert casts.rule_count == 2

    def test_clear(self) -> None:
        """清空规则。/ Clear rules."""
        casts = SolverBoundaryCasts()
        casts.register_cast("a", VariableType.INTEGER)
        casts.clear()
        assert casts.rule_count == 0


# ---------------------------------------------------------------------------
# 符号组合测试
# ---------------------------------------------------------------------------


class TestSymbolCombination:
    """符号组合测试 / Symbol combination tests."""

    def test_create_empty(self) -> None:
        """创建空组合。/ Create empty combination."""
        c = SymbolCombination(name="group1")
        assert c.size == 0
        assert len(c) == 0

    def test_create_with_tokens(self) -> None:
        """创建带令牌组合。/ Create with tokens."""
        tokens = (
            Token(name="a", index=0),
            Token(name="b", index=1),
        )
        c = SymbolCombination(name="group1", tokens=tokens)
        assert c.size == 2
        assert len(c) == 2

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        t = Token(name="a", index=0)
        c = SymbolCombination(name="g", tokens=(t,))
        assert c.contains(t) is True
        assert c.contains(Token(name="b", index=1)) is False

    def test_iter(self) -> None:
        """迭代。/ Iterate."""
        tokens = (
            Token(name="a", index=0),
            Token(name="b", index=1),
        )
        c = SymbolCombination(name="g", tokens=tokens)
        assert list(c) == list(tokens)

    def test_str(self) -> None:
        """字符串格式。/ String format."""
        c = SymbolCombination(name="g")
        assert str(c) == "SymbolCombination(g, size=0)"

    def test_frozen(self) -> None:
        """不可变。/ Frozen."""
        c = SymbolCombination(name="g")
        with pytest.raises(AttributeError):
            c.name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 展平工具测试
# ---------------------------------------------------------------------------


class TestFlattenUtility:
    """展平工具测试 / Flatten utility tests."""

    def test_flatten_token_like(self) -> None:
        """展平类令牌对象。/ Flatten token-like object."""
        util = FlattenUtility()
        t = Token(name="x", index=0)
        result = util.flatten(t)
        assert len(result) == 1
        assert result[0] == t

    def test_flatten_nested(self) -> None:
        """展平嵌套结构。/ Flatten nested structure."""

        class Node:
            def __init__(self, tokens):
                self.tokens = tokens

        t1 = Token(name="a", index=0)
        t2 = Token(name="b", index=1)
        t3 = Token(name="c", index=2)
        inner = Node([t2, t3])
        outer = Node([t1, inner])

        util = FlattenUtility()
        result = util.flatten(outer)
        assert len(result) == 3
        assert result == [t1, t2, t3]

    def test_flatten_with_token_attr(self) -> None:
        """展平带 token 属性的对象。/ Flatten object with token attr."""
        t = Token(name="x", index=0)

        class Leaf:
            def __init__(self, token):
                self.token = token

        util = FlattenUtility()
        result = util.flatten(Leaf(t))
        assert len(result) == 1
        assert result[0] == t

    def test_create_factory(self) -> None:
        """工厂方法创建。/ Factory method create."""
        util = FlattenUtility.create(max_depth=50)
        assert util._max_depth == 50

    def test_max_depth_respected(self) -> None:
        """最大深度限制。/ Max depth respected."""

        class Node:
            def __init__(self, children):
                self.tokens = children

        # Build chain deeper than max_depth
        leaf = Token(name="x", index=0)
        node = Node([leaf])
        for _ in range(200):
            node = Node([node])

        util = FlattenUtility.create(max_depth=5)
        result = util.flatten(node)
        assert len(result) == 0
