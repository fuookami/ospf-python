"""多项式词法分析器。

Polynomial lexer for tokenizing polynomial strings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, unique


@unique
class TokenKind(Enum):
    """词法单元类型。

    Token kind enumeration.

    Attributes:
        NUMBER: 数值字面量。/ Numeric literal.
        VARIABLE: 变量名。/ Variable name.
        PLUS: 加号 +。/ Plus sign +.
        MINUS: 减号 -。/ Minus sign -.
        STAR: 乘号 *。/ Star *.
        CARET: 幂 ^。/ Caret ^.
        LPAREN: 左括号 (。/ Left paren (.
        RPAREN: 右括号 )。/ Right paren ).
        EOF: 输入结束。/ End of input.
    """

    NUMBER = "number"
    VARIABLE = "variable"
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    CARET = "^"
    LPAREN = "("
    RPAREN = ")"
    EOF = "eof"


@dataclass(frozen=True)
class Token:
    """词法单元。

    A lexical token.

    Attributes:
        kind: 单元类型。/ Token kind.
        text: 原始文本。/ Raw text.
    """

    kind: TokenKind
    text: str


# 词法规则 / Lexical rules
_LEX_RULES: list[tuple[str, TokenKind | None]] = [
    (r"\s+", None),  # 空白跳过 / skip whitespace
    (r"\d+(\.\d*)?|\.\d+", TokenKind.NUMBER),
    (r"[a-zA-Z_]\w*", TokenKind.VARIABLE),
    (r"\+", TokenKind.PLUS),
    (r"-", TokenKind.MINUS),
    (r"\*", TokenKind.STAR),
    (r"\^", TokenKind.CARET),
    (r"\(", TokenKind.LPAREN),
    (r"\)", TokenKind.RPAREN),
]

_COMBINED_PATTERN = re.compile("|".join(f"({pattern})" for pattern, _ in _LEX_RULES))


@dataclass(frozen=True)
class PolynomialLexer:
    """多项式词法分析器。

    Tokenizes a polynomial expression string into a
    sequence of tokens.

    Attributes:
        input: 待分析的输入字符串。/ Input string.
    """

    input: str

    def tokenize(self) -> list[Token]:
        """将输入字符串分割为词法单元列表。

        Split the input string into a list of tokens.

        Returns:
            词法单元列表。/ List of tokens.
        """
        tokens: list[Token] = []
        pos = 0
        while pos < len(self.input):
            match = _COMBINED_PATTERN.match(self.input, pos)
            if match is None:
                break
            text = match.group(0)
            kind = _resolve_kind(text, match)
            if kind is not None:
                tokens.append(Token(kind=kind, text=text))
            pos = match.end()
        tokens.append(Token(kind=TokenKind.EOF, text=""))
        return tokens


def _resolve_kind(
    text: str,
    match: re.Match[str],
) -> TokenKind | None:
    """根据匹配结果确定词法单元类型。

    Determine token kind from the match result.

    Args:
        text: 匹配的文本。/ Matched text.
        match: 正则匹配对象。/ Regex match object.

    Returns:
        词法单元类型或 None。/ Token kind or None.
    """
    for idx, (_, kind) in enumerate(_LEX_RULES):
        group_idx = idx + 1
        if match.group(group_idx) is not None:
            return kind
    return None
