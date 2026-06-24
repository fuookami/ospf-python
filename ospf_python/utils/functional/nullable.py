"""可空值安全操作工具。

Nullable value safe-operation utilities (Kotlin ?.let / also).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
U = TypeVar("U")


def let_not_none(value: T | None, *, f: Callable[[T], U]) -> U | None:
    """当值不为 None 时应用变换函数，否则返回 None。

    Applies the function if value is not None (Kotlin's ``?.let``).

    Args:
        value: 可能为 None 的值。/ Potentially None value.
        f: 值不为 None 时执行的变换函数。/ Transform to apply.

    Returns:
        变换结果或 None。/ Transformed result or None.
    """
    if value is None:
        return None
    return f(value)


def also_not_none(
    value: T | None,
    *,
    f: Callable[[T], object],
) -> T | None:
    """当值不为 None 时执行副作用，始终返回原值。

    Executes a side-effect if value is not None, always returns the
    original value (Kotlin's ``?.also``).

    Args:
        value: 可能为 None 的值。/ Potentially None value.
        f: 值不为 None 时执行的副作用函数。/ Side-effect to apply.

    Returns:
        原始值（可能为 None）。/ Original value (may be None).
    """
    if value is not None:
        f(value)
    return value
