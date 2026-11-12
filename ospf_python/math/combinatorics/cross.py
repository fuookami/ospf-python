"""组合数学：笛卡尔积。

Combinatorics: Cartesian product.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar, cast

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed

T = TypeVar("T")


def cross(*iterables: Iterable[T]) -> BindingResult[list[tuple[T, ...]]]:
    """计算多个可迭代对象的笛卡尔积。

    Compute the Cartesian product through the pinned Rust enumerator.

    Args:
        *iterables: 可迭代对象序列。/ Iterable sequence.

    Returns:
        成功包含独立 tuple 列表，叶保持身份；失败保留外部协议异常。
        / Success contains detached tuples with original leaves; failure retains external protocol exceptions.
    """
    try:
        payload = _native._cross(iterables)
    except Exception as error:
        return Failed(
            ExErr(
                _code=ErrorCode.APPLICATION_ERROR,
                _message="笛卡尔积外部协议失败 / Cartesian product external protocol failed",
                value=FailureContext(
                    source="ospf-python",
                    category="APPLICATION_ERROR",
                    rust_code=None,
                    error_class="EXTERNAL_ITERABLE",
                    callback_exception=error,
                ),
            )
        )
    return cast("BindingResult[list[tuple[T, ...]]]", invoke(lambda: payload))
