"""最小值/最大值工具。

Minimum / maximum utilities.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

T = TypeVar("T")


def _failure[T](error: Exception) -> BindingResult[T]:
    error_type = type(error)
    if issubclass(error_type, MemoryError):
        code = ErrorCode.RESOURCE_EXHAUSTED
    elif issubclass(error_type, OverflowError):
        code = ErrorCode.OVERFLOW
    elif issubclass(error_type, (TypeError, ValueError)):
        code = ErrorCode.ILLEGAL_ARGUMENT
    else:
        code = ErrorCode.APPLICATION_ERROR
    return Failed(
        ExErr(
            _code=code,
            _message="极值协议失败 / Extrema protocol failed",
            value=FailureContext(
                source="ospf-python",
                category=code.name,
                rust_code=None,
                error_class="EXTERNAL_EXTREMA",
                callback_exception=error,
            ),
        )
    )


def min_of(items: Iterable[T]) -> BindingResult[T]:
    """返回可迭代对象中的最小值。

    Return the minimum value from an iterable.

    Args:
        items: 可迭代对象。/ Iterable of items.

    Returns:
        包含原最小对象的 Result；失败保留原异常。/
        Result with the original minimum; failures retain the exception.
    """
    try:
        result = _native._ordinary_extreme(
            items=items, callable=min, minimum=True, ops=_native._public_integer
        )
    except Exception as error:
        return _failure(error)
    return Ok(result)


def max_of(items: Iterable[T]) -> BindingResult[T]:
    """返回可迭代对象中的最大值。

    Return the maximum value from an iterable.

    Args:
        items: 可迭代对象。/ Iterable of items.

    Returns:
        包含原最大对象的 Result；失败保留原异常。/
        Result with the original maximum; failures retain the exception.
    """
    try:
        result = _native._ordinary_extreme(
            items=items, callable=max, minimum=False, ops=_native._public_integer
        )
    except Exception as error:
        return _failure(error)
    return Ok(result)


def min_max_of(
    items: Iterable[T],
) -> BindingResult[tuple[T, T]]:
    """返回可迭代对象中的最小值和最大值。

    Return the minimum and maximum from an iterable.

    Args:
        items: 可迭代对象。/ Iterable of items.

    Returns:
        包含原极值二元组的 Result；失败保留原异常。/
        Result with original extrema; failures retain the exception.
    """
    try:
        collected = list(items)
        low = _native._ordinary_extreme(
            items=collected, callable=min, minimum=True, ops=_native._public_integer
        )
        high = _native._ordinary_extreme(
            items=collected, callable=max, minimum=False, ops=_native._public_integer
        )
    except Exception as error:
        return _failure(error)
    return Ok((low, high))
