"""稀疏矩阵单元 / Sparse matrix cell.

表示稀疏矩阵中的一个非零元素。
Represents a non-zero element in a sparse matrix.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cell:
    """稀疏矩阵单元 / Sparse matrix cell.

    用行索引、列索引和值表示稀疏矩阵中的一个元素。
    Represents an element in a sparse matrix using row index,
    column index, and value.

    Attributes:
        row: 行索引 / The row index.
        col: 列索引 / The column index.
        value: 元素值 / The element value.
    """

    row: int
    col: int
    value: float
