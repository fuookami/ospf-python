"""Tests for Vector, DummyIndex, MapIndex."""

from __future__ import annotations

from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import Shape1
from ospf_python.multiarray.vector import (
    IdentityMapIndex,
    OffsetMapIndex,
    SimpleDummyIndex,
    SimpleDummyIndexIterator,
    Vector,
)

# ── DummyIndex ────────────────────────────────────────────────────


class TestDummyIndex:
    def test_simple_dummy_index(self) -> None:
        idx = SimpleDummyIndex(_name="i", _range=range(5))
        assert idx.name == "i"
        assert list(idx.range) == [0, 1, 2, 3, 4]
        assert len(idx.range) == 5

    def test_dummy_index_with_custom_range(self) -> None:
        idx = SimpleDummyIndex(_name="j", _range=range(2, 5))
        assert idx.name == "j"
        assert list(idx.range) == [2, 3, 4]
        assert len(idx.range) == 3

    def test_dummy_index_single_value(self) -> None:
        idx = SimpleDummyIndex(_name="k", _range=range(3, 4))
        assert list(idx.range) == [3]
        assert len(idx.range) == 1


# ── DummyIndexIterator ───────────────────────────────────────────


class TestDummyIndexIterator:
    def test_single_index_iterator(self) -> None:
        idx = SimpleDummyIndex(_name="i", _range=range(3))
        it = SimpleDummyIndexIterator([idx])
        result = list(it)
        assert len(result) == 3
        assert result[0] == (0,)
        assert result[1] == (1,)
        assert result[2] == (2,)

    def test_cartesian_product(self) -> None:
        idx_i = SimpleDummyIndex(_name="i", _range=range(2))
        idx_j = SimpleDummyIndex(_name="j", _range=range(3))
        it = SimpleDummyIndexIterator([idx_i, idx_j])
        result = list(it)
        assert len(result) == 6
        assert result[0] == (0, 0)
        assert result[1] == (0, 1)
        assert result[2] == (0, 2)
        assert result[3] == (1, 0)
        assert result[4] == (1, 1)
        assert result[5] == (1, 2)

    def test_len(self) -> None:
        idx_i = SimpleDummyIndex(_name="i", _range=range(2))
        idx_j = SimpleDummyIndex(_name="j", _range=range(3))
        it = SimpleDummyIndexIterator([idx_i, idx_j])
        assert len(it) == 6

    def test_empty_indices(self) -> None:
        it = SimpleDummyIndexIterator([])
        result = list(it)
        assert result == [()]

    def test_single_dimension(self) -> None:
        idx = SimpleDummyIndex(_name="i", _range=range(4))
        it = SimpleDummyIndexIterator([idx])
        result = list(it)
        assert len(result) == 4
        assert result[0] == (0,)
        assert result[3] == (3,)

    def test_3d_cartesian_product(self) -> None:
        idx_i = SimpleDummyIndex(_name="i", _range=range(2))
        idx_j = SimpleDummyIndex(_name="j", _range=range(2))
        idx_k = SimpleDummyIndex(_name="k", _range=range(2))
        it = SimpleDummyIndexIterator([idx_i, idx_j, idx_k])
        result = list(it)
        assert len(result) == 8
        assert result[0] == (0, 0, 0)
        assert result[-1] == (1, 1, 1)


# ── MapIndex ─────────────────────────────────────────────────────


class TestMapIndex:
    def test_identity_map(self) -> None:
        idx = IdentityMapIndex(ndim=3)
        assert idx.map_index(0) == 0
        assert idx.map_index(2) == 2
        assert idx.map_indices((1, 2, 3)) == (1, 2, 3)

    def test_offset_map(self) -> None:
        idx = OffsetMapIndex(offset=10)
        assert idx.map_index(0) == 10
        assert idx.map_index(5) == 15
        assert idx.map_indices((1, 2, 3)) == (11, 12, 13)

    def test_offset_map_negative(self) -> None:
        idx = OffsetMapIndex(offset=-5)
        assert idx.map_index(10) == 5
        assert idx.map_index(3) == -2


# ── Vector type alias ─────────────────────────────────────────────


class TestVector:
    def test_vector_is_multi_array_1d(self) -> None:
        v: Vector[int] = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        assert v.ndim == 1
        assert v.size == 3
        assert v.get(0) == 1
        assert v.get(2) == 3
