"""Float64 矩阵表示。

Float64 matrix representation of polynomials.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Flt64MatrixForm:
    """Float64 矩阵形式的多项式表示。

    Polynomial representation in Float64 matrix form,
    suitable for linear algebra operations.

    Attributes:
        coefficients: 系数矩阵。/ Coefficient matrix.
        row_count: 行数。/ Row count.
        col_count: 列数。/ Column count.
    """

    coefficients: tuple[float, ...]
    row_count: int
    col_count: int

    @property
    def size(self) -> int:
        """矩阵元素总数。/ Total matrix element count."""
        return self.row_count * self.col_count

    def get(self, row: int, col: int) -> float:
        """获取指定位置的系数。

        Get coefficient at specified position.

        Args:
            row: 行索引。/ Row index.
            col: 列索引。/ Column index.

        Returns:
            系数值。/ Coefficient value.
        """
        idx = row * self.col_count + col
        return self.coefficients[idx]
