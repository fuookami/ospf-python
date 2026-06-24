"""表达式序列化与反序列化。

Expression serialization and deserialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.math.symbol.expression.binary_expression import (
    BinaryExpression,
)
from ospf_python.math.symbol.expression.boolean_expression import (
    BooleanExpressionAdapter,
)
from ospf_python.math.symbol.expression.constant_expression import (
    ConstantExpression,
)
from ospf_python.math.symbol.expression.expression_operator import (
    ExpressionOperator,
)
from ospf_python.math.symbol.expression.path_symbol import PathSymbol
from ospf_python.math.symbol.expression.property_path import (
    PropertyPath,
)
from ospf_python.math.symbol.expression.unary_expression import (
    UnaryExpression,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.expression.expression import (
        Expression,
    )

# 运算符序列化符号 / Operator serialization symbols
_OP_SYMBOL: dict[ExpressionOperator, str] = {
    ExpressionOperator.ADD: "+",
    ExpressionOperator.SUB: "-",
    ExpressionOperator.MUL: "*",
    ExpressionOperator.DIV: "/",
    ExpressionOperator.NEG: "-",
    ExpressionOperator.AND: "&&",
    ExpressionOperator.OR: "||",
    ExpressionOperator.NOT: "!",
    ExpressionOperator.EQ: "==",
    ExpressionOperator.NE: "!=",
    ExpressionOperator.LT: "<",
    ExpressionOperator.LE: "<=",
    ExpressionOperator.GT: ">",
    ExpressionOperator.GE: ">=",
}

# 反序列化符号到运算符映射 / Deserialization symbol to operator mapping
_SYMBOL_OP: dict[str, ExpressionOperator] = {v: k for k, v in _OP_SYMBOL.items()}


def serialize(expr: Expression) -> str:
    """将表达式树序列化为字符串。

    Serialize an expression tree to a string.

    格式：S-表达式风格，如 (+ x 3)、(- (* a b))。
    Format: S-expression style, e.g. (+ x 3), (- (* a b)).

    Args:
        expr: 待序列化的表达式。/ The expression to serialize.

    Returns:
        表达式的字符串表示。/ String representation of the expression.
    """
    if isinstance(expr, PathSymbol):
        return expr.name

    if isinstance(expr, PropertyPath):
        return ".".join(expr.path)

    if isinstance(expr, ConstantExpression):
        return repr(expr.value)

    if isinstance(expr, BinaryExpression):
        sym = _OP_SYMBOL.get(expr.op, expr.op.value)
        left = serialize(expr.lhs)
        right = serialize(expr.rhs)
        return f"({sym} {left} {right})"

    if isinstance(expr, UnaryExpression):
        sym = _OP_SYMBOL.get(expr.op, expr.op.value)
        operand = serialize(expr.operand)
        return f"({sym} {operand})"

    if isinstance(expr, BooleanExpressionAdapter):
        return serialize(expr._inner)

    return repr(expr)


def deserialize(text: str) -> Expression:
    """从字符串反序列化为表达式树。

    Deserialize a string into an expression tree.

    Args:
        text: 表达式字符串。/ Expression string.

    Returns:
        反序列化后的表达式树。/ Deserialized expression tree.
    """
    tokens = _tokenize(text)
    pos = [0]

    def _parse() -> Expression:
        if pos[0] >= len(tokens):
            return ConstantExpression(value=0)

        tok = tokens[pos[0]]

        if tok == "(":
            pos[0] += 1
            op_tok = tokens[pos[0]]
            pos[0] += 1

            # 解析操作数 / Parse operands
            operands: list[Expression] = []
            while pos[0] < len(tokens) and tokens[pos[0]] != ")":
                operands.append(_parse())
            # 跳过 ')' / Skip ')'
            if pos[0] < len(tokens):
                pos[0] += 1

            op = _SYMBOL_OP.get(op_tok)
            if op is None:
                return ConstantExpression(value=0)

            if len(operands) == 1:
                return UnaryExpression(
                    op=op,
                    operand=operands[0],
                )
            if len(operands) >= 2:
                return BinaryExpression(
                    op=op,
                    lhs=operands[0],
                    rhs=operands[1],
                )
            return ConstantExpression(value=0)

        # 原子值 / Atomic value
        pos[0] += 1
        if tok.startswith("'") or tok.startswith('"'):
            return ConstantExpression(value=tok[1:-1])

        try:
            if "." in tok:
                return ConstantExpression(value=float(tok))
            return ConstantExpression(value=int(tok))
        except ValueError:
            return PathSymbol(name=tok)

    return _parse()


def _tokenize(text: str) -> list[str]:
    """将文本拆分为简单标记。/ Split text into simple tokens."""
    tokens: list[str] = []
    i = 0
    length = len(text)

    while i < length:
        ch = text[i]

        if ch in " \t\n\r":
            i += 1
            continue

        if ch in "()":
            tokens.append(ch)
            i += 1
            continue

        if ch in "'\"":
            quote = ch
            start = i
            i += 1
            while i < length and text[i] != quote:
                i += 1
            if i < length:
                i += 1
            tokens.append(text[start:i])
            continue

        start = i
        if ch == "-":
            i += 1
        while i < length and (text[i].isalnum() or text[i] in "._"):
            i += 1
        if i > start:
            tokens.append(text[start:i])
            continue

        # 运算符 / Operators
        if i + 1 < length and text[i : i + 2] in ("&&", "||", "!=", "<=", ">="):
            tokens.append(text[i : i + 2])
            i += 2
            continue

        if ch in "+-*/<>!=!":
            tokens.append(ch)
            i += 1
            continue

        i += 1

    return tokens
