"""块稀疏多维数组，适用于大规模稀疏数据。

Block-sparse multi-array for large sparse data.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

import numpy as np

from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape, Shape

# T: 元素类型 / Element type
T = TypeVar("T")

# S: 形状类型 / Shape type
S = TypeVar("S", bound=Shape)


@dataclass(frozen=True)
class IndexKey:
    """块索引键。

    Block index key. Identifies a block by its
    multi-dimensional position.

    Attributes:
        indices: 块的多维索引。/ Multi-dimensional
            block indices.
    """

    indices: tuple[int, ...]


class BlockMultiArray:
    """块稀疏多维数组。

    Block-sparse multi-array for large sparse data.

    仅存储非空块，通过索引键快速查找。
    Only non-empty blocks are stored, looked up by index key.

    Attributes:
        _shape: 数组形状。/ Array shape.
        _default: 默认值。/ Default value.
        _blocks: 块存储字典。/ Block storage dict.
    """

    def __init__(
        self,
        shape: Shape,
        *,
        default: T = 0,  # type: ignore[assignment]
    ) -> None:
        """初始化块稀疏数组。

        Initialize block-sparse array.

        Args:
            shape: 数组形状。/ Array shape.
            default: 未存储位置的默认值。
                Default value for unstored positions.
        """
        self._shape = shape
        self._default = default
        self._blocks: dict[IndexKey, T] = {}

    @property
    def shape(self) -> Shape:
        """获取数组形状。/ Get array shape."""
        return self._shape

    @property
    def ndim(self) -> int:
        """获取维度数。/ Get number of dimensions."""
        return self._shape.ndim

    def get(self, *indices: int) -> T:  # type: ignore[type-var]
        """获取指定索引处的元素。

        Get the element at the specified indices.

        如果对应块不存在，返回默认值。
        Returns the default value if no block exists.

        Args:
            indices: 多维索引。/ Multi-dimensional indices.

        Returns:
            元素值或默认值。/ Element value or default.
        """
        key = IndexKey(indices=tuple(indices))
        return self._blocks.get(key, self._default)  # type: ignore[return-value]

    def set(self, *args: int) -> None:
        """设置指定索引处的元素值。

        Set the element value at the specified indices.

        最后一个参数为值，其余为索引。
        The last argument is the value, the rest are indices.
        """
        if len(args) < 2:
            raise ValueError(
                "至少需要一个索引和一个值 / At least one index and a value are required"
            )
        *indices, value = args
        key = IndexKey(indices=tuple(indices))
        self._blocks[key] = value  # type: ignore[assignment]

    def blocks(self) -> dict[IndexKey, T]:
        """获取所有非空块的副本。

        Get a copy of all non-empty blocks.

        Returns:
            块索引到值的映射副本。
            Copy of block-index-to-value mapping.
        """
        return dict(self._blocks)  # type: ignore[arg-type]

    def block_count(self) -> int:
        """获取非空块数量。

        Get the number of non-empty blocks.

        Returns:
            非空块数量。/ Non-empty block count.
        """
        return len(self._blocks)

    def to_dense(self) -> MultiArray[Any, Any]:
        """转换为稠密数组。

        Convert to a dense MultiArray.

        Returns:
            稠密数组。/ Dense array.
        """
        data = np.full(
            self._shape.size,
            self._default,
            dtype=object,
        )
        for key, value in self._blocks.items():
            flat_idx = self._shape.flat_index(*key.indices)
            data[flat_idx] = value
        shape = DynShape(
            dims=self._shape.dims,
            storage_order=self._shape.storage_order,
        )
        return MultiArray(shape, data)

    def map(self, f: Callable[[T], T]) -> BlockMultiArray:
        """对所有非空块的值应用转换函数。

        Apply a transform function to all non-empty block values.

        Args:
            f: 转换函数。/ Transform function.

        Returns:
            新的块稀疏数组。/ New block-sparse array.
        """
        result = BlockMultiArray(
            self._shape,
            default=f(self._default),  # type: ignore[arg-type]
        )
        for key, value in self._blocks.items():
            result._blocks[key] = f(value)  # type: ignore[assignment,arg-type]
        return result
