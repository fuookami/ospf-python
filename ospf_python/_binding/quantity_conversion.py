"""开放单位回调的原生控制面。 / Native control plane for open unit callbacks.

这里只是完整 Quantity 转换的回调通道，不是内置单位的旧内核 fallback。
This callback lane is not a legacy-kernel fallback for builtin units.
"""

from __future__ import annotations

import builtins
from importlib import import_module
from typing import Any

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

# 只绑定模块，不提前捕获回调可替换的 Quantity 工厂。
# Bind the module, not the Quantity factory that callbacks may replace.
quantity_module = import_module("ospf_python.quantities.quantity.quantity")


def convert_callback(*, owner: object, target: object) -> BindingResult[Any]:
    """在 Rust 中编排开放单位回调，保持数值与输出不透明。

    Orchestrate open unit callbacks in Rust without coercing values or outputs.

    Args:
        owner: 提供 value/unit 的物理量。 / Quantity exposing value/unit.
        target: 提供 from_si 的目标。 / Target exposing from_si.

    Returns:
        当前 Quantity 工厂的输出或保留原异常的 Failed。
        Current Quantity factory output or Failed retaining the original error.
    """
    value, failure = _native._convert_quantity_callback(
        owner=owner,
        target=target,
        namespace=quantity_module.__dict__,
        builtins=builtins.__dict__,
    )
    if failure is None:
        return Ok(value)
    stage, error = failure
    return Failed(
        ExErr(
            _code=ErrorCode.APPLICATION_ERROR,
            _message=f"物理量回调协议失败 / Quantity callback protocol failed: {stage}",
            value=FailureContext(
                source="ospf-python-native",
                category="APPLICATION_ERROR",
                rust_code=None,
                error_class="QUANTITY_CALLBACK",
                callback_exception=error,
            ),
        )
    )
