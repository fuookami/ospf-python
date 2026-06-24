"""布尔谓词组合工具。

Boolean predicate combination utilities.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def all_of(*predicates: Callable[[T], bool]) -> Callable[[T], bool]:
    """返回一个谓词，当所有给定谓词均为 True 时返回 True。

    Returns a predicate that is True when all given predicates are True.

    Args:
        *predicates: 要组合的谓词函数列表。/ Predicate functions to combine.

    Returns:
        组合后的谓词。/ Combined predicate.
    """

    def _check(value: T) -> bool:
        return all(p(value) for p in predicates)

    return _check


def any_of(*predicates: Callable[[T], bool]) -> Callable[[T], bool]:
    """返回一个谓词，当任意给定谓词为 True 时返回 True。

    Returns a predicate that is True when any given predicate is True.

    Args:
        *predicates: 要组合的谓词函数列表。/ Predicate functions to combine.

    Returns:
        组合后的谓词。/ Combined predicate.
    """

    def _check(value: T) -> bool:
        return any(p(value) for p in predicates)

    return _check


def none_of(*predicates: Callable[[T], bool]) -> Callable[[T], bool]:
    """返回一个谓词，当所有给定谓词均为 False 时返回 True。

    Returns a predicate that is True when none of the given predicates
    are True.

    Args:
        *predicates: 要组合的谓词函数列表。/ Predicate functions to combine.

    Returns:
        组合后的谓词。/ Combined predicate.
    """

    def _check(value: T) -> bool:
        return not any(p(value) for p in predicates)

    return _check
