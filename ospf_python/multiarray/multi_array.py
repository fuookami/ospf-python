"""不可变与可变多维数组实现。

Immutable and mutable multi-dimensional array implementations.
"""

from __future__ import annotations

import abc
from collections.abc import Callable, Iterator, Sequence
from typing import Any, Generic, TypeVar

import numpy as np

from ospf_python.multiarray.shape import (
    DynShape,
    Shape,
    StorageOrder,
)

# T: 元素类型 / Element type
T = TypeVar("T")

# S: 形状类型 / Shape type
S = TypeVar("S", bound=Shape)


def _to_python_scalar(value: object) -> T:  # type: ignore[type-var]
    """将 numpy 标量转换为 Python 原生类型。

    Convert numpy scalar to Python native type.

    numpy 的 object dtype 数组元素已经是 Python 对象，
    数值 dtype 元素需要通过 .item() 转换。
    Elements from numpy object-dtype arrays are already
    Python objects; numeric-dtype elements need .item().

    Args:
        value: numpy 元素。/ Numpy element.

    Returns:
        Python 原生值。/ Python native value.
    """
    if hasattr(value, "item"):
        return value.item()  # type: ignore[no-any-return]
    return value  # type: ignore[return-value]


class AbstractMultiArray(abc.ABC, Generic[T, S]):
    """多维数组抽象基类。

    Abstract base class for multi-dimensional arrays.

    Attributes:
        shape: 数组形状。/ Array shape.
    """

    @property
    @abc.abstractmethod
    def shape(self) -> S:
        """获取数组形状。/ Get array shape."""
        ...

    @property
    def ndim(self) -> int:
        """获取维度数。/ Get number of dimensions."""
        return self.shape.ndim

    @property
    def size(self) -> int:
        """获取元素总数。/ Get total number of elements."""
        return self.shape.size

    @abc.abstractmethod
    def get(self, *indices: int) -> T:
        """获取指定索引处的元素。

        Get the element at the specified indices.
        """
        ...

    @abc.abstractmethod
    def to_list(self) -> list[Any]:
        """转换为嵌套 Python 列表。

        Convert to nested Python list.
        """
        ...

    @abc.abstractmethod
    def map(self, f: Callable[[T], T]) -> MultiArray[T, S]:
        """对每个元素应用转换函数，返回新数组。

        Apply a transform function to each element,
        returning a new array.
        """
        ...

    @abc.abstractmethod
    def flat_map(self, f: Callable[[T], Sequence[T]]) -> MultiArray[T, S]:
        """对每个元素应用返回序列的函数并展平。

        Apply a function returning a sequence to each
        element and flatten.
        """
        ...

    @abc.abstractmethod
    def reduce(self, f: Callable[[T, T], T]) -> T:
        """使用二元函数规约所有元素。

        Reduce all elements using a binary function.
        """
        ...

    @abc.abstractmethod
    def transpose(self) -> MultiArray[T, S]:
        """转置数组。/ Transpose the array."""
        ...

    @abc.abstractmethod
    def reshape(self, new_shape: DynShape) -> MultiArray[T, DynShape]:
        """重塑数组形状。/ Reshape the array."""
        ...

    @abc.abstractmethod
    def flatten(self) -> MultiArray[T, DynShape]:
        """展平为一维数组。/ Flatten to a 1-D array."""
        ...


class MultiArray(AbstractMultiArray[T, S]):
    """不可变多维数组，以 numpy 为后端存储。

    Immutable multi-dimensional array backed by numpy.

    Attributes:
        _shape: 数组形状。/ Array shape.
        _data: 扁平 numpy 数据。/ Flat numpy data.
    """

    def __init__(self, shape: S, data: np.ndarray) -> None:
        """初始化多维数组。

        Initialize multi-dimensional array.

        Args:
            shape: 数组形状。/ Array shape.
            data: 扁平 numpy 数组。/ Flat numpy array.
        """
        self._shape = shape
        self._data = data

    @property
    def shape(self) -> S:
        """获取数组形状。/ Get array shape."""
        return self._shape

    def get(self, *indices: int) -> T:
        """获取指定索引处的元素。

        Get the element at the specified indices.

        Args:
            indices: 多维索引。/ Multi-dimensional indices.

        Returns:
            指定位置的元素。/ Element at the position.
        """
        flat_idx = self._shape.flat_index(*indices)
        return _to_python_scalar(self._data[flat_idx])

    def __getitem__(self, indices: tuple[int, ...]) -> T:
        """通过索引元组获取元素。

        Get element by index tuple.

        Args:
            indices: 索引元组。/ Index tuple.

        Returns:
            指定位置的元素。/ Element at the position.
        """
        if isinstance(indices, int):
            indices = (indices,)
        return self.get(*indices)

    def __len__(self) -> int:
        """返回元素总数。/ Return total number of elements."""
        return self.size

    def __iter__(self) -> Iterator[T]:
        """迭代所有元素。/ Iterate over all elements."""
        for i in range(self.size):
            yield _to_python_scalar(self._data[i])

    def __eq__(self, other: object) -> bool:
        """判断两个数组是否相等。

        Check if two arrays are equal.

        Args:
            other: 另一个对象。/ Another object.

        Returns:
            是否相等。/ Whether equal.
        """
        if not isinstance(other, MultiArray):
            return NotImplemented
        if self._shape.dims != other._shape.dims:
            return False
        return bool(np.array_equal(self._data, other._data))

    def __hash__(self) -> int:
        """计算哈希值。/ Compute hash value."""
        return hash((self._shape.dims, self._data.data.tobytes()))

    def __repr__(self) -> str:
        """返回字符串表示。/ Return string representation."""
        return f"MultiArray(shape={self._shape.dims}, data={self._data.tolist()})"

    def to_list(self) -> list[Any]:
        """转换为嵌套 Python 列表。

        Convert to nested Python list.

        Returns:
            嵌套列表。/ Nested list.
        """
        reshaped = self._data.reshape(self._shape.dims)
        return reshaped.tolist()  # type: ignore[no-any-return]

    def map(self, f: Callable[[T], T]) -> MultiArray[T, S]:
        """对每个元素应用转换函数。

        Apply a transform function to each element.

        Args:
            f: 转换函数。/ Transform function.

        Returns:
            新的不可变数组。/ New immutable array.
        """
        new_data = np.array(
            [f(_to_python_scalar(self._data[i])) for i in range(self.size)]
        )
        return MultiArray(self._shape, new_data)

    def flat_map(self, f: Callable[[T], Sequence[T]]) -> MultiArray[T, S]:
        """对每个元素应用返回序列的函数并展平。

        Apply a function returning a sequence to each
        element and flatten.

        Args:
            f: 返回序列的函数。/ Function returning a sequence.

        Returns:
            新的不可变数组。/ New immutable array.
        """
        result: list[T] = []
        for i in range(self.size):
            result.extend(f(_to_python_scalar(self._data[i])))
        new_data = np.array(result)
        return MultiArray(self._shape, new_data)

    def reduce(self, f: Callable[[T, T], T]) -> T:
        """使用二元函数规约所有元素。

        Reduce all elements using a binary function.

        Args:
            f: 二元规约函数。/ Binary reduction function.

        Returns:
            规约结果。/ Reduction result.
        """
        result: T = _to_python_scalar(self._data[0])
        for i in range(1, self.size):
            result = f(result, _to_python_scalar(self._data[i]))
        return result

    def transpose(self) -> MultiArray[T, S]:
        """转置数组（反转维度顺序）。

        Transpose the array (reverse dimension order).

        Returns:
            转置后的新数组。/ New transposed array.
        """
        new_dims = tuple(reversed(self._shape.dims))
        new_strides = tuple(reversed(self._shape.strides()))
        new_data = np.empty(self.size, dtype=self._data.dtype)

        # 根据新步长重新排列元素
        # Rearrange elements according to new strides
        from ospf_python.multiarray.access_order import (
            AccessOrder,
            MultiIndexIterator,
        )

        for pos in MultiIndexIterator(
            self._shape.dims,
            access_order=AccessOrder.C_ORDER,
        ):
            old_flat = self._shape.flat_index(*pos.indices)
            new_indices = tuple(reversed(pos.indices))
            new_flat = sum(
                s * i for s, i in zip(new_strides, new_indices, strict=False)
            )
            new_data[new_flat] = self._data[old_flat]

        new_storage = (
            StorageOrder.COLUMN_MAJOR
            if self._shape.storage_order == StorageOrder.ROW_MAJOR
            else StorageOrder.ROW_MAJOR
        )
        new_shape = DynShape(dims=new_dims, storage_order=new_storage)
        return MultiArray(new_shape, new_data)  # type: ignore[arg-type]

    def reshape(self, new_shape: DynShape) -> MultiArray[T, DynShape]:
        """重塑数组形状。

        Reshape the array.

        Args:
            new_shape: 新形状。/ New shape.

        Returns:
            重塑后的新数组。/ New reshaped array.
        """
        new_data = self._data.reshape(new_shape.dims).flatten()
        return MultiArray(new_shape, new_data.copy())

    def flatten(self) -> MultiArray[T, DynShape]:
        """展平为一维数组。

        Flatten to a 1-D array.

        Returns:
            展平后的新数组。/ New flattened array.
        """
        flat_shape = DynShape(dims=(self.size,))
        return MultiArray(flat_shape, self._data.copy())

    # ==================== 工厂方法 ====================
    # ==================== Factory methods ====================

    @staticmethod
    def zeros(shape: S) -> MultiArray[float, S]:
        """创建全零数组。

        Create an array of zeros.

        Args:
            shape: 数组形状。/ Array shape.

        Returns:
            全零数组。/ Array of zeros.
        """
        data = np.zeros(shape.size, dtype=np.float64)
        return MultiArray(shape, data)

    @staticmethod
    def ones(shape: S) -> MultiArray[float, S]:
        """创建全一数组。

        Create an array of ones.

        Args:
            shape: 数组形状。/ Array shape.

        Returns:
            全一数组。/ Array of ones.
        """
        data = np.ones(shape.size, dtype=np.float64)
        return MultiArray(shape, data)

    @staticmethod
    def full(shape: S, value: T) -> MultiArray[T, S]:
        """创建填充指定值的数组。

        Create an array filled with a given value.

        Args:
            shape: 数组形状。/ Array shape.
            value: 填充值。/ Fill value.

        Returns:
            填充后的数组。/ Filled array.
        """
        data = np.full(shape.size, value)
        return MultiArray(shape, data)

    @staticmethod
    def from_list(data: Sequence[Any], shape: S) -> MultiArray[T, S]:
        """从嵌套列表创建数组。

        Create an array from a nested list.

        Args:
            data: 嵌套列表数据。/ Nested list data.
            shape: 数组形状。/ Array shape.

        Returns:
            新数组。/ New array.
        """
        flat = np.array(data, dtype=object).flatten()
        return MultiArray(shape, flat)


class MutableMultiArray(AbstractMultiArray[T, S]):
    """可变多维数组，支持元素修改。

    Mutable multi-dimensional array supporting element modification.

    Attributes:
        _shape: 数组形状。/ Array shape.
        _data: 扁平 numpy 数据。/ Flat numpy data.
    """

    def __init__(self, shape: S, data: np.ndarray) -> None:
        """初始化可变多维数组。

        Initialize mutable multi-dimensional array.

        Args:
            shape: 数组形状。/ Array shape.
            data: 扁平 numpy 数组。/ Flat numpy array.
        """
        self._shape = shape
        self._data = data

    @property
    def shape(self) -> S:
        """获取数组形状。/ Get array shape."""
        return self._shape

    def get(self, *indices: int) -> T:
        """获取指定索引处的元素。

        Get the element at the specified indices.

        Args:
            indices: 多维索引。/ Multi-dimensional indices.

        Returns:
            指定位置的元素。/ Element at the position.
        """
        flat_idx = self._shape.flat_index(*indices)
        return _to_python_scalar(self._data[flat_idx])

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
        flat_idx = self._shape.flat_index(*indices)
        self._data[flat_idx] = value

    def __getitem__(self, indices: tuple[int, ...]) -> T:
        """通过索引元组获取元素。

        Get element by index tuple.
        """
        if isinstance(indices, int):
            indices = (indices,)
        return self.get(*indices)

    def __setitem__(self, indices: tuple[int, ...], value: T) -> None:
        """通过索引元组设置元素值。

        Set element value by index tuple.
        """
        if isinstance(indices, int):
            indices = (indices,)
        flat_idx = self._shape.flat_index(*indices)
        self._data[flat_idx] = value

    def __len__(self) -> int:
        """返回元素总数。/ Return total number of elements."""
        return self.size

    def __iter__(self) -> Iterator[T]:
        """迭代所有元素。/ Iterate over all elements."""
        for i in range(self.size):
            yield _to_python_scalar(self._data[i])

    def to_list(self) -> list[Any]:
        """转换为嵌套 Python 列表。

        Convert to nested Python list.
        """
        reshaped = self._data.reshape(self._shape.dims)
        return reshaped.tolist()  # type: ignore[no-any-return]

    def map(self, f: Callable[[T], T]) -> MultiArray[T, S]:
        """对每个元素应用转换函数。

        Apply a transform function to each element.

        Args:
            f: 转换函数。/ Transform function.

        Returns:
            新的不可变数组。/ New immutable array.
        """
        new_data = np.array(
            [f(_to_python_scalar(self._data[i])) for i in range(self.size)]
        )
        return MultiArray(self._shape, new_data)

    def flat_map(self, f: Callable[[T], Sequence[T]]) -> MultiArray[T, S]:
        """对每个元素应用返回序列的函数并展平。

        Apply a function returning a sequence to each
        element and flatten.
        """
        result: list[T] = []
        for i in range(self.size):
            result.extend(f(_to_python_scalar(self._data[i])))
        new_data = np.array(result)
        return MultiArray(self._shape, new_data)

    def reduce(self, f: Callable[[T, T], T]) -> T:
        """使用二元函数规约所有元素。

        Reduce all elements using a binary function.
        """
        result: T = _to_python_scalar(self._data[0])
        for i in range(1, self.size):
            result = f(result, _to_python_scalar(self._data[i]))
        return result

    def transpose(self) -> MultiArray[T, S]:
        """转置数组（返回不可变副本）。

        Transpose the array (returns an immutable copy).
        """
        # 委托给不可变 MultiArray 的 transpose
        # Delegate to immutable MultiArray's transpose
        immutable: MultiArray[T, S] = MultiArray(self._shape, self._data.copy())
        return immutable.transpose()

    def reshape(self, new_shape: DynShape) -> MultiArray[T, DynShape]:
        """重塑数组形状（返回不可变副本）。

        Reshape the array (returns an immutable copy).
        """
        immutable: MultiArray[T, S] = MultiArray(self._shape, self._data.copy())
        return immutable.reshape(new_shape)

    def flatten(self) -> MultiArray[T, DynShape]:
        """展平为一维数组（返回不可变副本）。

        Flatten to a 1-D array (returns an immutable copy).
        """
        flat_shape = DynShape(dims=(self.size,))
        return MultiArray(flat_shape, self._data.copy())

    def to_immutable(self) -> MultiArray[T, S]:
        """转换为不可变数组。

        Convert to an immutable array.

        Returns:
            不可变数组副本。/ Immutable array copy.
        """
        return MultiArray(self._shape, self._data.copy())

    # ==================== 工厂方法 ====================
    # ==================== Factory methods ====================

    @staticmethod
    def zeros(shape: S) -> MutableMultiArray[float, S]:
        """创建全零可变数组。

        Create a mutable array of zeros.

        Args:
            shape: 数组形状。/ Array shape.

        Returns:
            全零可变数组。/ Mutable array of zeros.
        """
        data = np.zeros(shape.size, dtype=np.float64)
        return MutableMultiArray(shape, data)

    @staticmethod
    def ones(shape: S) -> MutableMultiArray[float, S]:
        """创建全一可变数组。

        Create a mutable array of ones.

        Args:
            shape: 数组形状。/ Array shape.

        Returns:
            全一可变数组。/ Mutable array of ones.
        """
        data = np.ones(shape.size, dtype=np.float64)
        return MutableMultiArray(shape, data)

    @staticmethod
    def full(shape: S, value: T) -> MutableMultiArray[T, S]:
        """创建填充指定值的可变数组。

        Create a mutable array filled with a given value.

        Args:
            shape: 数组形状。/ Array shape.
            value: 填充值。/ Fill value.

        Returns:
            填充后的可变数组。/ Filled mutable array.
        """
        data = np.full(shape.size, value)
        return MutableMultiArray(shape, data)

    @staticmethod
    def from_list(data: Sequence[Any], shape: S) -> MutableMultiArray[T, S]:
        """从嵌套列表创建可变数组。

        Create a mutable array from a nested list.

        Args:
            data: 嵌套列表数据。/ Nested list data.
            shape: 数组形状。/ Array shape.

        Returns:
            新可变数组。/ New mutable array.
        """
        flat = np.array(data, dtype=object).flatten()
        return MutableMultiArray(shape, flat)
