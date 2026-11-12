"""不可变与可变多维数组实现。

Immutable and mutable multi-dimensional array implementations.
"""

from __future__ import annotations

import abc
import copy
from collections.abc import Callable, Iterator, Sequence
from operator import index
from typing import Any, Generic, TypeVar, cast

import numpy as np

# 公共注解支持运行时 get_type_hints。 / Public annotations support runtime get_type_hints.
from ospf_python import _native
from ospf_python._binding import shared_nested as _shared_nested
from ospf_python._binding.public_array_access import read, read_many, write
from ospf_python._binding.result import BindingResult  # noqa: TC001
from ospf_python._binding.shared_mapping import map_shared_array
from ospf_python._binding.shared_nested import nested_shared_array
from ospf_python._binding.shared_reduction import reduce_shared_array
from ospf_python._binding.shared_transpose import transpose_shared_array
from ospf_python._binding.storage_transform import flatten_storage, reshape_storage
from ospf_python.multiarray.shape import (
    DynShape,
    Shape,
)

# T: 元素类型 / Element type
T = TypeVar("T")

# S: 形状类型 / Shape type
S = TypeVar("S", bound=Shape)

_DEFAULT_NESTED_PROTOCOL = _shared_nested._DEFAULT_PROTOCOL
_DEFAULT_NESTED_TO_LIST = _shared_nested._DEFAULT_TO_LIST


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
    if issubclass(type(value), np.generic):
        return cast("T", cast("np.generic", value).item())
    return value  # type: ignore[return-value]


def _storage_constructor() -> Callable[
    [Any, np.ndarray[Any, Any]], MultiArray[Any, Any]
]:
    """在原调用表达式的 callable 求值点捕获数组类型 / Capture the array type at the original call expression's callable evaluation point.

    Returns:
        当前公共构造器 / Current public constructor.
    """
    return MultiArray


class AbstractMultiArray(abc.ABC, Generic[T, S]):
    """多维数组抽象基类。

    Abstract base class for multi-dimensional arrays.

    Attributes:
        shape: 数组形状。/ Array shape.
    """

    # 具体类在 `__init__` 里赋值；基类先声明类型，`__deepcopy__` 才能在严格检查下访问它。
    # Concrete classes assign this in `__init__`; the base declares the type so `__deepcopy__`
    # can touch it under strict checking.
    _data: np.ndarray[Any, Any]

    def __deepcopy__(self, memo: dict[int, Any]) -> AbstractMultiArray[T, S]:
        """深拷贝，保持共享缓冲与叶子回指的别名图 / Deepcopy preserving the shared buffer and leaf back-reference graph.

        NumPy 的 ``ndarray.__deepcopy__`` 在递归拷贝 object 元素**之后**才把
        ``memo[id(buffer)]`` 写入，因此回指持有者的叶子元素会先复制出第二份缓冲，
        最后 ``copy.deepcopy`` 用第一份覆盖 memo —— 第二个持有者于是拿到独立的缓冲，
        共享关系丢失（AS-001）。

        这里把顺序反过来：先深拷贝缓冲并**立即登记**进 memo，再拷贝其余字段，
        回指叶子命中 memo 得到同一份缓冲，共享与别名图都保留。

        NumPy's ``ndarray.__deepcopy__`` writes ``memo[id(buffer)]`` only **after** recursively
        copying object elements, so a leaf that points back at the holder first produces a
        second buffer; ``copy.deepcopy`` then overwrites the memo with the first one, and the
        second holder ends up with its own buffer, losing the sharing (AS-001).

        This reverses the order: deep-copy the buffer and register it in the memo immediately,
        then copy the remaining fields, so back-referencing leaves hit the memo and both the
        sharing and the alias graph survive.

        Args:
            memo: deepcopy 记忆字典 / deepcopy memo dictionary.

        Returns:
            保持别名图的副本 / Copy preserving the alias graph.
        """
        clone = self.__class__.__new__(self.__class__)
        memo[id(self)] = clone
        # 缓冲必须第一个处理：先建同形状空缓冲并**立即登记**进 memo，再逐元素深拷贝填入。
        # 回指持有者的叶子元素会在填充过程中重入本方法，此时命中 memo 拿到同一个缓冲，
        # 共享与别名图因此保留。反过来（先让 ndarray 自己深拷贝）会在重入时复制出第二份，
        # 而 ndarray 只在内部递归完成后才登记，外层拿到的永远是错的那一份（AS-001）。
        # The buffer must be handled first: allocate a same-shaped buffer, register it in the
        # memo immediately, then fill it element by element. A leaf pointing back at the holder
        # re-enters this method while filling, hits the memo and gets the same buffer, so both
        # the sharing and the alias graph survive. The reverse order (letting ndarray deep-copy
        # itself) produces a second buffer on re-entry, and ndarray registers only after its own
        # recursion finishes, so the outer frame always keeps the wrong one (AS-001).
        source = self._data
        if id(source) in memo:
            clone._data = memo[id(source)]
        else:
            buffer = np.empty_like(source)
            memo[id(source)] = buffer
            for position, item in enumerate(source):
                buffer[position] = copy.deepcopy(item, memo)
            clone._data = buffer
        for name, value in self.__dict__.items():
            if name == "_data":
                continue
            setattr(clone, name, copy.deepcopy(value, memo))
        # __slots__ 子类没有 __dict__ 中的槽位，单独补上。
        # 双下划线名字会被 name-mangle 成 ``_ClassName__name``，所以按实际属性名查找。
        # Slotted subclasses keep their slots outside __dict__, so copy those explicitly.
        # Double-underscore names are mangled to ``_ClassName__name``, so look up the real name.
        for slot in getattr(self.__class__, "__slots__", ()):
            if slot == "_data" or slot in self.__dict__:
                continue
            name = slot
            if slot.startswith("__") and not slot.endswith("__"):
                name = f"_{self.__class__.__name__.lstrip('_')}{slot}"
            if hasattr(self, name):
                setattr(clone, name, copy.deepcopy(getattr(self, name), memo))
        return clone

    def __copy__(self) -> AbstractMultiArray[T, S]:
        """浅拷贝，缓冲保持共享 / Shallow copy keeping the buffer shared."""
        clone = self.__class__.__new__(self.__class__)
        for name, value in self.__dict__.items():
            setattr(clone, name, value)
        for slot in getattr(self.__class__, "__slots__", ()):
            if hasattr(self, slot):
                setattr(clone, slot, getattr(self, slot))
        return clone

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
    def to_list(self) -> BindingResult[Any]:
        """转换为嵌套 Python 列表。

        Export logical nested values through the existing Result.

        Returns:
            逻辑列表、标量叶或外部失败。/ Logical lists, scalar leaf, or external failure.
        """
        ...

    @abc.abstractmethod
    def map(self, f: Callable[[T], T]) -> BindingResult[MultiArray[T, S]]:
        """对每个元素应用转换函数，返回新数组。

        Apply a transform function to each element,
        returning the existing Result containing a new immutable array.

        Args:
            f: 转换函数。/ Transform function.

        Returns:
            新数组或外部失败。/ New array or external failure.
        """
        ...

    @abc.abstractmethod
    def flat_map(
        self, f: Callable[[T], Sequence[T]]
    ) -> BindingResult[MultiArray[T, S]]:
        """对每个元素应用返回序列的函数并展平。

        Apply a function returning a sequence to each
        element and flatten into the existing Result.

        Args:
            f: 返回可迭代序列的函数。/ Function returning an iterable sequence.

        Returns:
            新数组或外部失败，保留最终源形状。/ New array or external failure, retaining the final source shape.
        """
        ...

    @abc.abstractmethod
    def reduce(self, f: Callable[[T, T], T]) -> BindingResult[T]:
        """使用二元函数规约所有元素。

        Reduce live physical slots through pinned Rust indices and a binary callback.
        """
        ...

    @abc.abstractmethod
    def transpose(self) -> BindingResult[MultiArray[T, DynShape]]:
        """转置数组。/ Transpose the array."""
        ...

    @abc.abstractmethod
    def reshape(self, new_shape: DynShape) -> BindingResult[MultiArray[T, DynShape]]:
        """重塑数组形状。/ Reshape the array."""
        ...

    @abc.abstractmethod
    def flatten(self) -> BindingResult[MultiArray[T, DynShape]]:
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

    def at(
        self, *, indices: tuple[int, ...], standard_layout: bool = False
    ) -> BindingResult[T]:
        """通过 Rust 严格坐标读取共享槽位，不改变旧 get / Read a shared slot using strict Rust coordinates without changing legacy get.

        Args:
            indices: 完整非负整数坐标 tuple / Complete nonnegative integer coordinate tuple.
            standard_layout: 自定义形状必须显式确认标准行列布局 / Custom shapes must explicitly confirm standard row/column layout.

        Returns:
            元素或现有 Result 失败；不复制共享存储 / Element or existing Result failure; shared storage is not copied.
        """
        return read(owner=self, indices=indices, standard_layout=standard_layout)

    def at_many(
        self, *, indices: list[tuple[int, ...]], standard_layout: bool = False
    ) -> BindingResult[list[T]]:
        """整批检查坐标后读取共享槽位 / Read shared slots after checking the complete coordinate batch.

        Args:
            indices: 内置坐标 list，保持顺序并允许重复 / Built-in coordinate list, preserving order and allowing duplicates.
            standard_layout: 自定义形状须显式确认标准布局 / Custom shapes require explicit standard-layout confirmation.

        Returns:
            独立结果列表或 Failed，不返回部分值；非并发原子快照 / Detached result list or Failed, never partial values; not a concurrent atomic snapshot.
        """
        return read_many(owner=self, indices=indices, standard_layout=standard_layout)

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
        yield from _native._iterate_shared_array(
            owner=self, scalar_type=np.generic, count=max(0, index(self.size))
        )

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

    def to_list(self) -> BindingResult[Any]:
        """转换为嵌套 Python 列表。

        Convert to nested Python list.

        Returns:
            逻辑嵌套列表、标量叶或外部失败。/ Logical nested lists, scalar leaf, or external failure.
        """
        if _shared_nested._protocol is _DEFAULT_NESTED_PROTOCOL:
            try:
                return _DEFAULT_NESTED_TO_LIST(self)
            except Exception as error:
                return _shared_nested.external_failure(error)
        return nested_shared_array(self)

    def map(self, f: Callable[[T], T]) -> BindingResult[MultiArray[T, S]]:
        """对每个元素应用转换函数。

        Apply a transform function to each element.

        Args:
            f: 转换函数。/ Transform function.

        Returns:
            新的不可变数组或保留原异常的失败。/ New immutable array or failure retaining the original exception.
        """
        return map_shared_array(
            owner=self,
            callback=f,
            flat=False,
            finish=lambda data: MultiArray(self._shape, data),
        )

    def flat_map(
        self, f: Callable[[T], Sequence[T]]
    ) -> BindingResult[MultiArray[T, S]]:
        """对每个元素应用返回序列的函数并展平。

        Apply a function returning a sequence to each
        element and flatten.

        Args:
            f: 返回序列的函数。/ Function returning a sequence.

        Returns:
            新的不可变数组或保留原异常的失败。/ New immutable array or failure retaining the original exception.
        """
        return map_shared_array(
            owner=self,
            callback=f,
            flat=True,
            finish=lambda data: MultiArray(self._shape, data),
        )

    def reduce(self, f: Callable[[T, T], T]) -> BindingResult[T]:
        """使用二元函数规约所有元素。

        Reduce all elements using a binary function.

        Args:
            f: 二元规约函数。/ Binary reduction function.

        Returns:
            规约结果或保留外部异常的失败。/ Reduction result or failure retaining external exceptions.
        """
        return reduce_shared_array(self, f)

    def transpose(self) -> BindingResult[MultiArray[T, DynShape]]:
        """转置数组（反转维度顺序）。

        Transpose the array (reverse dimension order).

        Returns:
            转置后的新数组或外部失败。/ New transposed array or external failure.
        """
        return transpose_shared_array(
            owner=self,
            precopy=False,
            finish=lambda shape, data: MultiArray(shape, data),
        )

    def reshape(self, new_shape: DynShape) -> BindingResult[MultiArray[T, DynShape]]:
        """重塑数组形状。

        Reshape the array.

        Args:
            new_shape: 新形状。/ New shape.

        Returns:
            重塑后的新数组或外部失败。/ New reshaped array or external failure.
        """
        return reshape_storage(
            owner=self,
            target=new_shape,
            precopy=False,
            resolve=_storage_constructor,
        )

    def flatten(self) -> BindingResult[MultiArray[T, DynShape]]:
        """展平为一维数组。

        Flatten to a 1-D array.

        Returns:
            展平后的新数组或外部失败。/ New flattened array or external failure.
        """
        return flatten_storage(
            self, _storage_constructor, standard=type(self) is MultiArray
        )

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

    def at(
        self, *, indices: tuple[int, ...], standard_layout: bool = False
    ) -> BindingResult[T]:
        """通过 Rust 严格坐标读取共享槽位 / Read a shared slot using strict Rust coordinates.

        Args:
            indices: 完整非负整数坐标 tuple / Complete nonnegative integer coordinate tuple.
            standard_layout: 自定义形状必须显式确认标准布局 / Custom shapes must explicitly confirm standard layout.

        Returns:
            元素或现有 Result 失败；不改变旧 get / Element or existing Result failure; legacy get is unchanged.
        """
        return read(owner=self, indices=indices, standard_layout=standard_layout)

    def at_many(
        self, *, indices: list[tuple[int, ...]], standard_layout: bool = False
    ) -> BindingResult[list[T]]:
        """整批检查坐标后读取共享槽位 / Read shared slots after checking the complete coordinate batch.

        Args:
            indices: 内置坐标 list，保持顺序并允许重复 / Built-in coordinate list, preserving order and allowing duplicates.
            standard_layout: 自定义形状须显式确认标准布局 / Custom shapes require explicit standard-layout confirmation.

        Returns:
            独立结果列表或 Failed，非并发原子快照 / Detached result list or Failed, not a concurrent atomic snapshot.
        """
        return read_many(owner=self, indices=indices, standard_layout=standard_layout)

    def set_at(
        self, *, indices: tuple[int, ...], value: T, standard_layout: bool = False
    ) -> BindingResult[None]:
        """通过 Rust 严格坐标写入共享槽位 / Write a shared slot using strict Rust coordinates.

        Args:
            indices: 完整非负整数坐标 tuple / Complete nonnegative integer coordinate tuple.
            value: 遵守原 ndarray dtype 赋值规则的值 / Value following the original ndarray dtype assignment rules.
            standard_layout: 自定义形状必须显式确认标准布局 / Custom shapes must explicitly confirm standard layout.

        Returns:
            成功或现有 Result 失败；不改变旧 set / Success or existing Result failure; legacy set is unchanged.
        """
        return write(
            owner=self, indices=indices, value=value, standard_layout=standard_layout
        )

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
        yield from _native._iterate_shared_array(
            owner=self, scalar_type=np.generic, count=max(0, index(self.size))
        )

    def to_list(self) -> BindingResult[Any]:
        """转换为嵌套 Python 列表。

        Export logical nested values through the existing Result.

        Returns:
            逻辑列表、标量叶或外部失败。/ Logical lists, scalar leaf, or external failure.
        """
        if _shared_nested._protocol is _DEFAULT_NESTED_PROTOCOL:
            try:
                return _DEFAULT_NESTED_TO_LIST(self)
            except Exception as error:
                return _shared_nested.external_failure(error)
        return nested_shared_array(self)

    def map(self, f: Callable[[T], T]) -> BindingResult[MultiArray[T, S]]:
        """对每个元素应用转换函数。

        Apply a transform function to each element.

        Args:
            f: 转换函数。/ Transform function.

        Returns:
            新的不可变数组或保留原异常的失败。/ New immutable array or failure retaining the original exception.
        """
        return map_shared_array(
            owner=self,
            callback=f,
            flat=False,
            finish=lambda data: MultiArray(self._shape, data),
        )

    def flat_map(
        self, f: Callable[[T], Sequence[T]]
    ) -> BindingResult[MultiArray[T, S]]:
        """对每个元素应用返回序列的函数并展平。

        Apply a function returning a sequence to each
        element and flatten.

        Args:
            f: 返回可迭代序列的函数。/ Function returning an iterable sequence.

        Returns:
            新数组或外部失败，保留最终源形状。/ New array or external failure, retaining the final source shape.
        """
        return map_shared_array(
            owner=self,
            callback=f,
            flat=True,
            finish=lambda data: MultiArray(self._shape, data),
        )

    def reduce(self, f: Callable[[T, T], T]) -> BindingResult[T]:
        """使用二元函数规约所有元素。

        Reduce live physical slots through pinned Rust indices and a binary callback.

        Args:
            f: 二元规约函数。/ Binary reduction callback.

        Returns:
            规约结果或保留外部异常的失败。/ Reduction result or failure retaining external exceptions.
        """
        return reduce_shared_array(self, f)

    def transpose(self) -> BindingResult[MultiArray[T, DynShape]]:
        """转置数组（返回不可变副本）。

        Transpose the array (returns an immutable copy).
        """
        return transpose_shared_array(
            owner=self,
            precopy=True,
            finish=lambda shape, data: MultiArray(shape, data),
        )

    def reshape(self, new_shape: DynShape) -> BindingResult[MultiArray[T, DynShape]]:
        """重塑数组形状（返回不可变副本）。

        Reshape the array (returns an immutable copy).
        """
        return reshape_storage(
            owner=self,
            target=new_shape,
            precopy=True,
            resolve=_storage_constructor,
        )

    def flatten(self) -> BindingResult[MultiArray[T, DynShape]]:
        """展平为一维数组（返回不可变副本）。

        Flatten to a 1-D array (returns an immutable copy).
        """
        return flatten_storage(
            self, _storage_constructor, standard=type(self) is MutableMultiArray
        )

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
