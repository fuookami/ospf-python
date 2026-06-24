"""Extra tests for MultiArrayView chained views, materialize.

MultiArrayView 链式视图、物化的额外测试。
"""

from __future__ import annotations

from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.multi_array_view import (
    MultiArrayView,
    view_of,
)
from ospf_python.multiarray.shape import Shape1, Shape2, Shape3

# -- Chained views ---------------------------------------------------


class TestChainedViews:
    """Test chained view operations."""

    def test_view_of_view(self) -> None:
        """视图的视图 / View of view."""
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        v1 = MultiArrayView(arr)
        v2 = MultiArrayView(v1.materialize())
        assert v2.get(0, 0) == 1
        assert v2.get(1, 2) == 6

    def test_map_then_map(self) -> None:
        """映射后再次映射 / Map then map again."""
        arr = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        v = MultiArrayView(arr)
        m1 = v.map(lambda x: x * 2)
        mat = m1.materialize()
        v2 = MultiArrayView(mat)
        m2 = v2.map(lambda x: x + 10)
        assert m2.get(0) == 12
        assert m2.get(2) == 16

    def test_three_level_chained_map(self) -> None:
        """三级链式映射 / Three-level chained map."""
        arr = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        v1 = MultiArrayView(arr)
        m1 = v1.map(lambda x: x + 1)
        mat1 = m1.materialize()
        v2 = MultiArrayView(mat1)
        m2 = v2.map(lambda x: x * 3)
        mat2 = m2.materialize()
        v3 = MultiArrayView(mat2)
        m3 = v3.map(lambda x: x - 1)
        # (1+1)*3-1=5, (2+1)*3-1=8, (3+1)*3-1=11
        assert m3.get(0) == 5
        assert m3.get(1) == 8
        assert m3.get(2) == 11


# -- Materialize edge cases ------------------------------------------


class TestMaterializeEdgeCases:
    """Test materialize boundary conditions."""

    def test_materialize_preserves_values(self) -> None:
        """物化保留值 / Materialize preserves values."""
        arr = MultiArray.from_list([10, 20, 30], Shape1(d0=3))
        view = MultiArrayView(arr)
        mat = view.materialize()
        assert mat.get(0) == 10
        assert mat.get(2) == 30

    def test_materialize_with_offset(self) -> None:
        """带偏移物化 / Materialize with offset."""
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        view = MultiArrayView(arr, offsets=(1, 0))
        mat = view.materialize()
        assert mat.size == 6

    def test_materialize_preserves_dtype(self) -> None:
        """物化保留数据类型 / Materialize preserves dtype."""
        arr = MultiArray.from_list([1.5, 2.5, 3.5], Shape1(d0=3))
        view = MultiArrayView(arr)
        mat = view.materialize()
        assert mat.get(0) == 1.5

    def test_materialize_3d(self) -> None:
        """3D 物化 / 3D materialize."""
        data = list(range(24))
        arr = MultiArray.from_list(data, Shape3(d0=2, d1=3, d2=4))
        view = MultiArrayView(arr)
        mat = view.materialize()
        assert mat.ndim == 3
        assert mat.size == 24


# -- View shape and ndim ---------------------------------------------


class TestViewShapeAndNdim:
    """Test view shape and ndim properties."""

    def test_view_1d_shape(self) -> None:
        """1D 视图形状 / 1D view shape."""
        arr = MultiArray.from_list([1, 2, 3, 4, 5], Shape1(d0=5))
        view = MultiArrayView(arr)
        assert view.ndim == 1

    def test_view_3d_shape(self) -> None:
        """3D 视图形状 / 3D view shape."""
        arr = MultiArray.zeros(Shape3(d0=2, d1=3, d2=4))
        view = MultiArrayView(arr)
        assert view.ndim == 3
        assert view.shape.dims == (2, 3, 4)

    def test_mapped_view_shape(self) -> None:
        """映射视图形状 / Mapped view shape."""
        arr = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        view = MultiArrayView(arr)
        mapped = view.map(lambda x: x * 2)
        assert mapped.ndim == 1
        assert mapped.shape.dims == (3,)


# -- View with MutableMultiArray -------------------------------------


class TestViewWithMutableArray:
    """Test views backed by mutable arrays."""

    def test_view_reflects_mutation(self) -> None:
        """视图反映源数组变更 / View reflects source mutation."""
        arr = MutableMultiArray.from_list([1, 2, 3], Shape1(d0=3))
        view = MultiArrayView(arr)
        assert view.get(0) == 1
        arr[0] = 99
        assert view.get(0) == 99

    def test_mapped_view_reflects_mutation(self) -> None:
        """映射视图反映源变更 / Mapped view reflects source change."""
        arr = MutableMultiArray.from_list([1, 2, 3], Shape1(d0=3))
        view = MultiArrayView(arr)
        mapped = view.map(lambda x: x * 10)
        assert mapped.get(0) == 10
        arr[0] = 5
        assert mapped.get(0) == 50


# -- view_of factory -------------------------------------------------


class TestViewOfFactory:
    """Test view_of factory function."""

    def test_view_of_creates_view(self) -> None:
        """view_of 创建视图 / view_of creates view."""
        arr = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        v = view_of(arr)
        assert isinstance(v, MultiArrayView)
        assert v.get(0) == 1

    def test_view_of_with_offsets(self) -> None:
        """view_of 带偏移 / view_of with offsets."""
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        v = view_of(arr, offsets=(1, 0))
        assert v.get(0, 0) == 4
