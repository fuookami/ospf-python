"""向量、哑索引与映射索引抽象。

Vector, dummy index, and map index abstractions.
"""

from __future__ import annotations

import abc
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol, TypeVar

from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import Shape1

# T: 元素类型 / Element type
T = TypeVar("T")


class DummyIndexRange(Protocol):
    """哑索引范围协议。

    Protocol for dummy index ranges.

    哑索引范围定义一组可迭代的索引值。
    A dummy index range defines an iterable set of index values.
    """

    def __iter__(self) -> Iterator[int]:
        """迭代索引值。/ Iterate over index values."""
        ...

    def __len__(self) -> int:
        """返回索引数量。/ Return number of indices."""
        ...


class DummyIndex(abc.ABC):
    """哑索引抽象基类（密封）。

    Abstract base class for dummy indices (sealed).

    哑索引用于表达式中的占位索引，如 einsum 记法。
    Dummy indices are placeholder indices in expressions,
    such as in einsum notation.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """获取索引名称。/ Get index name."""
        ...

    @property
    @abc.abstractmethod
    def range(self) -> DummyIndexRange:
        """获取索引范围。/ Get index range."""
        ...


@dataclass(frozen=True)
class SimpleDummyIndex(DummyIndex):
    """简单哑索引，带名称和范围。

    Simple dummy index with a name and range.

    Attributes:
        _name: 索引名称。/ Index name.
        _range: 索引范围。/ Index range.
    """

    _name: str
    _range: DummyIndexRange

    @property
    def name(self) -> str:
        """获取索引名称。/ Get index name."""
        return self._name

    @property
    def range(self) -> DummyIndexRange:
        """获取索引范围。/ Get index range."""
        return self._range


class DummyIndexIterator(abc.ABC):
    """哑索引迭代器抽象基类（密封）。

    Abstract base class for dummy index iterators (sealed).

    遍历哑索引的所有可能值组合。
    Iterates over all possible value combinations
    of dummy indices.
    """

    @abc.abstractmethod
    def __iter__(self) -> Iterator[tuple[int, ...]]:
        """迭代索引值元组。/ Iterate over index value tuples."""
        ...

    @abc.abstractmethod
    def __len__(self) -> int:
        """返回迭代总数。/ Return total iteration count."""
        ...


class SimpleDummyIndexIterator(DummyIndexIterator):
    """简单哑索引迭代器。

    Simple dummy index iterator.

    按笛卡尔积遍历多个哑索引的值。
    Iterates over the Cartesian product of
    multiple dummy index values.

    Args:
        indices: 哑索引列表。/ List of dummy indices.
    """

    def __init__(self, indices: list[DummyIndex]) -> None:
        """初始化迭代器。/ Initialize iterator."""
        self._indices = indices

    def __iter__(self) -> Iterator[tuple[int, ...]]:
        """迭代笛卡尔积。/ Iterate over Cartesian product."""
        if not self._indices:
            yield ()
            return
        yield from self._cartesian_product(0, ())

    def __len__(self) -> int:
        """返回笛卡尔积大小。/ Return Cartesian product size."""
        total = 1
        for idx in self._indices:
            total *= len(idx.range)
        return total

    def _cartesian_product(
        self,
        depth: int,
        current: tuple[int, ...],
    ) -> Iterator[tuple[int, ...]]:
        """递归生成笛卡尔积。

        Recursively generate Cartesian product.

        Args:
            depth: 当前递归深度。/ Current recursion depth.
            current: 当前已选值。/ Currently selected values.

        Yields:
            完整的索引元组。/ Complete index tuple.
        """
        if depth == len(self._indices):
            yield current
            return
        for val in self._indices[depth].range:
            yield from self._cartesian_product(depth + 1, current + (val,))


class MapIndex(abc.ABC):
    """映射索引抽象基类（密封）。

    Abstract base class for map indices (sealed).

    映射索引将一个索引空间映射到另一个索引空间。
    A map index maps one index space to another.
    """

    @abc.abstractmethod
    def map_index(self, index: int) -> int:
        """将单个索引映射到目标空间。

        Map a single index to the target space.

        Args:
            index: 源索引。/ Source index.

        Returns:
            目标索引。/ Target index.
        """
        ...

    @abc.abstractmethod
    def map_indices(self, indices: tuple[int, ...]) -> tuple[int, ...]:
        """将索引元组映射到目标空间。

        Map an index tuple to the target space.

        Args:
            indices: 源索引元组。/ Source index tuple.

        Returns:
            目标索引元组。/ Target index tuple.
        """
        ...


@dataclass(frozen=True)
class IdentityMapIndex(MapIndex):
    """恒等映射索引，不做变换。

    Identity map index, no transformation.

    Attributes:
        ndim: 维度数。/ Number of dimensions.
    """

    ndim: int

    def map_index(self, index: int) -> int:
        """返回原索引。/ Return original index."""
        return index

    def map_indices(self, indices: tuple[int, ...]) -> tuple[int, ...]:
        """返回原索引元组。/ Return original index tuple."""
        return indices


@dataclass(frozen=True)
class OffsetMapIndex(MapIndex):
    """偏移映射索引，将索引加上固定偏移。

    Offset map index, adds a fixed offset to indices.

    Attributes:
        offset: 偏移量。/ Offset value.
    """

    offset: int

    def map_index(self, index: int) -> int:
        """返回索引加偏移。/ Return index plus offset."""
        return index + self.offset

    def map_indices(self, indices: tuple[int, ...]) -> tuple[int, ...]:
        """返回索引元组各元素加偏移。

        Return index tuple with offset added to each element.
        """
        return tuple(i + self.offset for i in indices)


# Vector: 一维 MultiArray 的类型别名。
# Vector: type alias for 1-D MultiArray.
Vector = MultiArray[T, Shape1]
