"""数组回调的控制面适配，不在 Python 中遍历数组 / Array callback control adapter without Python array traversal."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace
from typing import TYPE_CHECKING, Any, cast

from ospf_python._binding.result import BindingResult, invalid, invoke
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok, Result, Success

if TYPE_CHECKING:
    from ospf_python import _native

# None 是普通映射值；Ok 可以转义作为数据保存的 Result。 / None is a normal mapped value; Ok escapes a Result stored as data.
type MapCallback[T, U] = Callable[[T], U | Result[U, Any, Any]]
# Iterable 的物化是外部协议转换，拼接和形状验收在 Rust 中执行。 / Iterable materialization is external protocol conversion; Rust concatenates and validates shape.
type FlatMapCallback[T, U] = Callable[[T], Iterable[U] | Result[Iterable[U], Any, Any]]
# 二元用户操作的左结合归约，不在适配器中遍历输入。 / Binary user operation for a left fold, without input traversal in the adapter.
type ReduceCallback[T] = Callable[[T, T], T | Result[T, Any, Any]]


def reduce_callback[T](
    *,
    callback: object,
    operation: Callable[
        [Callable[[Any], tuple[bool, Any]]],
        tuple[T | None, _native.Failure | None],
    ],
) -> BindingResult[T]:
    """把 Rust 提供的内置二元组适配为用户二元调用 / Adapt a Rust-supplied built-in pair into a user binary call.

    Args:
        callback: 二元归约函数 / Binary reduction callback.
        operation: 执行完整归约的单次原生调用 / One native call performing the entire reduction.

    Returns:
        归约值或保留回调失败身份及调用序号的 Failed / Fold value or Failed retaining callback failure identity and ordinal.
    """
    if not callable(callback):
        return invalid("归约回调必须可调用 / Reduction callback must be callable")
    return map_callback(
        callback=lambda pair: callback(pair[0], pair[1]),
        flat=False,
        operation=operation,
    )


def map_callback[T](
    *,
    callback: object,
    flat: bool,
    operation: Callable[
        [Callable[[Any], tuple[bool, Any]]],
        tuple[T | None, _native.Failure | None],
    ],
) -> BindingResult[T]:
    """适配单次 Rust 批量映射调用中的 Python 回调 / Adapt Python callbacks within one Rust batch mapping call.

    Args:
        callback: 用户函数，可返回普通值或现有 Result / User function returning a plain value or existing Result.
        flat: 是否把返回的 iterable 转为传输 list / Whether to convert returned iterables into transport lists.
        operation: 接收适配回调的单次原生调用 / One native call accepting the adapted callback.

    Returns:
        原生数组或保留原始回调失败/异常及位置的 Failed / Native array or Failed retaining original callback result/exception and position.
    """
    return map_callbacks(callbacks=(callback,), flat=flat, operation=operation)


def map_callbacks[T](
    *,
    callbacks: tuple[object, ...],
    flat: bool,
    operation: Callable[
        [Callable[[Any], tuple[bool, Any]]],
        tuple[T | None, _native.Failure | None],
    ],
) -> BindingResult[T]:
    """适配单次原生调用的有序回调链，不遍历数组 / Adapt a callback chain for one native call without array traversal.

    Args:
        callbacks: 每个元素依次调用的非空函数链 / Nonempty functions called in order for each element.
        flat: 是否物化最终 iterable / Whether to materialize the final iterable.
        operation: 单次原生读取或批量操作 / One native read or batch operation.

    Returns:
        成功值或保留失败回调上下文的 Failed / Value or Failed retaining failing callback context.
    """
    if not callbacks or any(not callable(callback) for callback in callbacks):
        return invalid("映射回调必须可调用 / Mapping callbacks must be callable")
    chain = cast("tuple[Callable[[Any], Any], ...]", callbacks)
    original: Result[Any, Any, Any] | None = None
    exception: Exception | None = None
    failure_index: int | None = None
    position = 0
    reason = ""

    def adapted(value: Any) -> tuple[bool, Any]:
        nonlocal original, exception, failure_index, position, reason
        index = position
        position += 1
        returned_result: Result[Any, Any, Any] | None = None
        try:
            returned = value
            for callback in chain:
                returned_result = None
                returned = callback(returned)
                if isinstance(returned, Result):
                    returned_result = returned
                    if isinstance(returned, Ok):
                        returned = returned.value
                    elif isinstance(returned, Success):
                        returned = None
                    else:
                        original = returned_result
                        failure_index = index
                        reason = "回调返回失败或未支持结果 / Callback returned a failure or unsupported result"
                        return False, None
            if flat:
                returned = list(returned)
            return True, returned
        except Exception as error:
            # 用户函数及 iterable 为外部边界，不吞 KeyboardInterrupt/SystemExit。 / User calls and iterables are external boundaries; preserve KeyboardInterrupt/SystemExit.
            original = returned_result
            exception = error
            failure_index = index
            reason = f"Python 回调异常 / Python callback raised {type(error).__name__}"
            return False, None

    result = invoke(lambda: operation(adapted))
    if isinstance(result, Failed) and failure_index is not None:
        return Failed(
            ExErr(
                _code=result.error.code,
                _message=f"{result.error.message}: {reason}",
                value=replace(
                    result.error.value,
                    callback_result=original,
                    callback_exception=exception,
                    callback_index=failure_index,
                ),
            )
        )
    return result
