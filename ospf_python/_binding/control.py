"""单次 Rust 求解控制与只读进度 / Single-attempt Rust control and read-only progress."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from ospf_python import _native
from ospf_python._binding.result import BindingResult, invalid, invoke
from ospf_python._native import CancellationRecord, SolveProgress
from ospf_python.utils.functional.result import Failed, Ok, Result

__all__ = [
    "CancellationRecord",
    "CancellationScope",
    "ProgressCallback",
    "SolveHandle",
    "SolveProgress",
]

# 回调的领域错误上下文不受绑定错误类型限制。 / Callback domain errors retain their own context/type.
type ProgressCallback = Callable[[SolveProgress], Result[None, Any, Any] | None]


class SolveHandle:
    """共享 Rust 取消事实的单次求解句柄 / Single-attempt handle sharing Rust cancellation facts.

    Attributes:
        phase: READY、RUNNING 或 FINISHED / Attempt lifecycle phase.
        is_cancelled: 是否记录过取消 / Whether cancellation was recorded.
        completed_at_epoch_ms: 首次完成时间 / First completion time.
        cancellation_preceded_completion: 取消是否先于完成 / Whether cancellation preceded completion.
    """

    __slots__ = ("_handle",)

    def __init__(self) -> None:
        self._handle = _native.SolveHandle()

    @property
    def phase(self) -> str:
        """单次 attempt 的阶段 / Single-attempt phase."""
        return self._handle.phase

    @property
    def is_cancelled(self) -> bool:
        """Rust 已记录取消 / Rust has recorded cancellation."""
        return self._handle.is_cancelled

    @property
    def completed_at_epoch_ms(self) -> int | None:
        """Rust 的完成时间；尚未完成时为 None / Rust completion time, None before completion."""
        return self._handle.completed_at_epoch_ms

    @property
    def cancellation_preceded_completion(self) -> bool:
        """Rust 线性化的取消先后关系 / Rust-linearized cancellation ordering."""
        return self._handle.cancellation_preceded_completion

    def cancellation(self) -> CancellationRecord | None:
        """首次取消事实的只读快照 / Read-only snapshot of the first cancellation fact."""
        return self._handle.cancellation()

    def cancel(
        self, *, origin: str = "user", reason: str | None = None
    ) -> BindingResult[bool]:
        """线程安全地请求取消，不等待模型所有者 / Request cancellation without waiting for the model owner.

        Args:
            origin: Rust 线格式来源代码，未知非空代码原样保留 / Rust wire origin, preserving unknown nonempty codes.
            reason: 可选原因 / Optional reason.

        Returns:
            首次记录返回 True；重复返回 False；失败返回 Failed / True for first request, False for repeats, or Failed.
        """
        return invoke(lambda: self._handle.cancel(origin=origin, reason=reason))


class CancellationScope:
    """跨多个单次原生 attempt 共享取消 / Share cancellation across single-use native attempts.

    Attributes:
        is_cancelled: 是否已记录取消 / Whether cancellation has been recorded.
    """

    __slots__ = ("_cancelled", "_handles", "_lock", "_origin", "_reason")

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handles: list[SolveHandle] = []
        self._cancelled = False
        self._origin = "user"
        self._reason: str | None = None

    @property
    def is_cancelled(self) -> bool:
        """作用域是否已请求取消 / Whether the scope has requested cancellation."""
        with self._lock:
            return self._cancelled

    def new_handle(self) -> BindingResult[SolveHandle]:
        """创建下一次 attempt 的独立句柄 / Create an independent handle for the next attempt.

        Returns:
            新句柄；已取消作用域返回预取消句柄 / A fresh or pre-cancelled handle.
        """
        handle = SolveHandle()
        with self._lock:
            self._handles.append(handle)
            if not self._cancelled:
                return Ok(handle)
            cancelled = handle.cancel(origin=self._origin, reason=self._reason)
        if isinstance(cancelled, Failed):
            return Failed(cancelled.error)
        return Ok(handle)

    def cancel(
        self, *, origin: str = "user", reason: str | None = None
    ) -> BindingResult[bool]:
        """取消当前及后续 attempt / Cancel current and future attempts.

        Args:
            origin: 取消来源代码 / Cancellation origin code.
            reason: 可选原因 / Optional reason.

        Returns:
            首次请求返回 True，重复请求返回 False / True for the first request, False for repeats.
        """
        if not isinstance(origin, str) or not origin.strip():
            return invalid("取消来源不能为空 / Cancellation origin must not be empty")
        if reason is not None and not isinstance(reason, str):
            return invalid(
                "取消原因需要字符串或 None / Cancellation reason expects str or None"
            )
        with self._lock:
            if self._cancelled:
                return Ok(False)
            self._cancelled = True
            self._origin = origin
            self._reason = reason
            for handle in self._handles:
                cancelled = handle.cancel(origin=origin, reason=reason)
                if isinstance(cancelled, Failed):
                    return Failed(cancelled.error)
        return Ok(True)
