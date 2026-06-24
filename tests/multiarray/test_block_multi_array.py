"""Tests for BlockMultiArray block storage and sparse access."""

from __future__ import annotations

from ospf_python.multiarray.block_multi_array import BlockMultiArray
from ospf_python.multiarray.shape import Shape2, Shape3

# ── Creation ──────────────────────────────────────────────────────


class TestBlockMultiArrayCreation:
    def test_create_with_shape(self) -> None:
        block = BlockMultiArray(Shape3(d0=10, d1=10, d2=10))
        assert block.ndim == 3
        assert block.block_count() == 0

    def test_create_with_default(self) -> None:
        block = BlockMultiArray(Shape2(d0=5, d1=5), default=0)
        assert block.get(0, 0) == 0


# ── Get/Set ───────────────────────────────────────────────────────


class TestBlockMultiArrayAccess:
    def test_set_and_get(self) -> None:
        block = BlockMultiArray(Shape3(d0=10, d1=10, d2=10))
        block.set(0, 0, 0, 1)
        block.set(5, 5, 5, 2)
        assert block.get(0, 0, 0) == 1
        assert block.get(5, 5, 5) == 2

    def test_get_unset_returns_default(self) -> None:
        block = BlockMultiArray(Shape2(d0=5, d1=5), default=0)
        assert block.get(0, 0) == 0

    def test_get_custom_default(self) -> None:
        block = BlockMultiArray(Shape2(d0=5, d1=5), default=-1)
        assert block.get(3, 3) == -1

    def test_set_multiple(self) -> None:
        block = BlockMultiArray(Shape2(d0=3, d1=3))
        for i in range(3):
            for j in range(3):
                block.set(i, j, i * 3 + j)
        assert block.block_count() == 9
        assert block.get(1, 2) == 5


# ── Sparse access ─────────────────────────────────────────────────


class TestBlockMultiArraySparse:
    def test_only_stores_set_values(self) -> None:
        block = BlockMultiArray(Shape3(d0=100, d1=100, d2=100))
        block.set(0, 0, 0, 1)
        block.set(99, 99, 99, 2)
        assert block.block_count() == 2

    def test_blocks_dict(self) -> None:
        block = BlockMultiArray(Shape2(d0=3, d1=3))
        block.set(0, 0, 10)
        block.set(2, 2, 20)
        blocks = block.blocks()
        assert len(blocks) == 2


# ── Conversion ────────────────────────────────────────────────────


class TestBlockMultiArrayConversion:
    def test_to_dense(self) -> None:
        block = BlockMultiArray(Shape2(d0=3, d1=3), default=0)
        block.set(0, 0, 1)
        block.set(1, 1, 2)
        block.set(2, 2, 3)
        arr = block.to_dense()
        assert arr.get(0, 0) == 1
        assert arr.get(1, 1) == 2
        assert arr.get(2, 2) == 3
        assert arr.get(0, 1) == 0  # default

    def test_to_dense_preserves_shape(self) -> None:
        block = BlockMultiArray(Shape2(d0=3, d1=4))
        arr = block.to_dense()
        assert arr.ndim == 2
        assert arr.size == 12


# ── Map ───────────────────────────────────────────────────────────


class TestBlockMultiArrayMap:
    def test_map(self) -> None:
        block = BlockMultiArray(Shape2(d0=3, d1=3), default=0)
        block.set(0, 0, 1)
        block.set(1, 1, 2)
        mapped = block.map(lambda x: x * 10)
        assert mapped.get(0, 0) == 10
        assert mapped.get(1, 1) == 20
        assert mapped.get(2, 2) == 0  # default mapped

    def test_map_changes_default(self) -> None:
        block = BlockMultiArray(Shape2(d0=3, d1=3), default=1)
        mapped = block.map(lambda x: x * 10)
        assert mapped.get(2, 2) == 10  # default was 1, mapped to 10
