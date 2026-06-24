"""Tests for MultiArrayView, MappedMultiArrayView, materialize."""

from __future__ import annotations

from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.multi_array_view import (
    MappedMultiArrayView,
    MultiArrayView,
    view_of,
)
from ospf_python.multiarray.shape import Shape2, Shape3

# ── View creation ─────────────────────────────────────────────────


class TestMultiArrayViewCreation:
    def test_view_of(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        view = view_of(arr)
        assert view.ndim == 2

    def test_view_with_offsets(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        view = MultiArrayView(arr, offsets=(1, 0))
        # view[0, 0] -> source[1, 0] = 4
        assert view.get(0, 0) == 4

    def test_view_default_offsets(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        view = MultiArrayView(arr)
        assert view.get(0, 0) == 1
        assert view.get(1, 2) == 6


# ── View indexing ─────────────────────────────────────────────────


class TestMultiArrayViewIndexing:
    def test_get_element(self) -> None:
        arr = MultiArray.from_list([10, 20, 30, 40, 50, 60], Shape2(d0=2, d1=3))
        view = MultiArrayView(arr)
        assert view.get(0, 0) == 10
        assert view.get(0, 2) == 30
        assert view.get(1, 0) == 40

    def test_view_with_offset(self) -> None:
        arr = MultiArray.from_list(
            [1, 2, 3, 4, 5, 6, 7, 8, 9], Shape3(d0=3, d1=3, d2=1)
        )
        view = MultiArrayView(arr, offsets=(1, 0, 0))
        # view[0, 0, 0] -> source[1, 0, 0] = 4
        assert view.get(0, 0, 0) == 4


# ── MappedMultiArrayView ─────────────────────────────────────────


class TestMappedMultiArrayView:
    def test_mapped_view(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        view = MultiArrayView(arr)
        mapped = view.map(lambda x: x * 10)
        assert isinstance(mapped, MappedMultiArrayView)
        assert mapped.get(0, 0) == 10
        assert mapped.get(1, 2) == 60

    def test_chained_mapping_via_materialize(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        view = MultiArrayView(arr)
        # First mapping
        mapped1 = view.map(lambda x: x * 2)
        assert mapped1.get(0, 0) == 2
        # Materialize and create new view for chaining
        mat = mapped1.materialize()
        view2 = MultiArrayView(mat)
        mapped2 = view2.map(lambda x: x + 1)
        assert mapped2.get(0, 0) == 3
        assert mapped2.get(1, 2) == 13


# ── Materialize ───────────────────────────────────────────────────


class TestViewMaterialize:
    def test_materialize_view(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        view = MultiArrayView(arr)
        materialized = view.materialize()
        assert materialized.size == 6
        assert materialized.get(0, 0) == arr.get(0, 0)
        assert materialized.get(1, 2) == arr.get(1, 2)

    def test_materialize_mapped_view(self) -> None:
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        view = MultiArrayView(arr)
        mapped = view.map(lambda x: x * 2)
        materialized = mapped.materialize()
        assert materialized.get(0, 0) == 2
        assert materialized.get(1, 2) == 12

    def test_materialize_is_independent(self) -> None:
        arr = MutableMultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        view = MultiArrayView(arr)
        materialized = view.materialize()
        # Mutate source
        arr[0, 0] = 999
        # Materialized should not change
        assert materialized.get(0, 0) == 1


# ── View shape ────────────────────────────────────────────────────


class TestViewShape:
    def test_view_shape_matches_source(self) -> None:
        arr = MultiArray.zeros(Shape3(d0=2, d1=3, d2=4))
        view = MultiArrayView(arr)
        assert view.shape == arr.shape
        assert view.ndim == 3
