"""多项式解析器。

Polynomial parser combining lexer and parser stages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from ospf_python.math.symbol.parse.polynomial_lexer import (
    PolynomialLexer,
)
from ospf_python.math.symbol.parse.polynomial_parser import (
    PolynomialParser,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.parse.parse_result import (
        ParseResult,
    )

T = TypeVar("T")


@dataclass(frozen=True)
class Parser(Generic[T]):
    """组合式多项式解析器。

    Combines lexer and parser into a single pipeline
    for parsing polynomial strings.

    Attributes:
        polynomial_factory: 多项式工厂类型。/
            Polynomial factory type.
    """

    polynomial_factory: type[T]

    def parse(self, input: str) -> ParseResult[T] | None:
        """解析多项式字符串。

        Parse a polynomial expression string.

        Args:
            input: 多项式字符串。/ Polynomial string.

        Returns:
            解析结果或 None。/ Parse result or None.
        """
        lexer = PolynomialLexer(input=input)
        tokens = lexer.tokenize()
        parser = PolynomialParser(
            tokens=tokens,
            polynomial_factory=self.polynomial_factory,
        )
        return parser.parse()
