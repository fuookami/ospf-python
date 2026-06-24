"""Extra tests for MultiArray transpose, reshape, reduce edge cases.

MultiArray 转置、重塑、规约的额外边界测试。
"""

from __future__ import annotations

from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import (
    DynShape,
    Shape1,
    Shape2,
    Shape3,
    Shape4,
)

# -- Transpose edge cases --------------------------------------------


class TestTransposeEdgeCases:
    """Test transpose boundary conditions."""

    def test_transpose_1d(self) -> None:
        """1 维转置保持不变 / 1-D transpose is identity."""
        arr = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        t = arr.transpose()
        assert t.ndim == 1
        assert t.get(0) == 1
        assert t.get(2) == 3

    def test_transpose_3d(self) -> None:
        """3 维转置 / 3-D transpose."""
        data = list(range(24))
        arr = MultiArray.from_list(data, Shape3(d0=2, d1=3, d2=4))
        t = arr.transpose()
        assert t.ndim == 3
        assert t.get(1, 0, 0) == arr.get(0, 0, 1)

    def test_transpose_preserves_values(self) -> None:
        """转置保留所有值 / Transpose preserves all values."""
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        t = arr.transpose()
        t_values = sorted(t.get(i, j) for i in range(3) for j in range(2))
        assert t_values == [1, 2, 3, 4, 5, 6]

    def test_transpose_square_matrix(self) -> None:
        """方阵转置 / Square matrix transpose."""
        arr = MultiArray.from_list([1, 2, 3, 4], Shape2(d0=2, d1=2))
        t = arr.transpose()
        assert t.get(0, 0) == 1
        assert t.get(0, 1) == 3
        assert t.get(1, 0) == 2
        assert t.get(1, 1) == 4

    def test_mutable_transpose(self) -> None:
        """可变数组转置 / Mutable array transpose."""
        arr = MutableMultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        t = arr.transpose()
        assert t.get(0, 0) == 1
        assert t.get(1, 0) == 2


# -- Reshape edge cases ----------------------------------------------


class TestReshapeEdgeCases:
    """Test reshape boundary conditions."""

    def test_reshape_2d_to_1d(self) -> None:
        """2D 到 1D 重塑 / 2D to 1D reshape."""
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        reshaped = arr.reshape(DynShape(dims=(6,)))
        assert reshaped.ndim == 1
        assert reshaped.size == 6

    def test_reshape_1d_to_3d(self) -> None:
        """1D 到 3D 重塑 / 1D to 3D reshape."""
        arr = MultiArray.from_list(list(range(12)), Shape1(d0=12))
        reshaped = arr.reshape(DynShape(dims=(2, 3, 2)))
        assert reshaped.ndim == 3
        assert reshaped.size == 12

    def test_reshape_preserves_total_size(self) -> None:
        """重塑保持总大小 / Reshape preserves total size."""
        arr = MultiArray.zeros(Shape3(d0=2, d1=3, d2=4))
        reshaped = arr.reshape(DynShape(dims=(6, 4)))
        assert reshaped.size == 24

    def test_mutable_reshape(self) -> None:
        """可变数组重塑 / Mutable array reshape."""
        arr = MutableMultiArray.from_list([1, 2, 3, 4], Shape1(d0=4))
        reshaped = arr.reshape(DynShape(dims=(2, 2)))
        assert reshaped.ndim == 2
        assert reshaped.get(0, 0) == 1

    def test_reshape_1d_to_1d(self) -> None:
        """1D 到 1D 重塑 / 1D to 1D reshape."""
        arr = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        reshaped = arr.reshape(DynShape(dims=(3,)))
        assert reshaped.ndim == 1
        assert reshaped.size == 3


# -- Reduce edge cases -----------------------------------------------


class TestReduceEdgeCases:
    """Test reduce boundary conditions."""

    def test_reduce_single_element(self) -> None:
        """单元素规约 / Single element reduce."""
        arr = MultiArray.from_list([42], Shape1(d0=1))
        result = arr.reduce(lambda a, b: a + b)
        assert result == 42

    def test_reduce_min(self) -> None:
        """最小值规约 / Min reduce."""
        arr = MultiArray.from_list([3, 1, 4, 1, 5], Shape1(d0=5))
        result = arr.reduce(lambda a, b: min(a, b))
        assert result == 1

    def test_reduce_max(self) -> None:
        """最大值规约 / Max reduce."""
        arr = MultiArray.from_list([3, 1, 4, 1, 5], Shape1(d0=5))
        result = arr.reduce(lambda a, b: max(a, b))
        assert result == 5

    def test_reduce_2d_sum(self) -> None:
        """2D 数组求和规约 / 2D array sum reduce."""
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6], Shape2(d0=2, d1=3))
        result = arr.reduce(lambda a, b: a + b)
        assert result == 21

    def test_reduce_concat_strings(self) -> None:
        """字符串拼接规约 / String concatenation reduce."""
        arr = MultiArray.from_list(["a", "b", "c"], Shape1(d0=3))
        result = arr.reduce(lambda a, b: a + b)
        assert result == "abc"


# -- Flatten edge cases ----------------------------------------------


class TestFlattenEdgeCases:
    """Test flatten boundary conditions."""

    def test_flatten_3d(self) -> None:
        """3D 展平 / 3D flatten."""
        data = list(range(24))
        arr = MultiArray.from_list(data, Shape3(d0=2, d1=3, d2=4))
        flat = arr.flatten()
        assert flat.ndim == 1
        assert flat.size == 24
        assert flat.get(0) == 0
        assert flat.get(23) == 23

    def test_flatten_already_1d(self) -> None:
        """已是 1D 再展平 / Already 1D flatten."""
        arr = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        flat = arr.flatten()
        assert flat.ndim == 1
        assert flat.size == 3

    def test_mutable_flatten(self) -> None:
        """可变数组展平 / Mutable array flatten."""
        arr = MutableMultiArray.from_list([1, 2, 3, 4], Shape2(d0=2, d1=2))
        flat = arr.flatten()
        assert flat.ndim == 1
        assert flat.size == 4


# -- to_list edge cases ----------------------------------------------


class TestToListEdgeCases:
    """Test to_list boundary conditions."""

    def test_to_list_3d(self) -> None:
        """3D 转列表 / 3D to list."""
        data = list(range(24))
        arr = MultiArray.from_list(data, Shape3(d0=2, d1=3, d2=4))
        lst = arr.to_list()
        assert len(lst) == 2
        assert len(lst[0]) == 3
        assert len(lst[0][0]) == 4

    def test_to_list_4d(self) -> None:
        """4D 转列表 / 4D to list."""
        data = list(range(120))
        arr = MultiArray.from_list(data, Shape4(d0=2, d1=3, d2=4, d3=5))
        lst = arr.to_list()
        assert len(lst) == 2
        assert lst[0][0][0][0] == 0
        assert lst[1][2][3][4] == 119


# -- map edge cases --------------------------------------------------


class TestMapEdgeCases:
    """Test map boundary conditions."""

    def test_map_identity(self) -> None:
        """恒等映射 / Identity map."""
        arr = MultiArray.from_list([1, 2, 3], Shape1(d0=3))
        mapped = arr.map(lambda x: x)
        assert mapped == arr

    def test_map_negate(self) -> None:
        """取反映射 / Negate map."""
        arr = MultiArray.from_list([1, -2, 3], Shape1(d0=3))
        mapped = arr.map(lambda x: -x)
        assert mapped.get(0) == -1
        assert mapped.get(1) == 2
        assert mapped.get(2) == -3

    def test_map_2d(self) -> None:
        """2D 映射 / 2D map."""
        arr = MultiArray.from_list([1, 2, 3, 4], Shape2(d0=2, d1=2))
        mapped = arr.map(lambda x: x * 10)
        assert mapped.get(0, 0) == 10
        assert mapped.get(1, 1) == 40

    def test_mutable_map_returns_immutable(self) -> None:
        """可变数组映射返回不可变 / Mutable map returns immutable."""
        arr = MutableMultiArray.from_list([1, 2, 3], Shape1(d0=3))
        mapped = arr.map(lambda x: x * 2)
        assert isinstance(mapped, MultiArray)
