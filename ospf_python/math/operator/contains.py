"""包含关系运算符。

Containment check operator.
"""

from __future__ import annotations

from collections.abc import Container
from typing import TypeVar

T = TypeVar("T")


def contains_op(
    container: Container[T],
    item: T,
) -> bool:
    """检查容器是否包含指定元素。

    Check whether the container contains the item.

    Args:
        container: 容器。/ Container.
        item: 待检查元素。/ Item to check.

    Returns:
        是否包含。/ Whether contained.
    """
    return item in container
