"""表达式模块综合测试。

Expression module comprehensive tests.

覆盖：表达式树构建、运算符重载、求值、DSL、解析器往返、
      serde 往返、布尔求值、规范化、数值运算。
Covers: expression tree construction, operator overloading,
evaluation, DSL, parser round-trip, serde round-trip,
boolean evaluation, normalization, numeric ops.
"""

from __future__ import annotations

import math

from ospf_python.math.symbol.expression import (
    BinaryExpression,
    BooleanExpression,
    BooleanExpressionAdapter,
    ConstantExpression,
    Expression,
    ExpressionOperator,
    PathSymbol,
    PropertyPath,
    ScalarExpression,
    UnaryExpression,
)
from ospf_python.math.symbol.expression.dsl import ExpressionDsl
from ospf_python.math.symbol.expression.operation import (
    NumericOps,
    evaluate_boolean,
    normalize,
)
from ospf_python.math.symbol.expression.parser import (
    Lexer,
    Parser,
    TokenType,
)
from ospf_python.math.symbol.expression.serde import (
    deserialize,
    serialize,
)

# -- PathSymbol / PropertyPath ----------------------------------------


class TestPathSymbol:
    """路径符号测试。"""

    def test_evaluate_from_bindings(self) -> None:
        """从绑定中查找值。/ Look up value from bindings."""
        sym = PathSymbol(name="x")
        assert sym.evaluate({"x": 42}) == 42

    def test_evaluate_missing_key(self) -> None:
        """缺少键时抛出 KeyError。/ Raises KeyError when missing."""
        sym = PathSymbol(name="y")
        try:
            sym.evaluate({"x": 1})
            raise AssertionError("Expected KeyError")
        except KeyError:
            pass

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        sym = PathSymbol(name="a")
        try:
            sym.name = "b"  # type: ignore[misc]
            raise AssertionError("Expected FrozenInstanceError")
        except AttributeError:
            pass

    def test_repr(self) -> None:
        """开发者表示。/ Developer representation."""
        sym = PathSymbol(name="x")
        assert repr(sym) == "PathSymbol('x')"

    def test_equality(self) -> None:
        """相同名称相等。/ Equal with same name."""
        a = PathSymbol(name="x")
        b = PathSymbol(name="x")
        assert a == b

    def test_is_scalar_expression(self) -> None:
        """是标量表达式子类。/ Is a ScalarExpression subclass."""
        sym = PathSymbol(name="x")
        assert isinstance(sym, ScalarExpression)
        assert isinstance(sym, Expression)


class TestPropertyPath:
    """属性路径测试。"""

    def test_single_segment(self) -> None:
        """单段路径。/ Single segment path."""
        pp = PropertyPath(path=("x",))
        assert pp.evaluate({"x": 99}) == 99

    def test_nested_dict(self) -> None:
        """嵌套字典路径。/ Nested dict path."""
        pp = PropertyPath(path=("obj", "a", "b"))
        bindings = {"obj": {"a": {"b": 7}}}
        assert pp.evaluate(bindings) == 7

    def test_nested_object(self) -> None:
        """嵌套对象属性路径。/ Nested object attribute path."""

        class Inner:
            b = 5

        class Outer:
            a = Inner()

        pp = PropertyPath(path=("obj", "a", "b"))
        assert pp.evaluate({"obj": Outer()}) == 5

    def test_repr(self) -> None:
        """开发者表示。/ Developer representation."""
        pp = PropertyPath(path=("a", "b", "c"))
        assert repr(pp) == "PropertyPath(a.b.c)"

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        pp = PropertyPath(path=("a",))
        try:
            pp.path = ("b",)  # type: ignore[misc]
            raise AssertionError("Expected FrozenInstanceError")
        except AttributeError:
            pass


# -- ConstantExpression ------------------------------------------------


class TestConstantExpression:
    """常量表达式测试。"""

    def test_evaluate_int(self) -> None:
        """整数常量求值。/ Integer constant evaluation."""
        c = ConstantExpression(value=10)
        assert c.evaluate({}) == 10

    def test_evaluate_float(self) -> None:
        """浮点常量求值。/ Float constant evaluation."""
        c = ConstantExpression(value=3.14)
        assert c.evaluate({}) == 3.14

    def test_repr(self) -> None:
        """开发者表示。/ Developer representation."""
        c = ConstantExpression(value=42)
        assert repr(c) == "Constant(42)"


# -- Operator Overloading ----------------------------------------------


class TestScalarOperatorOverloading:
    """标量运算符重载测试。"""

    def test_add(self) -> None:
        """加法。/ Addition."""
        x = PathSymbol(name="x")
        result = x + ConstantExpression(value=1)
        assert isinstance(result, BinaryExpression)
        assert result.op == ExpressionOperator.ADD
        assert result.evaluate({"x": 5}) == 6

    def test_sub(self) -> None:
        """减法。/ Subtraction."""
        x = PathSymbol(name="x")
        result = x - ConstantExpression(value=2)
        assert isinstance(result, BinaryExpression)
        assert result.op == ExpressionOperator.SUB
        assert result.evaluate({"x": 10}) == 8

    def test_mul(self) -> None:
        """乘法。/ Multiplication."""
        x = PathSymbol(name="x")
        result = x * ConstantExpression(value=3)
        assert isinstance(result, BinaryExpression)
        assert result.op == ExpressionOperator.MUL
        assert result.evaluate({"x": 4}) == 12

    def test_truediv(self) -> None:
        """除法。/ Division."""
        x = PathSymbol(name="x")
        result = x / ConstantExpression(value=2)
        assert isinstance(result, BinaryExpression)
        assert result.op == ExpressionOperator.DIV
        assert result.evaluate({"x": 10}) == 5.0

    def test_neg(self) -> None:
        """取负。/ Negation."""
        x = PathSymbol(name="x")
        result = -x
        assert isinstance(result, UnaryExpression)
        assert result.op == ExpressionOperator.NEG
        assert result.evaluate({"x": 7}) == -7

    def test_coerce_native_value(self) -> None:
        """原生值自动转为常量。/ Native value auto-coerced to constant."""
        x = PathSymbol(name="x")
        result = x + 5
        assert isinstance(result, BinaryExpression)
        assert result.evaluate({"x": 3}) == 8

    def test_chained_operations(self) -> None:
        """链式运算。/ Chained operations."""
        x = PathSymbol(name="x")
        expr = (x + 1) * 2
        assert expr.evaluate({"x": 3}) == 8

    def test_sub_expression_type(self) -> None:
        """子表达式返回标量表达式。/ Sub-expression returns scalar."""
        x = PathSymbol(name="x")
        result = x + 1
        assert isinstance(result, ScalarExpression)


class TestBooleanOperatorOverloading:
    """布尔运算符重载测试。"""

    def test_and(self) -> None:
        """逻辑与。/ Logical AND."""
        a = BooleanExpressionAdapter(ConstantExpression(value=True))
        b = BooleanExpressionAdapter(ConstantExpression(value=False))
        result = a & b
        assert isinstance(result, BooleanExpression)
        assert result.evaluate({}) is False

    def test_or(self) -> None:
        """逻辑或。/ Logical OR."""
        a = BooleanExpressionAdapter(ConstantExpression(value=True))
        b = BooleanExpressionAdapter(ConstantExpression(value=False))
        result = a | b
        assert result.evaluate({}) is True

    def test_invert(self) -> None:
        """逻辑非。/ Logical NOT."""
        a = BooleanExpressionAdapter(ConstantExpression(value=True))
        result = ~a
        assert result.evaluate({}) is False

    def test_and_with_native(self) -> None:
        """与原生布尔值运算。/ AND with native boolean."""
        a = BooleanExpressionAdapter(ConstantExpression(value=True))
        result = a & False
        assert result.evaluate({}) is False


# -- ExpressionDsl -----------------------------------------------------


class TestExpressionDsl:
    """表达式 DSL 测试。"""

    def test_var(self) -> None:
        """创建变量。/ Create variable."""
        x = ExpressionDsl.var("x")
        assert isinstance(x, PathSymbol)
        assert x.name == "x"

    def test_const(self) -> None:
        """创建常量。/ Create constant."""
        c = ExpressionDsl.const(42)
        assert isinstance(c, ConstantExpression)
        assert c.value == 42

    def test_add(self) -> None:
        """DSL 加法。/ DSL addition."""
        x = ExpressionDsl.var("x")
        c = ExpressionDsl.const(1)
        expr = ExpressionDsl.add(x, c)
        assert expr.evaluate({"x": 5}) == 6

    def test_mul(self) -> None:
        """DSL 乘法。/ DSL multiplication."""
        x = ExpressionDsl.var("x")
        c = ExpressionDsl.const(3)
        expr = ExpressionDsl.mul(x, c)
        assert expr.evaluate({"x": 4}) == 12

    def test_sub(self) -> None:
        """DSL 减法。/ DSL subtraction."""
        x = ExpressionDsl.var("x")
        expr = ExpressionDsl.sub(x, ExpressionDsl.const(2))
        assert expr.evaluate({"x": 10}) == 8

    def test_div(self) -> None:
        """DSL 除法。/ DSL division."""
        x = ExpressionDsl.var("x")
        expr = ExpressionDsl.div(x, ExpressionDsl.const(2))
        assert expr.evaluate({"x": 10}) == 5.0

    def test_neg(self) -> None:
        """DSL 取负。/ DSL negation."""
        x = ExpressionDsl.var("x")
        expr = ExpressionDsl.neg(x)
        assert expr.evaluate({"x": 3}) == -3

    def test_and_expr(self) -> None:
        """DSL 逻辑与。/ DSL logical AND."""
        a = ExpressionDsl.const(True)
        b = ExpressionDsl.const(False)
        expr = ExpressionDsl.and_expr(a, b)
        assert expr.evaluate({}) is False

    def test_or_expr(self) -> None:
        """DSL 逻辑或。/ DSL logical OR."""
        a = ExpressionDsl.const(True)
        b = ExpressionDsl.const(False)
        expr = ExpressionDsl.or_expr(a, b)
        assert expr.evaluate({}) is True

    def test_not_expr(self) -> None:
        """DSL 逻辑非。/ DSL logical NOT."""
        a = ExpressionDsl.const(True)
        expr = ExpressionDsl.not_expr(a)
        assert expr.evaluate({}) is False

    def test_complex_tree(self) -> None:
        """复杂表达式树。/ Complex expression tree."""
        x = ExpressionDsl.var("x")
        y = ExpressionDsl.var("y")
        # (x + 1) * (y - 2)
        expr = ExpressionDsl.mul(
            ExpressionDsl.add(x, ExpressionDsl.const(1)),
            ExpressionDsl.sub(y, ExpressionDsl.const(2)),
        )
        assert expr.evaluate({"x": 3, "y": 5}) == 12


# -- Evaluate / Bindings -----------------------------------------------


class TestEvaluate:
    """表达式求值测试。"""

    def test_constant_evaluate(self) -> None:
        """常量求值。/ Constant evaluation."""
        c = ConstantExpression(value=99)
        assert c.evaluate({}) == 99

    def test_variable_evaluate(self) -> None:
        """变量求值。/ Variable evaluation."""
        x = PathSymbol(name="x")
        assert x.evaluate({"x": 7}) == 7

    def test_binary_evaluate(self) -> None:
        """二元运算求值。/ Binary evaluation."""
        expr = BinaryExpression(
            op=ExpressionOperator.MUL,
            lhs=PathSymbol(name="x"),
            rhs=ConstantExpression(value=2),
        )
        assert expr.evaluate({"x": 5}) == 10

    def test_unary_evaluate(self) -> None:
        """一元运算求值。/ Unary evaluation."""
        expr = UnaryExpression(
            op=ExpressionOperator.NEG,
            operand=ConstantExpression(value=3),
        )
        assert expr.evaluate({}) == -3

    def test_nested_evaluate(self) -> None:
        """嵌套表达式求值。/ Nested expression evaluation."""
        # (x + y) * z
        expr = BinaryExpression(
            op=ExpressionOperator.MUL,
            lhs=BinaryExpression(
                op=ExpressionOperator.ADD,
                lhs=PathSymbol(name="x"),
                rhs=PathSymbol(name="y"),
            ),
            rhs=PathSymbol(name="z"),
        )
        assert expr.evaluate({"x": 2, "y": 3, "z": 4}) == 20

    def test_float_arithmetic(self) -> None:
        """浮点运算。/ Float arithmetic."""
        expr = BinaryExpression(
            op=ExpressionOperator.DIV,
            lhs=ConstantExpression(value=7.0),
            rhs=ConstantExpression(value=2.0),
        )
        assert math.isclose(expr.evaluate({}), 3.5)


# -- Parser ------------------------------------------------------------


class TestLexer:
    """词法分析器测试。"""

    def test_simple_expression(self) -> None:
        """简单表达式标记化。/ Simple expression tokenization."""
        lexer = Lexer()
        tokens = lexer.tokenize("x + 1")
        types = [t.type for t in tokens]
        assert types == [
            TokenType.IDENT,
            TokenType.PLUS,
            TokenType.NUMBER,
            TokenType.EOF,
        ]

    def test_parentheses(self) -> None:
        """括号标记化。/ Parentheses tokenization."""
        lexer = Lexer()
        tokens = lexer.tokenize("(a * b)")
        types = [t.type for t in tokens]
        assert types == [
            TokenType.LPAREN,
            TokenType.IDENT,
            TokenType.STAR,
            TokenType.IDENT,
            TokenType.RPAREN,
            TokenType.EOF,
        ]

    def test_negative_number(self) -> None:
        """负数标记化。/ Negative number tokenization."""
        lexer = Lexer()
        tokens = lexer.tokenize("-3.14")
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "-3.14"


class TestParser:
    """递归下降解析器测试。"""

    def test_simple_addition(self) -> None:
        """简单加法。/ Simple addition."""
        parser = Parser()
        expr = parser.parse("x + 1")
        assert expr.evaluate({"x": 5}) == 6

    def test_operator_precedence(self) -> None:
        """运算符优先级。/ Operator precedence."""
        parser = Parser()
        # 2 + 3 * 4 == 14
        expr = parser.parse("2 + 3 * 4")
        assert expr.evaluate({}) == 14

    def test_parentheses(self) -> None:
        """括号改变优先级。/ Parentheses override precedence."""
        parser = Parser()
        # (2 + 3) * 4 == 20
        expr = parser.parse("(2 + 3) * 4")
        assert expr.evaluate({}) == 20

    def test_unary_negation(self) -> None:
        """一元取负。/ Unary negation."""
        parser = Parser()
        expr = parser.parse("-x")
        assert expr.evaluate({"x": 5}) == -5

    def test_complex_expression(self) -> None:
        """复杂表达式。/ Complex expression."""
        parser = Parser()
        expr = parser.parse("(a + b) * (c - d) / e")
        result = expr.evaluate({"a": 2, "b": 3, "c": 7, "d": 2, "e": 5})
        assert result == 5.0

    def test_nested_parentheses(self) -> None:
        """嵌套括号。/ Nested parentheses."""
        parser = Parser()
        expr = parser.parse("((x))")
        assert expr.evaluate({"x": 42}) == 42

    def test_single_number(self) -> None:
        """单独数字。/ Single number."""
        parser = Parser()
        expr = parser.parse("42")
        assert expr.evaluate({}) == 42

    def test_single_variable(self) -> None:
        """单独变量。/ Single variable."""
        parser = Parser()
        expr = parser.parse("y")
        assert expr.evaluate({"y": 99}) == 99


# -- Serde Round-Trip --------------------------------------------------


class TestSerde:
    """序列化往返测试。"""

    def test_serialize_constant(self) -> None:
        """序列化常量。/ Serialize constant."""
        expr = ConstantExpression(value=42)
        assert serialize(expr) == "42"

    def test_serialize_variable(self) -> None:
        """序列化变量。/ Serialize variable."""
        expr = PathSymbol(name="x")
        assert serialize(expr) == "x"

    def test_serialize_binary(self) -> None:
        """序列化二元运算。/ Serialize binary."""
        expr = BinaryExpression(
            op=ExpressionOperator.ADD,
            lhs=PathSymbol(name="x"),
            rhs=ConstantExpression(value=1),
        )
        assert serialize(expr) == "(+ x 1)"

    def test_serialize_unary(self) -> None:
        """序列化一元运算。/ Serialize unary."""
        expr = UnaryExpression(
            op=ExpressionOperator.NEG,
            operand=PathSymbol(name="x"),
        )
        assert serialize(expr) == "(- x)"

    def test_serialize_complex(self) -> None:
        """序列化复杂表达式。/ Serialize complex expression."""
        # (x + 1) * 2
        expr = BinaryExpression(
            op=ExpressionOperator.MUL,
            lhs=BinaryExpression(
                op=ExpressionOperator.ADD,
                lhs=PathSymbol(name="x"),
                rhs=ConstantExpression(value=1),
            ),
            rhs=ConstantExpression(value=2),
        )
        assert serialize(expr) == "(* (+ x 1) 2)"

    def test_deserialize_constant(self) -> None:
        """反序列化常量。/ Deserialize constant."""
        expr = deserialize("42")
        assert isinstance(expr, ConstantExpression)
        assert expr.evaluate({}) == 42

    def test_deserialize_variable(self) -> None:
        """反序列化变量。/ Deserialize variable."""
        expr = deserialize("x")
        assert isinstance(expr, PathSymbol)
        assert expr.evaluate({"x": 7}) == 7

    def test_deserialize_binary(self) -> None:
        """反序列化二元运算。/ Deserialize binary."""
        expr = deserialize("(+ x 1)")
        assert expr.evaluate({"x": 5}) == 6

    def test_deserialize_unary(self) -> None:
        """反序列化一元运算。/ Deserialize unary."""
        expr = deserialize("(- x)")
        assert expr.evaluate({"x": 3}) == -3

    def test_round_trip_simple(self) -> None:
        """简单往返。/ Simple round-trip."""
        original = BinaryExpression(
            op=ExpressionOperator.ADD,
            lhs=PathSymbol(name="x"),
            rhs=ConstantExpression(value=1),
        )
        text = serialize(original)
        restored = deserialize(text)
        assert restored.evaluate({"x": 5}) == original.evaluate({"x": 5})

    def test_round_trip_complex(self) -> None:
        """复杂往返。/ Complex round-trip."""
        original = BinaryExpression(
            op=ExpressionOperator.MUL,
            lhs=BinaryExpression(
                op=ExpressionOperator.ADD,
                lhs=PathSymbol(name="a"),
                rhs=PathSymbol(name="b"),
            ),
            rhs=ConstantExpression(value=3),
        )
        text = serialize(original)
        restored = deserialize(text)
        bindings = {"a": 2, "b": 4}
        assert restored.evaluate(bindings) == original.evaluate(bindings)

    def test_round_trip_unary(self) -> None:
        """一元运算往返。/ Unary round-trip."""
        original = UnaryExpression(
            op=ExpressionOperator.NEG,
            operand=PathSymbol(name="x"),
        )
        text = serialize(original)
        restored = deserialize(text)
        assert restored.evaluate({"x": 10}) == -10

    def test_serialize_property_path(self) -> None:
        """序列化属性路径。/ Serialize property path."""
        pp = PropertyPath(path=("a", "b", "c"))
        assert serialize(pp) == "a.b.c"


# -- evaluate_boolean --------------------------------------------------


class TestEvaluateBoolean:
    """布尔求值测试。"""

    def test_true_constant(self) -> None:
        """真常量。/ True constant."""
        expr = ConstantExpression(value=True)
        assert evaluate_boolean(expr, {}) is True

    def test_false_constant(self) -> None:
        """假常量。/ False constant."""
        expr = ConstantExpression(value=False)
        assert evaluate_boolean(expr, {}) is False

    def test_truthy_value(self) -> None:
        """真值转换。/ Truthy conversion."""
        expr = ConstantExpression(value=1)
        assert evaluate_boolean(expr, {}) is True

    def test_falsy_value(self) -> None:
        """假值转换。/ Falsy conversion."""
        expr = ConstantExpression(value=0)
        assert evaluate_boolean(expr, {}) is False

    def test_and_expression(self) -> None:
        """逻辑与求值。/ AND evaluation."""
        expr = BinaryExpression(
            op=ExpressionOperator.AND,
            lhs=ConstantExpression(value=True),
            rhs=ConstantExpression(value=False),
        )
        assert evaluate_boolean(expr, {}) is False

    def test_not_expression(self) -> None:
        """逻辑非求值。/ NOT evaluation."""
        expr = UnaryExpression(
            op=ExpressionOperator.NOT,
            operand=ConstantExpression(value=True),
        )
        assert evaluate_boolean(expr, {}) is False


# -- normalize ---------------------------------------------------------


class TestNormalize:
    """规范化测试。"""

    def test_constant_passthrough(self) -> None:
        """常量直通。/ Constant passthrough."""
        c = ConstantExpression(value=5)
        result = normalize(c)
        assert isinstance(result, ConstantExpression)
        assert result.value == 5

    def test_variable_passthrough(self) -> None:
        """变量直通。/ Variable passthrough."""
        x = PathSymbol(name="x")
        result = normalize(x)
        assert isinstance(result, PathSymbol)

    def test_constant_folding(self) -> None:
        """常量折叠。/ Constant folding."""
        expr = BinaryExpression(
            op=ExpressionOperator.ADD,
            lhs=ConstantExpression(value=2),
            rhs=ConstantExpression(value=3),
        )
        result = normalize(expr)
        assert isinstance(result, ConstantExpression)
        assert result.value == 5

    def test_mixed_not_folded(self) -> None:
        """混合表达式不折叠。/ Mixed expression not folded."""
        expr = BinaryExpression(
            op=ExpressionOperator.ADD,
            lhs=PathSymbol(name="x"),
            rhs=ConstantExpression(value=1),
        )
        result = normalize(expr)
        assert isinstance(result, BinaryExpression)
        assert result.evaluate({"x": 5}) == 6

    def test_partial_folding(self) -> None:
        """部分折叠。/ Partial folding."""
        # (2 + 3) * x -> 5 * x
        inner = BinaryExpression(
            op=ExpressionOperator.ADD,
            lhs=ConstantExpression(value=2),
            rhs=ConstantExpression(value=3),
        )
        expr = BinaryExpression(
            op=ExpressionOperator.MUL,
            lhs=inner,
            rhs=PathSymbol(name="x"),
        )
        result = normalize(expr)
        assert isinstance(result, BinaryExpression)
        assert isinstance(result.lhs, ConstantExpression)
        assert result.lhs.value == 5
        assert result.evaluate({"x": 4}) == 20

    def test_unary_constant_folding(self) -> None:
        """一元常量折叠。/ Unary constant folding."""
        expr = UnaryExpression(
            op=ExpressionOperator.NEG,
            operand=ConstantExpression(value=5),
        )
        result = normalize(expr)
        assert isinstance(result, ConstantExpression)
        assert result.value == -5


# -- NumericOps --------------------------------------------------------


class TestNumericOps:
    """数值运算构建器测试。"""

    def test_add_expr(self) -> None:
        """加法。/ Addition."""
        x = PathSymbol(name="x")
        c = ConstantExpression(value=1)
        expr = NumericOps.add_expr(x, c)
        assert expr.evaluate({"x": 5}) == 6

    def test_sub_expr(self) -> None:
        """减法。/ Subtraction."""
        x = PathSymbol(name="x")
        c = ConstantExpression(value=2)
        expr = NumericOps.sub_expr(x, c)
        assert expr.evaluate({"x": 10}) == 8

    def test_mul_expr(self) -> None:
        """乘法。/ Multiplication."""
        x = PathSymbol(name="x")
        c = ConstantExpression(value=3)
        expr = NumericOps.mul_expr(x, c)
        assert expr.evaluate({"x": 4}) == 12

    def test_div_expr(self) -> None:
        """除法。/ Division."""
        x = PathSymbol(name="x")
        c = ConstantExpression(value=2)
        expr = NumericOps.div_expr(x, c)
        assert expr.evaluate({"x": 10}) == 5.0

    def test_neg_expr(self) -> None:
        """取负。/ Negation."""
        x = PathSymbol(name="x")
        expr = NumericOps.neg_expr(x)
        assert expr.evaluate({"x": 7}) == -7


# -- ExpressionOperator Enum -------------------------------------------


class TestExpressionOperator:
    """运算符枚举测试。"""

    def test_all_members(self) -> None:
        """所有成员。/ All members."""
        members = list(ExpressionOperator)
        assert len(members) == 14

    def test_scalar_ops(self) -> None:
        """标量运算符。/ Scalar operators."""
        assert ExpressionOperator.ADD.value == "add"
        assert ExpressionOperator.SUB.value == "sub"
        assert ExpressionOperator.MUL.value == "mul"
        assert ExpressionOperator.DIV.value == "div"
        assert ExpressionOperator.NEG.value == "neg"

    def test_boolean_ops(self) -> None:
        """布尔运算符。/ Boolean operators."""
        assert ExpressionOperator.AND.value == "and"
        assert ExpressionOperator.OR.value == "or"
        assert ExpressionOperator.NOT.value == "not"

    def test_comparison_ops(self) -> None:
        """比较运算符。/ Comparison operators."""
        assert ExpressionOperator.EQ.value == "eq"
        assert ExpressionOperator.NE.value == "ne"
        assert ExpressionOperator.LT.value == "lt"
        assert ExpressionOperator.LE.value == "le"
        assert ExpressionOperator.GT.value == "gt"
        assert ExpressionOperator.GE.value == "ge"


# -- Repr --------------------------------------------------------------


class TestRepr:
    """repr 测试。"""

    def test_binary_repr(self) -> None:
        """二元表达式 repr。/ Binary expression repr."""
        expr = BinaryExpression(
            op=ExpressionOperator.ADD,
            lhs=PathSymbol(name="x"),
            rhs=ConstantExpression(value=1),
        )
        r = repr(expr)
        assert "+" in r
        assert "PathSymbol('x')" in r
        assert "Constant(1)" in r

    def test_unary_repr(self) -> None:
        """一元表达式 repr。/ Unary expression repr."""
        expr = UnaryExpression(
            op=ExpressionOperator.NEG,
            operand=PathSymbol(name="x"),
        )
        r = repr(expr)
        assert "-" in r
        assert "PathSymbol('x')" in r

    def test_boolean_adapter_repr(self) -> None:
        """布尔适配器 repr。/ Boolean adapter repr."""
        inner = ConstantExpression(value=True)
        adapter = BooleanExpressionAdapter(inner)
        assert repr(adapter) == repr(inner)
