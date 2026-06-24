"""MultiArray 扩展功能测试。

测试 MultiArray 的高级操作和扩展功能。
Tests MultiArray advanced operations and extensions.
"""

from __future__ import annotations

from ospf_python.multiarray.multi_array import (
    MultiArray,
    MutableMultiArray,
)
from ospf_python.multiarray.multi_array_view import (
    MappedMultiArrayView,
    MultiArrayView,
)
from ospf_python.multiarray.shape import (
    DynShape,
    Shape1,
    Shape2,
)


class TestMultiArrayAdvanced:
    """高级操作测试 / Advanced operation tests."""

    def test_transpose_2d(self) -> None:
        """二维转置。/ 2D transpose."""
        arr = MultiArray.from_list(
            [1, 2, 3, 4, 5, 6],
            Shape2(d0=2, d1=3),
        )
        transposed = arr.transpose()
        assert transposed.ndim == 2
        assert transposed[0, 0] == 1
        assert transposed[1, 0] == 2
        assert transposed[0, 1] == 4

    def test_reshape(self) -> None:
        """重塑数组。/ Reshape array."""
        arr = MultiArray.from_list(
            [1, 2, 3, 4, 5, 6],
            Shape1(d0=6),
        )
        reshaped = arr.reshape(DynShape(dims=(2, 3)))
        assert reshaped.ndim == 2
        assert reshaped.size == 6

    def test_flatten(self) -> None:
        """展平数组。/ Flatten array."""
        arr = MultiArray.from_list(
            [1, 2, 3, 4, 5, 6],
            Shape2(d0=2, d1=3),
        )
        flat = arr.flatten()
        assert flat.size == 6
        assert flat.ndim == 1

    def test_to_list_2d(self) -> None:
        """二维转列表。/ 2D to list."""
        arr = MultiArray.from_list(
            [1, 2, 3, 4, 5, 6],
            Shape2(d0=2, d1=3),
        )
        lst = arr.to_list()
        assert lst == [[1, 2, 3], [4, 5, 6]]


class TestMultiArrayViewAdvanced:
    """视图高级测试 / View advanced tests."""

    def test_view_with_offsets(self) -> None:
        """带偏移的视图。/ View with offsets."""
        arr = MultiArray.from_list(
            [1, 2, 3, 4, 5, 6],
            Shape2(d0=2, d1=3),
        )
        view = MultiArrayView(arr, offsets=(1, 0))
        assert view.get(0, 0) == 4

    def test_mapped_view(self) -> None:
        """映射视图。/ Mapped view."""
        arr = MultiArray.from_list(
            [1, 2, 3, 4, 5, 6],
            Shape2(d0=2, d1=3),
        )
        view = MultiArrayView(arr)
        mapped = view.map(lambda x: x * 10)
        assert isinstance(mapped, MappedMultiArrayView)
        assert mapped.get(0, 0) == 10
        assert mapped.get(1, 2) == 60

    def test_materialize_is_independent(self) -> None:
        """物化视图独立于源。/ Materialized is independent."""
        arr = MutableMultiArray.from_list(
            [1, 2, 3, 4, 5, 6],
            Shape2(d0=2, d1=3),
        )
        view = MultiArrayView(arr)
        materialized = view.materialize()
        arr[0, 0] = 999
        assert materialized.get(0, 0) == 1


class TestMutableMultiArrayExtensions:
    """可变数组扩展测试 / Mutable array extension tests."""

    def test_to_immutable(self) -> None:
        """转不可变数组。/ Convert to immutable."""
        mut = MutableMultiArray.full(
            Shape2(d0=2, d1=3),
            5,
        )
        imm = mut.to_immutable()
        assert imm[0, 0] == 5
        assert imm.size == 6

    def test_set_method(self) -> None:
        """set 方法。/ set method."""
        arr = MutableMultiArray.zeros(Shape2(d0=2, d1=3))
        arr.set(0, 0, 42)
        assert arr.get(0, 0) == 42
