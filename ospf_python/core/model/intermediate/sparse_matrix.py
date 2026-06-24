"""稀疏矩阵 / Sparse matrix.

以字典形式存储的稀疏矩阵实现。
Sparse matrix implementation stored as a dictionary.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.core.model.intermediate.cell import Cell


@dataclass
class SparseMatrix:
    """稀疏矩阵 / Sparse matrix.

    使用单元字典存储非零元素的稀疏矩阵。
    A sparse matrix that stores non-zero elements
    using a cell dictionary.

    Attributes:
        name: 矩阵名称 / The matrix name.
        num_rows: 行数 / Number of rows.
        num_cols: 列数 / Number of columns.
        cells: 非零单元字典，键为 (行, 列) / Dictionary of
            non-zero cells, keyed by (row, col).
    """

    name: str = ""
    num_rows: int = 0
    num_cols: int = 0
    cells: dict[tuple[int, int], float] = field(
        default_factory=dict,
    )

    def set(self, row: int, col: int, value: float) -> None:
        """设置单元值 / Set a cell value.

        Args:
            row: 行索引 / The row index.
            col: 列索引 / The column index.
            value: 单元值 / The cell value.
        """
        self.cells[(row, col)] = value

    def get(
        self,
        row: int,
        col: int,
        default: float = 0.0,
    ) -> float:
        """获取单元值 / Get a cell value.

        Args:
            row: 行索引 / The row index.
            col: 列索引 / The column index.
            default: 默认值 / The default value.

        Returns:
            单元值 / The cell value.
        """
        return self.cells.get((row, col), default)

    def to_cells(self) -> list[Cell]:
        """转换为单元列表 / Convert to cell list.

        Returns:
            单元对象列表 / List of Cell objects.
        """
        return [Cell(row=r, col=c, value=v) for (r, c), v in self.cells.items()]

    @property
    def nnz(self) -> int:
        """非零元素数量 / Number of non-zero elements."""
        return len(self.cells)
