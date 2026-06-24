"""词法分析器。

Lexer / Tokenizer.
"""

from __future__ import annotations

from ospf_python.math.symbol.expression.parser.token import (
    Token,
    TokenType,
)

# 单字符标记映射 / Single-character token mapping
_SINGLE_CHAR: dict[str, TokenType] = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
}


class Lexer:
    """将源文本拆分为标记序列。

    Tokenizes source text into a sequence of tokens.

    支持整数、浮点数、标识符和算术运算符。
    Supports integers, floats, identifiers, and arithmetic operators.
    """

    def tokenize(self, text: str) -> list[Token]:
        """将输入文本拆分为标记列表。

        Tokenize input text into a list of tokens.

        Args:
            text: 待分析的源文本。/ Source text to tokenize.

        Returns:
            标记列表，以 EOF 结尾。/ Token list ending with EOF.
        """
        tokens: list[Token] = []
        pos = 0
        length = len(text)

        while pos < length:
            ch = text[pos]

            # 跳过空白 / Skip whitespace
            if ch in " \t\n\r":
                pos += 1
                continue

            # 数字（含负号前缀）/ Numbers (with optional negative sign)
            if ch.isdigit() or (
                ch == "-" and pos + 1 < length and text[pos + 1].isdigit()
            ):
                start = pos
                if ch == "-":
                    pos += 1
                while pos < length and text[pos].isdigit():
                    pos += 1
                if pos < length and text[pos] == ".":
                    pos += 1
                    while pos < length and text[pos].isdigit():
                        pos += 1
                tokens.append(Token(type=TokenType.NUMBER, value=text[start:pos]))
                continue

            # 标识符 / Identifiers
            if ch.isalpha() or ch == "_":
                start = pos
                while pos < length and (text[pos].isalnum() or text[pos] == "_"):
                    pos += 1
                tokens.append(Token(type=TokenType.IDENT, value=text[start:pos]))
                continue

            # 单字符标记 / Single-character tokens
            tok_type = _SINGLE_CHAR.get(ch)
            if tok_type is not None:
                tokens.append(Token(type=tok_type, value=ch))
                pos += 1
                continue

            # 未知字符，跳过 / Unknown character, skip
            pos += 1

        tokens.append(Token(type=TokenType.EOF, value=""))
        return tokens
