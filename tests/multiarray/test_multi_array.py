"""Tests for MultiArray and MutableMultiArray creation, access, operations."""

from __future__ import annotations

from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import (
    DynShape,
    Shape1,
    Shape2,
    Shape3,
    Shape4,
)

# ── Creation ──────────────────────────────────────────────────────


class TestMultiArrayCreation:
    def test_zeros(self) -> None:
        arr = MultiArray.zeros(Shape2(d0=3, d1=4))
        assert arr.size == 12
        assert arr.ndim == 2
        assert arr.get(0, 0) == 0.0
        assert arr.get(2, 3) == 0.0

    def test_ones(self) -> None:
        arr = MultiArray.ones(Shape2(d0=2, d1=3))
        assert arr.size == 6
        assert arr.get(0, 0) == 1.0
        assert arr.get(1, 2) == 1.0

    def test_full(self) -> None:
        arr = MultiArray.full(Shape2(d0=2, d1=3), 42)
        assert arr.get(0, 0) == 42
        assert arr.get(1, 2) == 42

    def test_from_list(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        assert arr.size == 6
        assert arr.get(0, 0) == 1
        assert arr.get(1, 2) == 6

    def test_create_1d(self) -> None:
        arr = MultiArray.full(Shape1(d0=5), 42)
        assert arr.size == 5
        assert arr.ndim == 1

    def test_create_3d(self) -> None:
        arr = MultiArray.zeros(Shape3(d0=2, d1=3, d2=4))
        assert arr.size == 24
        assert arr.ndim == 3

    def test_create_4d(self) -> None:
        arr = MultiArray.ones(Shape4(d0=2, d1=3, d2=4, d3=5))
        assert arr.size == 120
        assert arr.ndim == 4

    def test_create_with_dyn_shape(self) -> None:
        arr = MultiArray.zeros(DynShape(dims=(3, 4)))
        assert arr.size == 12


# ── Access (get) ──────────────────────────────────────────────────


class TestMultiArrayAccess:
    def test_get_by_multidim_index(self) -> None:
        arr = MultiArray.from_list([10, 20, 30, 40, 50, 60], Shape2(d0=2, d1=3))
        assert arr.get(0, 0) == 10
        assert arr.get(0, 2) == 30
        assert arr.get(1, 2) == 60

    def test_getitem_tuple(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        assert arr[0, 0] == 1
        assert arr[0, 2] == 3
        assert arr[1, 0] == 4
        assert arr[1, 2] == 6

    def test_getitem_single_int(self) -> None:
        arr = MultiArray.from_list([10, 20, 30], Shape1(d0=3))
        assert arr[0] == 10
        assert arr[2] == 30


# ── MutableMultiArray ─────────────────────────────────────────────


class TestMutableMultiArray:
    def test_create_and_modify(self) -> None:
        arr = MutableMultiArray.zeros(Shape2(d0=2, d1=3))
        arr[0, 0] = 99
        assert arr[0, 0] == 99

    def test_set_method(self) -> None:
        arr = MutableMultiArray.zeros(Shape2(d0=2, d1=3))
        arr.set(0, 0, 42)
        assert arr.get(0, 0) == 42

    def test_to_immutable(self) -> None:
        mut = MutableMultiArray.full(Shape2(d0=2, d1=3), 5)
        imm = mut.to_immutable()
        assert imm[0, 0] == 5
        assert imm.size == 6

    def test_from_list(self) -> None:
        arr = MutableMultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        arr[0, 0] = 99
        assert arr[0, 0] == 99

    def test_zeros(self) -> None:
        arr = MutableMultiArray.zeros(Shape1(d0=5))
        for i in range(5):
            assert arr.get(i) == 0.0

    def test_ones(self) -> None:
        arr = MutableMultiArray.ones(Shape2(d0=2, d1=2))
        assert arr.get(0, 0) == 1.0
        assert arr.get(1, 1) == 1.0

    def test_full(self) -> None:
        arr = MutableMultiArray.full(Shape2(d0=2, d1=2), 7)
        assert arr.get(0, 0) == 7
        assert arr.get(1, 1) == 7


# ── Map / Transform ───────────────────────────────────────────────


class TestMultiArrayMap:
    def test_map_elements(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5], Shape1(d0=5))
        mapped = arr.map(lambda x: x * 2)
        for i in range(5):
            assert mapped.get(i) == (i + 1) * 2

    def test_map_to_different_type(self) -> None:
        arr = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        mapped = arr.map(lambda x: str(x))
        assert mapped.get(0) == "1"
        assert mapped.get(2) == "3"


# ── Reduce ────────────────────────────────────────────────────────


class TestMultiArrayReduce:
    def test_sum(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5], Shape1(d0=5))
        total = arr.reduce(lambda a, b: a + b)
        assert total == 15

    def test_product(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4], Shape1(d0=4))
        product = arr.reduce(lambda a, b: a * b)
        assert product == 24


# ── Flatten ───────────────────────────────────────────────────────


class TestMultiArrayFlatten:
    def test_flatten(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        flat = arr.flatten()
        assert flat.size == 6
        assert flat.ndim == 1
        assert flat.get(0) == 1
        assert flat.get(5) == 6


# ── Transpose ─────────────────────────────────────────────────────


class TestMultiArrayTranspose:
    def test_transpose_2d(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        transposed = arr.transpose()
        # Original: [[1,2,3],[4,5,6]] -> Transposed: [[1,4],[2,5],[3,6]]
        assert transposed.ndim == 2
        # transposed[0,0] = arr[0,0] = 1
        assert transposed[0, 0] == 1
        # transposed[1,0] = arr[0,1] = 2
        assert transposed[1, 0] == 2
        # transposed[0,1] = arr[1,0] = 4
        assert transposed[0, 1] == 4


# ── Reshape ───────────────────────────────────────────────────────


class TestMultiArrayReshape:
    def test_reshape(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape1(d0=6))
        reshaped = arr.reshape(DynShape(dims=(2, 3)))
        assert reshaped.ndim == 2
        assert reshaped.size == 6


# ── to_list ───────────────────────────────────────────────────────


class TestMultiArrayToList:
    def test_to_list_1d(self) -> None:
        arr = MultiArray.from_list([10, 20, 30, 40, 50], Shape1(d0=5))
        lst = arr.to_list()
        assert lst == [10, 20, 30, 40, 50]

    def test_to_list_2d(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        lst = arr.to_list()
        assert lst == [[1, 2, 3], [4, 5, 6]]


# ── Collection interface ─────────────────────────────────────────


class TestMultiArrayCollection:
    def test_len(self) -> None:
        arr = MultiArray.zeros(Shape2(d0=3, d1=4))
        assert len(arr) == 12

    def test_iter(self) -> None:
        arr = MultiArray.from_list([10, 20, 30, 40], Shape1(d0=4))
        values = list(arr)
        assert values == [10, 20, 30, 40]

    def test_eq(self) -> None:
        a = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        b = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        assert a == b

    def test_neq(self) -> None:
        a = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        b = MultiArray.from_list([1, 2, 4], Shape1(d0=3))
        assert a != b


# ── flat_map ──────────────────────────────────────────────────────


class TestMultiArrayFlatMap:
    def test_flat_map(self) -> None:
        arr = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        result = arr.flat_map(lambda x: [x, x * 10])
        # flat_map applies the function and flattens the results
        # The underlying data contains all expanded values
        assert result._data.tolist() == [1, 10, 2, 20, 3, 30]
