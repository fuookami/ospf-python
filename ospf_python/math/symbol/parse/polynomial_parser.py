"""多项式语法分析器。

Polynomial parser that converts expression strings
into CanonicalPolynomial via recursive descent.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.parse.polynomial_lexer import (
    PolynomialLexer,
    Token,
    TokenKind,
)
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)
from ospf_python.math.symbol.symbol import Symbol


@dataclass(frozen=True)
class PolynomialParser:
    """多项式语法分析器。

    Parses a polynomial expression string into a
    CanonicalPolynomial using recursive descent.

    语法 / Grammar:
        expr   -> term (('+' | '-') term)*
        term   -> factor (implicit_mul factor)*
        factor -> atom ('^' NUMBER)?
        atom   -> NUMBER | VARIABLE | '(' expr ')'

    Attributes:
        expr: 待解析的表达式字符串。/
            Expression string to parse.
    """

    expr: str

    def parse(self) -> CanonicalPolynomial:
        """解析表达式为标准多项式。

        Parse the expression into a canonical polynomial.

        Returns:
            解析得到的标准多项式。/
            Parsed canonical polynomial.
        """
        lexer = PolynomialLexer(input=self.expr)
        tokens = lexer.tokenize()
        state = _ParserState(tokens)
        result = _parse_expr(state)
        return result


# ── 内部解析状态 / Internal parser state ────────────────


@dataclass
class _ParserState:
    """可变解析状态。

    Mutable parser state tracking current token position.

    Attributes:
        tokens: 词法单元列表。/ Token list.
        pos: 当前位置。/ Current position.
    """

    tokens: list[Token]
    pos: int = 0

    def current(self) -> Token:
        """获取当前词法单元。/ Get current token."""
        return self.tokens[self.pos]

    def advance(self) -> Token:
        """前进并返回上一个词法单元。/
        Advance and return previous token."""
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind: TokenKind) -> Token:
        """期望指定类型的词法单元。/
        Expect a token of the given kind."""
        tok = self.advance()
        return tok


# ── 递归下降函数 / Recursive descent functions ──────────


def _parse_expr(state: _ParserState) -> CanonicalPolynomial:
    """解析加减法表达式。

    Parse addition/subtraction expression.

    expr -> term (('+' | '-') term)*
    """
    left = _parse_term(state)

    while state.current().kind in (TokenKind.PLUS, TokenKind.MINUS):
        op = state.advance()
        right = _parse_term(state)
        if op.kind == TokenKind.PLUS:
            left = _add_polynomials(left, right)
        else:
            left = _subtract_polynomials(left, right)

    return left


def _parse_term(state: _ParserState) -> CanonicalPolynomial:
    """解析乘法项。

    Parse multiplication term.

    term -> factor (('*')? factor)*
    """
    left = _parse_factor(state)

    while state.current().kind == TokenKind.STAR:
        state.advance()
        right = _parse_factor(state)
        left = _multiply_polynomials(left, right)

    # 隐式乘法：factor 后跟 VARIABLE 或 NUMBER
    # Implicit multiplication: factor followed by
    # VARIABLE or NUMBER
    while state.current().kind in (
        TokenKind.NUMBER,
        TokenKind.VARIABLE,
        TokenKind.LPAREN,
    ):
        right = _parse_factor(state)
        left = _multiply_polynomials(left, right)

    return left


def _parse_factor(state: _ParserState) -> CanonicalPolynomial:
    """解析幂次因子。

    Parse power factor.

    factor -> atom ('^' NUMBER)?
    """
    base = _parse_atom(state)

    if state.current().kind == TokenKind.CARET:
        state.advance()
        exp_tok = state.expect(TokenKind.NUMBER)
        exp = int(exp_tok.text)
        base = _power_polynomial(base, exp)

    return base


def _parse_atom(state: _ParserState) -> CanonicalPolynomial:
    """解析原子表达式。

    Parse atomic expression.

    atom -> NUMBER | VARIABLE | NUMBER VARIABLE
            | '(' expr ')'
    """
    tok = state.current()

    # 括号表达式 / Parenthesized expression
    if tok.kind == TokenKind.LPAREN:
        state.advance()
        result = _parse_expr(state)
        state.expect(TokenKind.RPAREN)
        return result

    # 数值字面量 / Numeric literal
    if tok.kind == TokenKind.NUMBER:
        state.advance()
        coeff = float(tok.text)
        return CanonicalPolynomial.constant(coeff)

    # 变量 / Variable
    if tok.kind == TokenKind.VARIABLE:
        state.advance()
        symbol = Symbol.create(tok.text)
        mono = CanonicalMonomial.single(symbol)
        return CanonicalPolynomial.of(mono)

    # 回退：返回零多项式 / Fallback: zero polynomial
    return CanonicalPolynomial.zero()


# ── 多项式运算辅助 / Polynomial operation helpers ───────


def _add_polynomials(
    left: CanonicalPolynomial,
    right: CanonicalPolynomial,
) -> CanonicalPolynomial:
    """多项式加法。/ Polynomial addition."""
    return CanonicalPolynomial(
        terms=left.terms + right.terms,
    )


def _subtract_polynomials(
    left: CanonicalPolynomial,
    right: CanonicalPolynomial,
) -> CanonicalPolynomial:
    """多项式减法。/ Polynomial subtraction."""
    negated = [
        CanonicalMonomial(
            coefficient=-t.coefficient,
            powers=dict(t.powers),
        )
        for t in right.terms
    ]
    return CanonicalPolynomial(
        terms=left.terms + negated,
    )


def _multiply_polynomials(
    left: CanonicalPolynomial,
    right: CanonicalPolynomial,
) -> CanonicalPolynomial:
    """多项式乘法。/ Polynomial multiplication."""
    result_terms: list[CanonicalMonomial] = []
    for lt in left.terms:
        for rt in right.terms:
            new_coeff = lt.coefficient * rt.coefficient
            new_powers: dict[Symbol, int] = dict(lt.powers)
            for sym, pow in rt.powers.items():
                new_powers[sym] = new_powers.get(sym, 0) + pow
            result_terms.append(
                CanonicalMonomial(
                    coefficient=new_coeff,
                    powers=new_powers,
                ),
            )
    return CanonicalPolynomial(terms=result_terms)


def _power_polynomial(
    base: CanonicalPolynomial,
    exp: int,
) -> CanonicalPolynomial:
    """多项式幂运算。/ Polynomial exponentiation."""
    if exp == 0:
        return CanonicalPolynomial.constant(1.0)
    if exp == 1:
        return base
    result = base
    for _ in range(exp - 1):
        result = _multiply_polynomials(result, base)
    return result
