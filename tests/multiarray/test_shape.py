"""Tests for Shape1-4, DynShape, StorageOrder, dimension validation."""

from __future__ import annotations

import pytest

from ospf_python.multiarray.shape import (
    DimensionMismatchingException,
    DynShape,
    Shape1,
    Shape2,
    Shape3,
    Shape4,
    StorageOrder,
)

# ── StorageOrder ──────────────────────────────────────────────────


class TestStorageOrder:
    def test_row_major_member(self) -> None:
        assert StorageOrder.ROW_MAJOR is not None

    def test_column_major_member(self) -> None:
        assert StorageOrder.COLUMN_MAJOR is not None


# ── Shape1 ────────────────────────────────────────────────────────


class TestShape1:
    def test_creation(self) -> None:
        s = Shape1(d0=5)
        assert s.ndim == 1
        assert s.size == 5

    def test_dims(self) -> None:
        s = Shape1(d0=10)
        assert s.dims == (10,)

    def test_strides_row_major(self) -> None:
        s = Shape1(d0=5)
        assert s.strides() == (1,)

    def test_strides_column_major(self) -> None:
        s = Shape1(d0=5, storage_order=StorageOrder.COLUMN_MAJOR)
        assert s.strides() == (1,)

    def test_flat_index(self) -> None:
        s = Shape1(d0=5)
        assert s.flat_index(0) == 0
        assert s.flat_index(3) == 3

    def test_negative_dimension_raises(self) -> None:
        with pytest.raises(DimensionMismatchingException):
            Shape1(d0=-1)

    def test_zero_dimension_raises(self) -> None:
        with pytest.raises(DimensionMismatchingException):
            Shape1(d0=0)

    def test_factory_method(self) -> None:
        s = Shape1.of(5)
        assert s.size == 5

    def test_default_storage_order(self) -> None:
        s = Shape1(d0=5)
        assert s.storage_order == StorageOrder.ROW_MAJOR


# ── Shape2 ────────────────────────────────────────────────────────


class TestShape2:
    def test_creation(self) -> None:
        s = Shape2(d0=3, d1=4)
        assert s.ndim == 2
        assert s.size == 12

    def test_dims(self) -> None:
        s = Shape2(d0=3, d1=4)
        assert s.dims == (3, 4)

    def test_strides_row_major(self) -> None:
        s = Shape2(d0=3, d1=4)
        assert s.strides() == (4, 1)

    def test_strides_column_major(self) -> None:
        s = Shape2(d0=3, d1=4, storage_order=StorageOrder.COLUMN_MAJOR)
        assert s.strides() == (1, 3)

    def test_flat_index_row_major(self) -> None:
        s = Shape2(d0=3, d1=4)
        # Row-major: index = row * ncols + col
        assert s.flat_index(0, 0) == 0
        assert s.flat_index(0, 3) == 3
        assert s.flat_index(1, 0) == 4
        assert s.flat_index(2, 3) == 11

    def test_flat_index_column_major(self) -> None:
        s = Shape2(d0=3, d1=4, storage_order=StorageOrder.COLUMN_MAJOR)
        # Column-major: index = col * nrows + row
        assert s.flat_index(0, 0) == 0
        assert s.flat_index(1, 0) == 1
        assert s.flat_index(0, 1) == 3

    def test_factory_method(self) -> None:
        s = Shape2.of(3, 4)
        assert s.size == 12

    def test_negative_dimension_raises(self) -> None:
        with pytest.raises(DimensionMismatchingException):
            Shape2(d0=-1, d1=4)

    def test_zero_dimension_raises(self) -> None:
        with pytest.raises(DimensionMismatchingException):
            Shape2(d0=0, d1=4)


# ── Shape3 ────────────────────────────────────────────────────────


class TestShape3:
    def test_creation(self) -> None:
        s = Shape3(d0=2, d1=3, d2=4)
        assert s.ndim == 3
        assert s.size == 24

    def test_dims(self) -> None:
        s = Shape3(d0=2, d1=3, d2=4)
        assert s.dims == (2, 3, 4)

    def test_strides_row_major(self) -> None:
        s = Shape3(d0=2, d1=3, d2=4)
        assert s.strides() == (12, 4, 1)

    def test_strides_column_major(self) -> None:
        s = Shape3(d0=2, d1=3, d2=4, storage_order=StorageOrder.COLUMN_MAJOR)
        assert s.strides() == (1, 2, 6)

    def test_flat_index_row_major(self) -> None:
        s = Shape3(d0=2, d1=3, d2=4)
        assert s.flat_index(0, 0, 0) == 0
        assert s.flat_index(0, 0, 1) == 1
        assert s.flat_index(0, 1, 0) == 4
        assert s.flat_index(1, 0, 0) == 12
        assert s.flat_index(1, 2, 3) == 23

    def test_flat_index_column_major(self) -> None:
        s = Shape3(d0=2, d1=3, d2=4, storage_order=StorageOrder.COLUMN_MAJOR)
        assert s.flat_index(0, 0, 0) == 0
        assert s.flat_index(1, 0, 0) == 1
        assert s.flat_index(0, 1, 0) == 2

    def test_factory_method(self) -> None:
        s = Shape3.of(2, 3, 4)
        assert s.size == 24


# ── Shape4 ────────────────────────────────────────────────────────


class TestShape4:
    def test_creation(self) -> None:
        s = Shape4(d0=2, d1=3, d2=4, d3=5)
        assert s.ndim == 4
        assert s.size == 120

    def test_dims(self) -> None:
        s = Shape4(d0=2, d1=3, d2=4, d3=5)
        assert s.dims == (2, 3, 4, 5)

    def test_strides_row_major(self) -> None:
        s = Shape4(d0=2, d1=3, d2=4, d3=5)
        assert s.strides() == (60, 20, 5, 1)

    def test_strides_column_major(self) -> None:
        s = Shape4(d0=2, d1=3, d2=4, d3=5, storage_order=StorageOrder.COLUMN_MAJOR)
        assert s.strides() == (1, 2, 6, 24)

    def test_first_and_last_element(self) -> None:
        s = Shape4(d0=2, d1=3, d2=4, d3=5)
        assert s.flat_index(0, 0, 0, 0) == 0
        assert s.flat_index(1, 2, 3, 4) == 119

    def test_factory_method(self) -> None:
        s = Shape4.of(2, 3, 4, 5)
        assert s.size == 120


# ── DynShape ──────────────────────────────────────────────────────


class TestDynShape:
    def test_creation_from_tuple(self) -> None:
        s = DynShape(dims=(2, 3, 4))
        assert s.ndim == 3
        assert s.size == 24

    def test_dims(self) -> None:
        s = DynShape(dims=(2, 3, 4))
        assert s.dims == (2, 3, 4)

    def test_strides_row_major(self) -> None:
        s = DynShape(dims=(2, 3, 4))
        assert s.strides() == (12, 4, 1)

    def test_strides_column_major(self) -> None:
        s = DynShape(dims=(2, 3, 4), storage_order=StorageOrder.COLUMN_MAJOR)
        assert s.strides() == (1, 2, 6)

    def test_flat_index(self) -> None:
        s = DynShape(dims=(2, 3))
        assert s.flat_index(0, 0) == 0
        assert s.flat_index(0, 2) == 2
        assert s.flat_index(1, 0) == 3

    def test_1d(self) -> None:
        s = DynShape(dims=(10,))
        assert s.ndim == 1
        assert s.size == 10
        assert s.flat_index(5) == 5

    def test_negative_dimension_raises(self) -> None:
        with pytest.raises(DimensionMismatchingException):
            DynShape(dims=(-1, 3))

    def test_equality(self) -> None:
        a = DynShape(dims=(2, 3, 4))
        b = DynShape(dims=(2, 3, 4))
        assert a == b

    def test_inequality(self) -> None:
        a = DynShape(dims=(2, 3))
        b = DynShape(dims=(3, 2))
        assert a != b
