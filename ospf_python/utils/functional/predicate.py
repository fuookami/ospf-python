"""谓词组合子工具。

Predicate combinator utilities.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def negate(predicate: Callable[[T], bool]) -> Callable[[T], bool]:
    """取反谓词。

    Negates a predicate.

    Args:
        predicate: 待取反的谓词。/ Predicate to negate.

    Returns:
        取反后的谓词。/ Negated predicate.
    """
    return lambda value: not predicate(value)


def and_then(*predicates: Callable[[T], bool]) -> Callable[[T], bool]:
    """组合谓词，所有谓词均通过时返回 True。

    Combines predicates; returns True only when all predicates pass.

    Args:
        *predicates: 谓词列表。/ Predicates to combine.

    Returns:
        组合后的谓词。/ Combined predicate.
    """
    return lambda value: all(p(value) for p in predicates)


def or_else(*predicates: Callable[[T], bool]) -> Callable[[T], bool]:
    """组合谓词，任一谓词通过时返回 True。

    Combines predicates; returns True when any predicate passes.

    Args:
        *predicates: 谓词列表。/ Predicates to combine.

    Returns:
        组合后的谓词。/ Combined predicate.
    """
    return lambda value: any(p(value) for p in predicates)
