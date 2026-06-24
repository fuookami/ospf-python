"""Extra tests for DynShape edge cases, strides computation.

DynShape 边界情况、步长计算的额外测试。
"""

from __future__ import annotations

import pytest

from ospf_python.multiarray.shape import (
    DynShape,
    Shape1,
    Shape2,
    Shape3,
    Shape4,
    StorageOrder,
    _compute_strides,
)

# -- DynShape edge cases ---------------------------------------------


class TestDynShapeEdgeCases:
    """Test DynShape boundary conditions."""

    def test_5d_shape(self) -> None:
        """5 维形状 / 5-D shape."""
        s = DynShape(dims=(2, 3, 4, 5, 6))
        assert s.ndim == 5
        assert s.size == 720

    def test_single_dim(self) -> None:
        """单维形状 / Single dimension shape."""
        s = DynShape(dims=(100,))
        assert s.ndim == 1
        assert s.size == 100

    def test_all_ones(self) -> None:
        """全 1 维度 / All ones dimensions."""
        s = DynShape(dims=(1, 1, 1, 1))
        assert s.ndim == 4
        assert s.size == 1

    def test_mixed_dims(self) -> None:
        """混合维度 / Mixed dimensions."""
        s = DynShape(dims=(1, 5, 1, 3))
        assert s.ndim == 4
        assert s.size == 15

    def test_column_major_strides_5d(self) -> None:
        """列优先 5 维步长 / Column-major 5-D strides."""
        s = DynShape(
            dims=(2, 3, 4, 5, 6),
            storage_order=StorageOrder.COLUMN_MAJOR,
        )
        strides = s.strides()
        assert strides[0] == 1
        assert strides[1] == 2
        assert strides[2] == 6
        assert strides[3] == 24
        assert strides[4] == 120

    def test_row_major_strides_5d(self) -> None:
        """行优先 5 维步长 / Row-major 5-D strides."""
        s = DynShape(dims=(2, 3, 4, 5, 6))
        strides = s.strides()
        assert strides[4] == 1
        assert strides[3] == 6
        assert strides[2] == 30
        assert strides[1] == 120
        assert strides[0] == 360

    def test_flat_index_5d(self) -> None:
        """5 维扁平索引 / 5-D flat index."""
        s = DynShape(dims=(2, 3, 4, 5, 6))
        assert s.flat_index(0, 0, 0, 0, 0) == 0
        assert s.flat_index(1, 2, 3, 4, 5) == s.size - 1

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        s = DynShape(dims=(2, 3))
        with pytest.raises(AttributeError):
            s.dims = (3, 4)  # type: ignore[misc]

    def test_equality_different_dims(self) -> None:
        """不同维度不相等 / Different dims not equal."""
        a = DynShape(dims=(2, 3))
        b = DynShape(dims=(3, 2))
        assert a != b

    def test_equality_same_dims(self) -> None:
        """相同维度相等 / Same dims equal."""
        a = DynShape(dims=(2, 3))
        b = DynShape(dims=(2, 3))
        assert a == b


# -- Strides computation edge cases ----------------------------------


class TestStridesComputation:
    """Test _compute_strides helper."""

    def test_empty_dims(self) -> None:
        """空维度返回空步长 / Empty dims returns empty strides."""
        assert _compute_strides((), StorageOrder.ROW_MAJOR) == ()

    def test_single_dim_row_major(self) -> None:
        """单维行优先步长 / Single dim row-major stride."""
        assert _compute_strides((10,), StorageOrder.ROW_MAJOR) == (1,)

    def test_single_dim_column_major(self) -> None:
        """单维列优先步长 / Single dim column-major stride."""
        assert _compute_strides((10,), StorageOrder.COLUMN_MAJOR) == (1,)

    def test_2d_row_major(self) -> None:
        """2 维行优先步长 / 2-D row-major strides."""
        assert _compute_strides((3, 4), StorageOrder.ROW_MAJOR) == (4, 1)

    def test_2d_column_major(self) -> None:
        """2 维列优先步长 / 2-D column-major strides."""
        assert _compute_strides((3, 4), StorageOrder.COLUMN_MAJOR) == (1, 3)

    def test_3d_row_major(self) -> None:
        """3 维行优先步长 / 3-D row-major strides."""
        assert _compute_strides((2, 3, 4), StorageOrder.ROW_MAJOR) == (
            12,
            4,
            1,
        )

    def test_3d_column_major(self) -> None:
        """3 维列优先步长 / 3-D column-major strides."""
        assert _compute_strides((2, 3, 4), StorageOrder.COLUMN_MAJOR) == (
            1,
            2,
            6,
        )


# -- Shape equality and hashing --------------------------------------


class TestShapeEquality:
    """Test shape equality and hashing."""

    def test_shape1_equality(self) -> None:
        """Shape1 相等性 / Shape1 equality."""
        a = Shape1(d0=5)
        b = Shape1(d0=5)
        assert a == b

    def test_shape2_equality(self) -> None:
        """Shape2 相等性 / Shape2 equality."""
        a = Shape2(d0=3, d1=4)
        b = Shape2(d0=3, d1=4)
        assert a == b

    def test_shape3_hash(self) -> None:
        """Shape3 哈希 / Shape3 hash."""
        a = Shape3(d0=2, d1=3, d2=4)
        b = Shape3(d0=2, d1=3, d2=4)
        assert hash(a) == hash(b)

    def test_shape4_dims_tuple(self) -> None:
        """Shape4 维度元组 / Shape4 dims tuple."""
        s = Shape4(d0=2, d1=3, d2=4, d3=5)
        assert s.dims == (2, 3, 4, 5)
