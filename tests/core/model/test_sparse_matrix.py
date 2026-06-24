"""SparseMatrix 测试。

测试稀疏矩阵的创建、设置和获取。
Tests SparseMatrix creation, set, and get.
"""

from __future__ import annotations

from ospf_python.core.model.intermediate.sparse_matrix import (
    SparseMatrix,
)


class TestSparseMatrix:
    """稀疏矩阵测试 / Sparse matrix tests."""

    def test_set_get(self) -> None:
        """设置和获取值。/ Set and get values."""
        sm = SparseMatrix(name="test")
        sm.set(0, 1, 3.14)
        assert sm.get(0, 1) == 3.14

    def test_get_default(self) -> None:
        """不存在的键返回默认值。/ Missing key returns default."""
        sm = SparseMatrix()
        assert sm.get(99, 99) == 0.0
        assert sm.get(99, 99, default=-1.0) == -1.0

    def test_nnz(self) -> None:
        """非零元素计数。/ Non-zero element count."""
        sm = SparseMatrix()
        sm.set(0, 0, 1.0)
        sm.set(1, 1, 2.0)
        assert sm.nnz == 2

    def test_to_cells(self) -> None:
        """转换为单元列表。/ Convert to cell list."""
        sm = SparseMatrix()
        sm.set(0, 1, 5.0)
        cells = sm.to_cells()
        assert len(cells) == 1
        assert cells[0].row == 0
        assert cells[0].col == 1
        assert cells[0].value == 5.0
