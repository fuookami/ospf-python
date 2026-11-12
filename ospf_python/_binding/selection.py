"""位置选择的 Python 协议边界。 / Python protocol boundary for positional selection."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar, cast

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed

T = TypeVar("T")


def select(
    *, items: Sequence[T], k: int, permutations: bool
) -> BindingResult[list[list[T]]]:
    """调用同一固定上游位置内核并保留外部错误。

    Invoke the pinned positional kernel while retaining external failures.

    Args:
        items: live 索引源。 / Live indexed source.
        k: 原始选取参数。 / Original selection count.
        permutations: 是否生成有序选择。 / Whether to produce ordered selections.

    Returns:
        既有 Result 包含新行或原始失败。 / Existing Result with new rows or original failure.
    """
    try:
        payload = _native._selection(items=items, k=k, permutations=permutations)
    except Exception as error:
        return Failed(
            ExErr(
                _code=ErrorCode.APPLICATION_ERROR,
                _message="选择外部协议失败 / Selection external protocol failed",
                value=FailureContext(
                    source="ospf-python",
                    category="APPLICATION_ERROR",
                    rust_code=None,
                    error_class="EXTERNAL_SEQUENCE",
                    callback_exception=error,
                ),
            )
        )
    return cast("BindingResult[list[list[T]]]", invoke(lambda: payload))
