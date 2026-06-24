"""索引体系 / Indexed hierarchy.

Indexed / IndexedImpl / ManualIndexed / AutoIndexed。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Indexed(Protocol):
    """索引协议 / Indexed protocol."""

    def index(self) -> int:
        """获取索引 / Get index."""


class IndexedImpl(ABC):
    """索引实现基类 / Indexed implementation base class."""

    @abstractmethod
    def index(self) -> int:
        """获取索引 / Get index."""


@dataclass
class ManualIndexed(IndexedImpl):
    """手动索引 / Manual index."""

    _index: int = field(default=0, repr=False)

    def index(self) -> int:
        return self._index

    def set_index(self, new_index: int) -> None:
        """设置索引 / Set index."""
        self._index = new_index


_auto_index_counter: int = 0


@dataclass
class AutoIndexed(IndexedImpl):
    """自动索引 / Auto index."""

    _index: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        global _auto_index_counter
        self._index = _auto_index_counter
        _auto_index_counter += 1

    def index(self) -> int:
        return self._index
