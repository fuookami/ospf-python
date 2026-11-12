"""有限枚举身份到固定Rust求值的薄适配。 / Thin finite-enum identity adapter to pinned Rust evaluation."""

from __future__ import annotations

from enum import Enum

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invalid, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok


def _index(value: object, members: tuple[Enum, Enum, Enum]) -> int:
    if value is members[0]:
        return 0
    if value is members[1]:
        return 1
    if value is members[2]:
        return 2
    return -1


def _evaluate[T](
    *,
    members: tuple[Enum, Enum, Enum],
    outputs: tuple[T, T, T],
    operation: str,
    left: object,
    right: object | None = None,
) -> BindingResult[T]:
    left_index = _index(left, members)
    if left_index < 0:
        return invalid(
            "左操作数不是同家族三值成员 / Left operand is not a same-family trivalent member"
        )
    right_index = -1
    if operation in ("and", "or"):
        right_index = _index(right, members)
        if right_index < 0:
            return invalid(
                "右操作数不是同家族三值成员 / Right operand is not a same-family trivalent member"
            )
    # 只编码三个枚举标签，不缓存或复制逻辑真值表。 / Encode enum tags only; do not cache or copy logical truth tables.
    tags = (True, False, None)
    try:
        value, failure = _native._trivalent(
            operation=operation,
            left=tags[left_index],
            right=tags[right_index] if right_index >= 0 else None,
        )
    except Exception as error:
        code = (
            ErrorCode.RESOURCE_EXHAUSTED
            if isinstance(error, MemoryError)
            else ErrorCode.APPLICATION_ERROR
        )
        return Failed(
            ExErr(
                _code=code,
                _message="三值逻辑传输失败 / Trivalent logic transport failed",
                value=FailureContext(
                    source="ospf-python",
                    category=code.name,
                    rust_code=None,
                    error_class="EXTERNAL_TRIVALENT",
                    callback_exception=error,
                ),
            )
        )
    if failure is not None:
        return invoke(lambda: (None, failure))
    # 成功只投影一次并发布一个Ok，不先包装传输值再map。 / Project once and publish one Ok, without wrapping a transport value and then mapping it.
    return Ok(
        outputs[0] if value is True else outputs[1] if value is False else outputs[2]
    )


def logic[T: Enum](
    *,
    members: tuple[T, T, T],
    operation: str,
    left: object,
    right: object | None = None,
) -> BindingResult[T]:
    """调用固定上游并还原原家族单例。 / Invoke pinned upstream and restore the original family singleton.

    Args:
        members: 真/假/未知成员。 / True/false/unknown members.
        operation: 与/或/非操作。 / AND/OR/NOT operation.
        left: 左成员。 / Left member.
        right: 可选右成员。 / Optional right member.

    Returns:
        原家族单例或显式失败。 / Original-family singleton or explicit failure.
    """
    return _evaluate(
        members=members,
        outputs=members,
        operation=operation,
        left=left,
        right=right,
    )


def optional_bool[T: Enum](
    *, members: tuple[T, T, T], owner: object
) -> BindingResult[bool | None]:
    """通过上游转换为可选布尔值。 / Convert to an optional boolean through upstream.

    Args:
        members: 真/假/未知成员。 / True/false/unknown members.
        owner: 原家族成员。 / Original-family member.

    Returns:
        bool/None成功值或显式失败。 / Successful bool/None or explicit failure.
    """
    return _evaluate(
        members=members, outputs=(True, False, None), operation="bool", left=owner
    )
