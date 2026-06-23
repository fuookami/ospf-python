"""Functional primitives for the ospf-python framework.

Provides utility functions for functional programming patterns.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")
U = TypeVar("U")


def identity(value: T) -> T:
    """Return the input value unchanged.

    Args:
        value: Any value.

    Returns:
        The same value.
    """
    return value


def constant(value: T) -> Callable[[], T]:
    """Create a function that always returns the given value.

    Args:
        value: The value to return.

    Returns:
        A function that returns the value.
    """
    return lambda: value


def compose(*fns: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """Compose multiple functions right-to-left.

    Args:
        *fns: Functions to compose.

    Returns:
        Composed function.
    """

    def composed(x: Any) -> Any:
        result = x
        for fn in reversed(fns):
            result = fn(result)
        return result

    return composed


def curry(fn: Callable[[Any, Any], Any]) -> Callable[[Any], Callable[[Any], Any]]:
    """Curry a two-argument function.

    Args:
        fn: Two-argument function.

    Returns:
        Curried function.
    """
    return lambda a: lambda b: fn(a, b)


def flip(fn: Callable[[Any, Any], Any]) -> Callable[[Any, Any], Any]:
    """Flip the arguments of a two-argument function.

    Args:
        fn: Two-argument function.

    Returns:
        Function with flipped arguments.
    """
    return lambda a, b: fn(b, a)


def tap(fn: Callable[[T], Any]) -> Callable[[T], T]:
    """Execute a side effect and return the input unchanged.

    Args:
        fn: Side effect function.

    Returns:
        Function that executes fn and returns input.
    """

    def tapper(value: T) -> T:
        fn(value)
        return value

    return tapper


def ignore(_value: Any) -> None:
    """Ignore a value.

    Args:
        _value: Value to ignore.
    """
    pass
