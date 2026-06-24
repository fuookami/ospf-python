"""词法分析器标记。

Lexer tokens.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique


@unique
class TokenType(Enum):
    """标记类型枚举。

    Token type enum.
    """

    NUMBER = "NUMBER"
    IDENT = "IDENT"
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    """词法分析器标记。

    Lexer token.

    Attributes:
        type: 标记类型。/ Token type.
        value: 标记值。/ Token value.
    """

    type: TokenType
    value: str
