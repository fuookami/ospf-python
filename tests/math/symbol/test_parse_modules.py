"""符号解析模块测试。

Tests for symbol parsing modules: ParseResult,
NumberParser, PolynomialLexer, PolynomialParser,
and Parser.
"""

from __future__ import annotations

import pytest

from ospf_python.math.symbol.parse.number_parser import (
    NumberParser,
)
from ospf_python.math.symbol.parse.parse_result import (
    ParseResult,
)
from ospf_python.math.symbol.parse.polynomial_lexer import (
    PolynomialLexer,
    Token,
    TokenKind,
)
from ospf_python.math.symbol.parse.polynomial_parser import (
    PolynomialParser,
)
from ospf_python.math.symbol.symbol import Symbol

# ============================================================
# ParseResult
# ============================================================


class TestParseResult:
    """ParseResult 测试。/ ParseResult tests."""

    def test_ok_factory(self) -> None:
        """ok 工厂方法。/ ok factory method."""
        r = ParseResult.ok(42)
        assert r.success is True
        assert r.value == 42
        assert r.error == ""

    def test_fail_factory(self) -> None:
        """fail 工厂方法。/ fail factory method."""
        r = ParseResult.fail("bad input")
        assert r.success is False
        assert r.value is None
        assert r.error == "bad input"

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        r = ParseResult.ok(1)
        with pytest.raises(AttributeError):
            r.value = 2  # type: ignore[misc]

    def test_ok_with_none(self) -> None:
        """ok 可以包装 None。/ ok can wrap None."""
        r = ParseResult.ok(None)
        assert r.success is True
        assert r.value is None


# ============================================================
# NumberParser
# ============================================================


class TestNumberParser:
    """NumberParser 测试。/ NumberParser tests."""

    def test_parse_int(self) -> None:
        """解析整数。/ Parse integer."""
        assert NumberParser.parse("42") == 42.0

    def test_parse_float(self) -> None:
        """解析浮点数。/ Parse float."""
        assert NumberParser.parse("3.14") == pytest.approx(3.14)

    def test_parse_scientific(self) -> None:
        """解析科学记数法。/ Parse scientific notation."""
        assert NumberParser.parse("1.5e2") == pytest.approx(150.0)

    def test_parse_empty(self) -> None:
        """空字符串返回 None。/ Empty returns None."""
        assert NumberParser.parse("") is None

    def test_parse_whitespace(self) -> None:
        """纯空白返回 None。/ Whitespace only returns None."""
        assert NumberParser.parse("   ") is None

    def test_parse_invalid(self) -> None:
        """无效输入返回 None。/ Invalid returns None."""
        assert NumberParser.parse("abc") is None

    def test_parse_negative(self) -> None:
        """解析负数。/ Parse negative."""
        assert NumberParser.parse("-5") == pytest.approx(-5.0)

    def test_parse_int_value(self) -> None:
        """解析整数值。/ Parse int value."""
        assert NumberParser.parse_int("42") == 42

    def test_parse_int_negative(self) -> None:
        """解析负整数。/ Parse negative int."""
        assert NumberParser.parse_int("-7") == -7

    def test_parse_int_none_for_float(self) -> None:
        """浮点字符串返回 None。/ Float string returns None."""
        assert NumberParser.parse_int("3.14") is None

    def test_parse_int_none_for_empty(self) -> None:
        """空字符串返回 None。/ Empty returns None."""
        assert NumberParser.parse_int("") is None

    def test_is_numeric_true(self) -> None:
        """数值字符串返回 True。/ Numeric returns True."""
        assert NumberParser.is_numeric("42") is True
        assert NumberParser.is_numeric("3.14") is True
        assert NumberParser.is_numeric("-5") is True

    def test_is_numeric_false(self) -> None:
        """非数值字符串返回 False。/ Non-numeric returns False."""
        assert NumberParser.is_numeric("abc") is False
        assert NumberParser.is_numeric("") is False


# ============================================================
# PolynomialLexer
# ============================================================


class TestPolynomialLexer:
    """PolynomialLexer 测试。/ PolynomialLexer tests."""

    def test_tokenize_returns_list(self) -> None:
        """分词返回列表。/ tokenize returns list."""
        lexer = PolynomialLexer(input="1 + 2")
        tokens = lexer.tokenize()
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_tokenize_ends_with_eof(self) -> None:
        """最后一个 token 是 EOF。/ Last token is EOF."""
        lexer = PolynomialLexer(input="1 + 2")
        tokens = lexer.tokenize()
        assert tokens[-1].kind == TokenKind.EOF

    def test_tokenize_numbers(self) -> None:
        """数字字面量分词。/ Number literals tokenized."""
        lexer = PolynomialLexer(input="42 3.14")
        tokens = lexer.tokenize()
        number_tokens = [t for t in tokens if t.kind == TokenKind.NUMBER]
        assert len(number_tokens) == 2

    def test_tokenize_empty(self) -> None:
        """空输入只有 EOF。/ Empty input has only EOF."""
        lexer = PolynomialLexer(input="")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].kind == TokenKind.EOF

    def test_tokenize_operators(self) -> None:
        """运算符分词。/ Operator tokenization."""
        lexer = PolynomialLexer(input="+ - * ^ ( )")
        tokens = lexer.tokenize()
        kinds = [t.kind for t in tokens if t.kind != TokenKind.EOF]
        assert kinds == [
            TokenKind.PLUS,
            TokenKind.MINUS,
            TokenKind.STAR,
            TokenKind.CARET,
            TokenKind.LPAREN,
            TokenKind.RPAREN,
        ]

    def test_tokenize_variable(self) -> None:
        """变量分词。/ Variable tokenization."""
        lexer = PolynomialLexer(input="x y_1 alpha")
        tokens = lexer.tokenize()
        var_tokens = [t for t in tokens if t.kind == TokenKind.VARIABLE]
        assert len(var_tokens) == 3
        assert var_tokens[0].text == "x"
        assert var_tokens[1].text == "y_1"
        assert var_tokens[2].text == "alpha"

    def test_tokenize_complex_expression(self) -> None:
        """复杂表达式分词。/ Complex expression."""
        lexer = PolynomialLexer(input="3*x^2 + 2*x - 1")
        tokens = lexer.tokenize()
        kinds = [t.kind for t in tokens if t.kind != TokenKind.EOF]
        assert kinds == [
            TokenKind.NUMBER,
            TokenKind.STAR,
            TokenKind.VARIABLE,
            TokenKind.CARET,
            TokenKind.NUMBER,
            TokenKind.PLUS,
            TokenKind.NUMBER,
            TokenKind.STAR,
            TokenKind.VARIABLE,
            TokenKind.MINUS,
            TokenKind.NUMBER,
        ]

    def test_token_frozen(self) -> None:
        """Token 是 frozen。/ Token is frozen."""
        t = Token(kind=TokenKind.NUMBER, text="42")
        assert t.kind == TokenKind.NUMBER
        assert t.text == "42"
        with pytest.raises(AttributeError):
            t.text = "0"  # type: ignore[misc]

    def test_token_kind_values(self) -> None:
        """TokenKind 枚举值。/ TokenKind enum values."""
        assert TokenKind.NUMBER.value == "number"
        assert TokenKind.VARIABLE.value == "variable"
        assert TokenKind.EOF.value == "eof"
        assert TokenKind.PLUS.value == "+"
        assert TokenKind.MINUS.value == "-"
        assert TokenKind.STAR.value == "*"
        assert TokenKind.CARET.value == "^"
        assert TokenKind.LPAREN.value == "("
        assert TokenKind.RPAREN.value == ")"


# ============================================================
# PolynomialParser
# ============================================================


class TestPolynomialParser:
    """PolynomialParser 测试。/ PolynomialParser tests."""

    def test_parse_constant(self) -> None:
        """解析常数。/ Parse constant."""
        poly = PolynomialParser(expr="5").parse()
        assert len(poly.terms) == 1
        assert poly.terms[0].is_constant
        assert poly.terms[0].coefficient == 5.0

    def test_parse_variable(self) -> None:
        """解析变量。/ Parse variable."""
        poly = PolynomialParser(expr="x").parse()
        assert len(poly.terms) == 1
        x = Symbol.create("x")
        assert x in poly.terms[0].powers

    def test_parse_coefficient_variable(self) -> None:
        """解析系数变量。/ Parse coefficient variable."""
        poly = PolynomialParser(expr="3x").parse()
        assert len(poly.terms) == 1
        x = Symbol.create("x")
        assert poly.terms[0].coefficient == 3.0
        assert poly.terms[0].powers[x] == 1

    def test_parse_addition(self) -> None:
        """解析加法。/ Parse addition."""
        poly = PolynomialParser(expr="x + 1").parse()
        assert len(poly.terms) == 2

    def test_parse_subtraction(self) -> None:
        """解析减法。/ Parse subtraction."""
        poly = PolynomialParser(expr="x - 1").parse()
        assert len(poly.terms) == 2
        coeffs = [t.coefficient for t in poly.terms]
        assert 1.0 in coeffs
        assert -1.0 in coeffs

    def test_parse_power(self) -> None:
        """解析幂次。/ Parse power."""
        poly = PolynomialParser(expr="x^2").parse()
        x = Symbol.create("x")
        assert poly.terms[0].powers[x] == 2

    def test_parse_coefficient_power(self) -> None:
        """解析系数幂次。/ Parse coefficient power."""
        poly = PolynomialParser(expr="3x^2").parse()
        x = Symbol.create("x")
        assert poly.terms[0].coefficient == 3.0
        assert poly.terms[0].powers[x] == 2

    def test_parse_complex_polynomial(self) -> None:
        """解析复杂多项式。/ Parse complex polynomial."""
        poly = PolynomialParser(
            expr="3x^2 + 2x - 5",
        ).parse()
        assert len(poly.terms) == 3

    def test_parse_with_spaces(self) -> None:
        """解析带空格的表达式。/ Parse with spaces."""
        poly = PolynomialParser(expr="  x  +  1  ").parse()
        assert len(poly.terms) == 2

    def test_parse_empty(self) -> None:
        """空表达式返回零多项式。/ Empty returns zero."""
        poly = PolynomialParser(expr="").parse()
        assert poly.is_zero

    def test_parse_parenthesized(self) -> None:
        """解析括号表达式。/ Parse parenthesized."""
        poly = PolynomialParser(expr="(x + 1)").parse()
        assert len(poly.terms) == 2

    def test_parse_multiplication(self) -> None:
        """解析乘法。/ Parse multiplication."""
        poly = PolynomialParser(expr="x * y").parse()
        assert len(poly.terms) == 1
        x = Symbol.create("x")
        y = Symbol.create("y")
        assert poly.terms[0].powers[x] == 1
        assert poly.terms[0].powers[y] == 1


# ============================================================
# Parser (symbol/parser/parser.py)
# ============================================================


class TestParser:
    """Parser 组合解析器测试。/ Parser tests."""

    def test_parse_simple(self) -> None:
        """解析简单表达式。/ Parse simple expression."""
        from ospf_python.math.symbol.parser.parser import (
            Parser,
        )

        p = Parser()
        result = p.parse("x + 1")
        assert len(result.terms) == 2

    def test_parse_complex(self) -> None:
        """解析复杂表达式。/ Parse complex expression."""
        from ospf_python.math.symbol.parser.parser import (
            Parser,
        )

        p = Parser()
        result = p.parse("3x^2 + 2x - 1")
        assert len(result.terms) == 3
