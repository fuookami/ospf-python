"""递归下降表达式解析器。

Recursive descent expression parser.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.math.symbol.expression.binary_expression import (
    BinaryExpression,
)
from ospf_python.math.symbol.expression.constant_expression import (
    ConstantExpression,
)
from ospf_python.math.symbol.expression.expression_operator import (
    ExpressionOperator,
)
from ospf_python.math.symbol.expression.parser.lexer import Lexer
from ospf_python.math.symbol.expression.parser.token import (
    Token,
    TokenType,
)
from ospf_python.math.symbol.expression.path_symbol import PathSymbol
from ospf_python.math.symbol.expression.unary_expression import (
    UnaryExpression,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.expression.expression import (
        Expression,
    )
    from ospf_python.math.symbol.expression.scalar_expression import (
        ScalarExpression,
    )


class Parser:
    """递归下降解析器，将文本解析为表达式树。

    Recursive descent parser that parses text into an expression tree.

    支持 +、-、*、/、一元负号、括号和变量名。
    Supports +, -, *, /, unary negation, parentheses, and variable names.

    语法:
        expr   -> term (('+' | '-') term)*
        term   -> factor (('*' | '/') factor)*
        factor -> '-' factor | atom
        atom   -> NUMBER | IDENT | '(' expr ')'
    """

    def __init__(self) -> None:
        self._tokens: list[Token] = []
        self._pos: int = 0

    def parse(self, text: str) -> Expression:
        """解析文本为表达式。/ Parse text into an expression.

        Args:
            text: 待解析的表达式文本。/ Expression text to parse.

        Returns:
            解析得到的表达式树。/ Parsed expression tree.
        """
        lexer = Lexer()
        self._tokens = lexer.tokenize(text)
        self._pos = 0
        result = self._parse_expr()
        return result

    def _current(self) -> Token:
        """获取当前标记。/ Get the current token."""
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        """前进到下一个标记。/ Advance to the next token."""
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, tok_type: TokenType) -> Token:
        """期望指定类型的标记。/ Expect a token of the given type."""
        tok = self._advance()
        return tok

    def _parse_expr(self) -> ScalarExpression:
        """解析加减法表达式。/ Parse addition/subtraction expression."""
        left = self._parse_term()

        while self._current().type in (TokenType.PLUS, TokenType.MINUS):
            op_tok = self._advance()
            right = self._parse_term()
            if op_tok.type == TokenType.PLUS:
                left = BinaryExpression(
                    op=ExpressionOperator.ADD,
                    lhs=left,
                    rhs=right,
                )
            else:
                left = BinaryExpression(
                    op=ExpressionOperator.SUB,
                    lhs=left,
                    rhs=right,
                )

        return left

    def _parse_term(self) -> ScalarExpression:
        """解析乘除法表达式。/ Parse multiplication/division expression."""
        left = self._parse_factor()

        while self._current().type in (TokenType.STAR, TokenType.SLASH):
            op_tok = self._advance()
            right = self._parse_factor()
            if op_tok.type == TokenType.STAR:
                left = BinaryExpression(
                    op=ExpressionOperator.MUL,
                    lhs=left,
                    rhs=right,
                )
            else:
                left = BinaryExpression(
                    op=ExpressionOperator.DIV,
                    lhs=left,
                    rhs=right,
                )

        return left

    def _parse_factor(self) -> ScalarExpression:
        """解析一元运算因子。/ Parse unary factor."""
        if self._current().type == TokenType.MINUS:
            self._advance()
            operand = self._parse_factor()
            return UnaryExpression(
                op=ExpressionOperator.NEG,
                operand=operand,
            )
        return self._parse_atom()

    def _parse_atom(self) -> ScalarExpression:
        """解析原子表达式。/ Parse atomic expression."""
        tok = self._current()

        if tok.type == TokenType.NUMBER:
            self._advance()
            value: float | int
            value = float(tok.value) if "." in tok.value else int(tok.value)
            return ConstantExpression(value=value)

        if tok.type == TokenType.IDENT:
            self._advance()
            return PathSymbol(name=tok.value)

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return expr

        # 回退：返回零常量 / Fallback: return zero constant
        return ConstantExpression(value=0)
