"""多项式解析器。

Polynomial parser combining lexer and parser stages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.math.symbol.parse.polynomial_parser import (
    PolynomialParser,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.polynomial.canonical_polynomial import (
        CanonicalPolynomial,
    )


@dataclass(frozen=True)
class Parser:
    """组合式多项式解析器。

    Combines lexer and parser into a single pipeline
    for parsing polynomial strings.
    """

    def parse(self, input: str) -> CanonicalPolynomial:
        """解析多项式字符串。

        Parse a polynomial expression string.

        Args:
            input: 多项式字符串。/ Polynomial string.

        Returns:
            解析得到的标准多项式。/
            Parsed canonical polynomial.
        """
        parser = PolynomialParser(expr=input)
        return parser.parse()
