"""求和协议 / Sum protocol.

Sum 提供可迭代对象的求和能力。
Sum provides summation capability for iterables.
"""

from __future__ import annotations

from typing import Iterable, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class Sum(Protocol):
    """求和协议 / Sum protocol.

    对可迭代对象中的元素求和。
    Sums elements in an iterable.
    """

    @staticmethod
    def sum(items: Iterable[T]) -> T:
        """对可迭代对象求和 / Sum an iterable.

        Args:
            items: 可迭代对象。An iterable of items.

        Returns:
            求和结果。The sum result.
        """
