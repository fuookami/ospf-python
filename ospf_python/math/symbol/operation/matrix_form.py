"""矩阵形式表示。

Matrix form representation of polynomials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class MatrixForm(Generic[T]):
    """多项式的矩阵形式表示。

    Matrix form representation of a polynomial, useful
    for quadratic forms and optimization.

    Attributes:
        source: 源多项式。/ Source polynomial.
        row_labels: 行标签。/ Row labels.
        col_labels: 列标签。/ Column labels.
    """

    source: T
    row_labels: tuple[str, ...]
    col_labels: tuple[str, ...]

    @property
    def rows(self) -> int:
        """行数。/ Row count."""
        return len(self.row_labels)

    @property
    def cols(self) -> int:
        """列数。/ Column count."""
        return len(self.col_labels)
