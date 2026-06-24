"""Extra tests for BlockMultiArray sparse access, to_dense.

BlockMultiArray 稀疏访问、to_dense 的额外测试。
"""

from __future__ import annotations

import pytest

from ospf_python.multiarray.block_multi_array import BlockMultiArray
from ospf_python.multiarray.shape import Shape2, Shape3

# -- Sparse access edge cases ----------------------------------------


class TestSparseAccessEdgeCases:
    """Test sparse access boundary conditions."""

    def test_large_sparse_array(self) -> None:
        """大稀疏数组 / Large sparse array."""
        block = BlockMultiArray(Shape3(d0=1000, d1=1000, d2=1000))
        block.set(0, 0, 0, 1)
        block.set(999, 999, 999, 2)
        assert block.block_count() == 2
        assert block.get(0, 0, 0) == 1
        assert block.get(999, 999, 999) == 2
        # All other positions return default
        assert block.get(500, 500, 500) == 0

    def test_overwrite_block_value(self) -> None:
        """覆盖块值 / Overwrite block value."""
        block = BlockMultiArray(Shape2(d0=5, d1=5))
        block.set(0, 0, 10)
        assert block.get(0, 0) == 10
        block.set(0, 0, 20)
        assert block.get(0, 0) == 20
        assert block.block_count() == 1

    def test_set_with_negative_default(self) -> None:
        """负默认值 / Negative default value."""
        block = BlockMultiArray(Shape2(d0=3, d1=3), default=-999)
        assert block.get(0, 0) == -999
        block.set(1, 1, 0)
        assert block.get(1, 1) == 0

    def test_set_with_float_default(self) -> None:
        """浮点默认值 / Float default value."""
        block = BlockMultiArray(Shape2(d0=3, d1=3), default=3.14)
        assert block.get(0, 0) == pytest.approx(3.14)

    def test_set_with_string_values(self) -> None:
        """字符串值 / String values."""
        block = BlockMultiArray(Shape2(d0=3, d1=3), default="")
        block.set(0, 0, "hello")
        block.set(1, 1, "world")
        assert block.get(0, 0) == "hello"
        assert block.get(1, 1) == "world"
        assert block.get(2, 2) == ""


# -- to_dense edge cases ---------------------------------------------


class TestToDenseEdgeCases:
    """Test to_dense boundary conditions."""

    def test_to_dense_3d(self) -> None:
        """3D 转稠密 / 3D to dense."""
        block = BlockMultiArray(Shape3(d0=3, d1=3, d2=3), default=0)
        block.set(0, 0, 0, 1)
        block.set(2, 2, 2, 27)
        arr = block.to_dense()
        assert arr.ndim == 3
        assert arr.size == 27
        assert arr.get(0, 0, 0) == 1
        assert arr.get(2, 2, 2) == 27
        assert arr.get(1, 1, 1) == 0

    def test_to_dense_all_default(self) -> None:
        """全默认值转稠密 / All default to dense."""
        block = BlockMultiArray(Shape2(d0=3, d1=3), default=7)
        arr = block.to_dense()
        assert arr.get(0, 0) == 7
        assert arr.get(2, 2) == 7

    def test_to_dense_full(self) -> None:
        """满填充转稠密 / Full fill to dense."""
        block = BlockMultiArray(Shape2(d0=3, d1=3))
        for i in range(3):
            for j in range(3):
                block.set(i, j, i * 3 + j)
        arr = block.to_dense()
        assert arr.get(0, 0) == 0
        assert arr.get(1, 1) == 4
        assert arr.get(2, 2) == 8

    def test_to_dense_preserves_ndim(self) -> None:
        """转稠密保持维度 / to_dense preserves ndim."""
        block = BlockMultiArray(Shape3(d0=2, d1=3, d2=4))
        arr = block.to_dense()
        assert arr.ndim == 3


# -- Map edge cases --------------------------------------------------


class TestBlockMapEdgeCases:
    """Test map boundary conditions."""

    def test_map_with_float_values(self) -> None:
        """浮点值映射 / Float value map."""
        block = BlockMultiArray(Shape2(d0=3, d1=3), default=0.0)
        block.set(0, 0, 1.5)
        block.set(1, 1, 2.5)
        mapped = block.map(lambda x: x * 2.0)
        assert mapped.get(0, 0) == pytest.approx(3.0)
        assert mapped.get(1, 1) == pytest.approx(5.0)

    def test_map_preserves_sparsity(self) -> None:
        """映射保持稀疏性 / Map preserves sparsity."""
        block = BlockMultiArray(Shape3(d0=10, d1=10, d2=10))
        block.set(0, 0, 0, 1)
        mapped = block.map(lambda x: x * 10)
        assert mapped.block_count() == 1

    def test_map_negate(self) -> None:
        """取反映射 / Negate map."""
        block = BlockMultiArray(Shape2(d0=3, d1=3), default=0)
        block.set(0, 0, 5)
        block.set(1, 1, -3)
        mapped = block.map(lambda x: -x)
        assert mapped.get(0, 0) == -5
        assert mapped.get(1, 1) == 3

    def test_map_identity(self) -> None:
        """恒等映射 / Identity map."""
        block = BlockMultiArray(Shape2(d0=3, d1=3), default=0)
        block.set(0, 0, 42)
        mapped = block.map(lambda x: x)
        assert mapped.get(0, 0) == 42


# -- BlockMultiArray shape -------------------------------------------


class TestBlockMultiArrayShape:
    """Test BlockMultiArray shape properties."""

    def test_ndim_2d(self) -> None:
        """2D 维度 / 2D ndim."""
        block = BlockMultiArray(Shape2(d0=5, d1=5))
        assert block.ndim == 2

    def test_ndim_3d(self) -> None:
        """3D 维度 / 3D ndim."""
        block = BlockMultiArray(Shape3(d0=2, d1=3, d2=4))
        assert block.ndim == 3

    def test_shape_property(self) -> None:
        """形状属性 / Shape property."""
        shape = Shape2(d0=5, d1=5)
        block = BlockMultiArray(shape)
        assert block.shape.dims == (5, 5)
