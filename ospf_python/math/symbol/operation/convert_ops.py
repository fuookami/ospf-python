"""转换运算操作。

Conversion operations for polynomials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ospf_python.math.symbol.operation.convert import (
        PolynomialConverter,
    )

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True)
class ConvertOps(Generic[T, U]):
    """转换运算操作集。

    Collection of conversion operations.

    Attributes:
        converter: 多项式转换器。/ Polynomial converter.
    """

    converter: PolynomialConverter[T, U]

    def to_target(self, source: T) -> U:
        """转换为目标类型。

        Convert to target type.

        Args:
            source: 源多项式。/ Source polynomial.

        Returns:
            目标类型的多项式。/ Target polynomial.
        """
        return self.converter.convert(source)
