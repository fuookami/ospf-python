"""多维数组访问顺序与索引迭代器。

Access order and multi-dimensional index iterators.
"""

from __future__ import annotations

import enum
from collections.abc import Iterator
from dataclasses import dataclass


class AccessOrder(enum.Enum):
    """数组访问顺序 / Array access order.

    C_ORDER: 行优先（最后维度变化最快）。
        Row-major (last dimension varies fastest).
    F_ORDER: 列优先（第一维度变化最快）。
        Column-major (first dimension varies fastest).
    DEFAULT: 默认顺序（等同 C_ORDER）。
        Default order (same as C_ORDER).
    """

    C_ORDER = enum.auto()
    F_ORDER = enum.auto()
    DEFAULT = enum.auto()


@dataclass(frozen=True)
class IteratorPosition:
    """迭代器当前位置的索引元组。

    Index tuple at the current iterator position.

    Attributes:
        indices: 多维索引元组。/ Multi-dimensional index tuple.
    """

    indices: tuple[int, ...]


class MultiIndexIterator:
    """多维索引迭代器。

    Multi-dimensional index iterator. Iterates over all index
    combinations for a given shape in the specified access order.

    Args:
        shape: 各维度大小。/ Size of each dimension.
        access_order: 访问顺序。/ Access order.
    """

    def __init__(
        self,
        shape: tuple[int, ...],
        *,
        access_order: AccessOrder = AccessOrder.DEFAULT,
    ) -> None:
        self._shape = shape
        self._ndim = len(shape)
        self._c_order = access_order != AccessOrder.F_ORDER

        if any(d <= 0 for d in shape):
            self._total = 0
        elif self._c_order:
            # C 阶段：从最后一维开始递增
            # C-order: increment from the last dimension
            self._total = 1
            for d in shape:
                self._total *= d
        else:
            # F 阶段：从第一维开始递增
            # F-order: increment from the first dimension
            self._total = 1
            for d in shape:
                self._total *= d

        self._index = 0
        self._current: list[int] = [0] * self._ndim

    def __iter__(self) -> MultiIndexIterator:
        """返回自身作为迭代器。/ Return self as iterator."""
        return self

    def __next__(self) -> IteratorPosition:
        """获取下一组索引。/ Get the next index tuple."""
        if self._index >= self._total:
            raise StopIteration

        result = IteratorPosition(
            indices=tuple(self._current),
        )

        self._index += 1
        if self._index < self._total:
            if self._c_order:
                self._advance_c_order()
            else:
                self._advance_f_order()

        return result

    def __len__(self) -> int:
        """返回索引总数。/ Return total number of indices."""
        return int(self._total)

    def _advance_c_order(self) -> None:
        """C 阶段前进：最后维度优先递增。

        Advance in C-order: last dimension increments first.
        """
        carry = 1
        for i in range(self._ndim - 1, -1, -1):
            self._current[i] += carry
            if self._current[i] < self._shape[i]:
                return
            self._current[i] = 0
            carry = 1

    def _advance_f_order(self) -> None:
        """F 阶段前进：第一维度优先递增。

        Advance in F-order: first dimension increments first.
        """
        carry = 1
        for i in range(self._ndim):
            self._current[i] += carry
            if self._current[i] < self._shape[i]:
                return
            self._current[i] = 0
            carry = 1


class MultiIndexSequence:
    """多维索引序列生成器。

    Generates index sequences for a given shape.

    Args:
        shape: 各维度大小。/ Size of each dimension.
        access_order: 访问顺序。/ Access order.
    """

    def __init__(
        self,
        shape: tuple[int, ...],
        *,
        access_order: AccessOrder = AccessOrder.DEFAULT,
    ) -> None:
        self._shape = shape
        self._access_order = access_order

    def __iter__(self) -> Iterator[IteratorPosition]:
        """迭代所有索引位置。/ Iterate over all index positions."""
        return iter(
            MultiIndexIterator(
                self._shape,
                access_order=self._access_order,
            )
        )

    def __len__(self) -> int:
        """返回索引总数。/ Return total number of indices."""
        total = 1
        for d in self._shape:
            total *= d
        return total

    def to_list(self) -> list[IteratorPosition]:
        """转换为索引列表。/ Convert to a list of index positions."""
        return list(self)
