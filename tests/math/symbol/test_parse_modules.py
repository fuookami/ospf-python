"""符号解析模块测试。

Tests for symbol parsing modules: ParseResult,
NumberParser (both versions), PolynomialLexer,
PolynomialParser, and Parser.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from ospf_python.math.symbol.parse.parse_result import ParseResult
from ospf_python.math.symbol.parse.polynomial_lexer import (
    PolynomialLexer,
    Token,
    TokenKind,
)

# ============================================================
# ParseResult
# ============================================================


class TestParseResult:
    """ParseResult 测试。/ ParseResult tests."""

    def test_of_factory(self) -> None:
        """of 工厂方法。/ of factory method."""
        r = ParseResult.of(42, " remaining")
        assert r.value == 42
        assert r.remaining == " remaining"

    def test_is_fully_consumed_true(self) -> None:
        """完全消费。/ Fully consumed."""
        r = ParseResult.of(42, "")
        assert r.is_fully_consumed is True

    def test_is_fully_consumed_with_spaces(self) -> None:
        """剩余空白视为完全消费。/ Whitespace only is consumed."""
        r = ParseResult.of(42, "   ")
        assert r.is_fully_consumed is True

    def test_is_fully_consumed_false(self) -> None:
        """有剩余输入。/ Has remaining input."""
        r = ParseResult.of(42, "more")
        assert r.is_fully_consumed is False

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        r = ParseResult.of(1, "rest")
        with pytest.raises(AttributeError):
            r.value = 2  # type: ignore[misc]


# ============================================================
# NumberParser (symbol/operation/number_parser.py)
# ============================================================


class TestOperationNumberParser:
    """symbol/operation 版 NumberParser 测试。/ Operation NumberParser tests."""

    def test_parse_int(self) -> None:
        """解析整数。/ Parse integer."""
        from ospf_python.math.symbol.operation.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="42")
        result = p.parse()
        assert result == 42
        assert isinstance(result, int)

    def test_parse_float_with_dot(self) -> None:
        """解析带小数点的浮点数。/ Parse float with dot."""
        from ospf_python.math.symbol.operation.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="3.14")
        result = p.parse()
        assert result == pytest.approx(3.14)
        assert isinstance(result, float)

    def test_parse_float_with_exponent(self) -> None:
        """解析科学记数法。/ Parse scientific notation."""
        from ospf_python.math.symbol.operation.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="1.5e2")
        result = p.parse()
        assert result == pytest.approx(150.0)

    def test_parse_fraction(self) -> None:
        """解析分数。/ Parse fraction."""
        from ospf_python.math.symbol.operation.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="3/4")
        result = p.parse()
        assert result == Fraction(3, 4)

    def test_parse_empty(self) -> None:
        """空字符串返回 None。/ Empty string returns None."""
        from ospf_python.math.symbol.operation.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="")
        assert p.parse() is None

    def test_parse_whitespace_only(self) -> None:
        """纯空白返回 None。/ Whitespace only returns None."""
        from ospf_python.math.symbol.operation.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="   ")
        assert p.parse() is None

    def test_parse_invalid(self) -> None:
        """无效输入返回 None。/ Invalid input returns None."""
        from ospf_python.math.symbol.operation.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="abc")
        assert p.parse() is None

    def test_parse_negative_int(self) -> None:
        """解析负整数。/ Parse negative integer."""
        from ospf_python.math.symbol.operation.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="-5")
        result = p.parse()
        assert result == -5


# ============================================================
# NumberParser (symbol/parse/number_parser.py)
# ============================================================


class TestParseNumberParser:
    """symbol/parse 版 NumberParser 测试。/ Parse NumberParser tests."""

    def test_parse_int(self) -> None:
        """解析整数。/ Parse integer."""
        from ospf_python.math.symbol.parse.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="42")
        result = p.parse_int()
        assert result is not None
        assert result.value == 42
        assert isinstance(result.value, int)

    def test_parse_int_none_for_float(self) -> None:
        """浮点字符串返回 None。/ Float string returns None."""
        from ospf_python.math.symbol.parse.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="3.14")
        assert p.parse_int() is None

    def test_parse_float(self) -> None:
        """解析浮点数。/ Parse float."""
        from ospf_python.math.symbol.parse.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="3.14")
        result = p.parse_float()
        assert result is not None
        assert result.value == pytest.approx(3.14)

    def test_parse_float_int_value(self) -> None:
        """整数字符串也可以解析为浮点。/ Int string as float."""
        from ospf_python.math.symbol.parse.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="42")
        result = p.parse_float()
        assert result is not None
        assert result.value == pytest.approx(42.0)

    def test_parse_fraction(self) -> None:
        """解析分数。/ Parse fraction."""
        from ospf_python.math.symbol.parse.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="3/4")
        result = p.parse_fraction()
        assert result is not None
        assert result.value == Fraction(3, 4)

    def test_parse_fraction_from_float(self) -> None:
        """浮点字符串解析为分数。/ Float string as fraction."""
        from ospf_python.math.symbol.parse.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="0.5")
        result = p.parse_fraction()
        assert result is not None
        assert isinstance(result.value, Fraction)

    def test_parse_int_none_for_empty(self) -> None:
        """空字符串返回 None。/ Empty returns None."""
        from ospf_python.math.symbol.parse.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="")
        assert p.parse_int() is None

    def test_parse_int_with_remaining(self) -> None:
        """解析后有剩余输入。/ Has remaining after parse."""
        from ospf_python.math.symbol.parse.number_parser import (
            NumberParser,
        )

        p = NumberParser(input="42 + x")
        result = p.parse_int()
        assert result is not None
        assert result.value == 42
        assert result.remaining == " + x"


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
        assert len(number_tokens) >= 1

    def test_tokenize_empty(self) -> None:
        """空输入只有 EOF。/ Empty input has only EOF."""
        lexer = PolynomialLexer(input="")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].kind == TokenKind.EOF

    def test_tokenize_operators(self) -> None:
        """运算符分词。/ Operator tokenization."""
        lexer = PolynomialLexer(input="1+2")
        tokens = lexer.tokenize()
        # At minimum should produce tokens + EOF
        assert tokens[-1].kind == TokenKind.EOF

    def test_tokenize_complex_expression(self) -> None:
        """复杂表达式分词。/ Complex expression tokenization."""
        lexer = PolynomialLexer(input="42+3.14")
        tokens = lexer.tokenize()
        assert tokens[-1].kind == TokenKind.EOF
        # Should produce at least number and operator tokens
        assert len(tokens) >= 3

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

    def test_parse_empty_tokens(self) -> None:
        """空 token 列表返回 None。/ Empty tokens returns None."""
        from ospf_python.math.symbol.parse.polynomial_parser import (
            PolynomialParser,
        )

        parser = PolynomialParser(tokens=[], polynomial_factory=str)
        assert parser.parse() is None

    def test_current_token(self) -> None:
        """获取当前 token。/ Get current token."""
        from ospf_python.math.symbol.parse.polynomial_parser import (
            PolynomialParser,
        )

        tok = Token(kind=TokenKind.NUMBER, text="42")
        parser = PolynomialParser(tokens=[tok], polynomial_factory=str)
        assert parser._current() == tok

    def test_advance(self) -> None:
        """前进到下一个 token。/ Advance to next token."""
        from ospf_python.math.symbol.parse.polynomial_parser import (
            PolynomialParser,
        )

        t1 = Token(kind=TokenKind.NUMBER, text="1")
        t2 = Token(kind=TokenKind.PLUS, text="+")
        parser = PolynomialParser(tokens=[t1, t2], polynomial_factory=str)
        current, remaining = parser._advance()
        assert current == t1
        assert remaining == [t2]


# ============================================================
# Parser (symbol/parser/parser.py)
# ============================================================


class TestParser:
    """Parser 组合解析器测试。/ Parser tests."""

    def test_parse_returns_none_for_stub(self) -> None:
        """当前实现返回 None（TODO 状态）。/ Returns None (TODO)."""
        from ospf_python.math.symbol.parser.parser import Parser

        p = Parser(polynomial_factory=str)
        result = p.parse("x + 1")
        assert result is None
