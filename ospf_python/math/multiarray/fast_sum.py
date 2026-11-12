"""多维数组快速求和。

Optimized summation for multi-arrays using numpy.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape, Shape2, StorageOrder

# 导入时捕获，避免测试把模块级 DynShape 换成工厂函数后 isinstance 失效。
# Captured at import so isinstance keeps working when tests replace the module-level DynShape
# with a factory.
_DYN_SHAPE_TYPE = DynShape
_SHAPE2_TYPE = Shape2

# 哨兵：表示"无需分派"，用 is 比较，避免与合法的 None 混淆。
# Sentinel meaning "no dispatch"; compared by identity so a legitimate None cannot be confused.
_NO_DISPATCH: Any = object()


def _dispatch_once(reshaped: Any, *, axis: Any) -> Any:
    """只调用一次特殊方法，不重复触发描述符 / Invoke a special method once without re-triggering descriptors.

    FS-005：NumPy 在归约时会**吞掉描述符查找抛出的异常**（它按类型探测特殊方法，
    异常被当作"没有这个方法"）。这里自己走 MRO、直接取 ``vars(base)[attr]``（0 次
    ``__get__``），再显式 ``__get__(None, klass)`` 一次，因此异常原样传播。
    FS-005: NumPy swallows exceptions raised while looking up special methods during a
    reduction (it probes by type and treats the exception as "no such method"). This walks the
    MRO itself, reads ``vars(base)[attr]`` directly (zero ``__get__`` calls) and then calls
    ``__get__(None, klass)`` exactly once, so the exception propagates unchanged.

    Args:
        reshaped: 已按逻辑内容重排的数组 / Array already reordered to its logical content.
        axis: 求和轴 / Summation axis.

    Returns:
        分派结果，或 ``_NO_DISPATCH`` 表示无特殊方法。
        Dispatch result, or ``_NO_DISPATCH`` when no special method exists.
    """
    for klass in type(reshaped).__mro__:
        namespace = vars(klass)
        if "__array_function__" in namespace:
            attr, base = "__array_function__", klass
            break
        if "__array_ufunc__" in namespace:
            attr, base = "__array_ufunc__", klass
            break
    else:
        return _NO_DISPATCH
    raw = namespace[attr]
    if raw is None:
        # 显式把特殊方法设为 None 表示"禁用该协议"，NumPy 对此抛 TypeError；
        # 这里必须同样抛错，不能静默回退到默认路径。检查必须在 __get__ 之前。
        # Setting the special method to None disables the protocol and NumPy raises TypeError;
        # this must raise too instead of silently falling back. The check must precede __get__.
        raise TypeError(f"{attr} 被显式禁用 / {attr} is explicitly disabled")
    implementation = raw.__get__(None, base)
    if implementation is None:
        # 显式把特殊方法设为 None 表示"禁用该协议"，NumPy 对此抛 TypeError；
        # 这里必须同样抛错，不能静默回退到默认路径。
        # Setting the special method to None disables the protocol and NumPy raises TypeError;
        # this must raise too instead of silently falling back to the default path.
        raise TypeError(f"{attr} 被显式禁用 / {attr} is explicitly disabled")
    if implementation is NotImplemented:
        # 返回 NotImplemented 的协议表示"不接管"，交回 NumPy 默认路径。
        # A NotImplemented protocol means "do not take over"; fall back to NumPy's default.
        return _NO_DISPATCH
    # 两个协议签名不同，必须按 NumPy 的原始形式调用，否则用户实现看到的参数不对。
    # The two protocols have different signatures and must be called in NumPy's original form,
    # otherwise user implementations observe the wrong arguments.
    kwargs = {} if axis is None else {"axis": axis}
    # implementation 经 __get__(None, base) 得到的是未绑定函数，self 要显式传入。
    # implementation came from __get__(None, base) and is therefore unbound; pass self explicitly.
    if attr == "__array_function__":
        # __array_function__(self, func, types, args, kwargs)
        dispatched = implementation(
            reshaped, np.sum, (type(reshaped),), (reshaped,), kwargs
        )
    else:
        # __array_ufunc__(self, ufunc, method, *inputs, **kwargs)
        # reduce 的 kwargs 必须带 NumPy 默认的 dtype/keepdims/where，用户实现按该形状断言。
        # reduce kwargs must carry NumPy's defaults for dtype/keepdims/where; user
        # implementations assert that exact shape.
        # ufunc 的 kwargs 永远带 axis（含 None），与 NumPy reduce 的实际调用一致。
        # ufunc kwargs always carry axis (including None), matching NumPy's real reduce call.
        dispatched = implementation(
            reshaped,
            np.add,
            "reduce",
            reshaped,
            axis=axis,
            dtype=None,
            keepdims=False,
            where=True,
        )
    if dispatched is NotImplemented:
        raise TypeError(
            "特殊方法返回 NotImplemented，无法归约 / "
            "special method returned NotImplemented and cannot be reduced"
        )
    return dispatched


def fast_sum(
    arr: MultiArray[Any, Any],
    *,
    axis: int | None = None,
) -> Any:
    """对多维数组进行快速求和。

    Fast summation over a multi-array using numpy backend.

    当 axis 为 None 时，对所有元素求和返回标量。
    当 axis 指定维度时，沿该轴求和返回新的 MultiArray。
    When axis is None, sums all elements and returns a scalar.
    When axis is given, sums along that axis and returns a
    new MultiArray.

    Args:
        arr: 输入多维数组。/ Input multi-array.
        axis: 求和轴，None 表示全部。/ Summation axis, None for all.

    Returns:
        求和结果（标量或新数组）。/ Sum result (scalar or new array).

    Raises:
        ValueError: axis 在最终 rank 上不存在时 / When axis does not exist on the final rank.
    """
    # 访问顺序是合同：data → lookup_reshape → shape → dims → reshape。
    # 逐步绑定既保持该顺序，又只读一次 shape，于是 storage_order 可以免费读。
    # The access order is contractual: data -> lookup_reshape -> shape -> dims -> reshape.
    # Binding each step keeps that order while reading shape exactly once, so storage_order
    # comes for free.
    data = arr._data
    capture = data.reshape
    shape = arr.shape
    reshaped = capture(shape.dims)
    # 全量归约的和与元素顺序无关，因此只有指定轴时才需要按 F 序重排。
    # An all-reduction total is independent of element order, so only an axis reduction needs
    # the F-order reinterpretation.
    if (
        axis is not None
        and isinstance(shape, (_DYN_SHAPE_TYPE, _SHAPE2_TYPE))
        # 只用导入时捕获的类判定"已知形状"：测试会把模块级 DynShape 换成工厂函数，
        # 因此不能对模块属性做 isinstance。
        # Only the classes captured at import identify a KNOWN shape: the tests replace the
        # module-level DynShape with a factory, so isinstance must not read the module
        # attribute.
        and shape.storage_order is StorageOrder.COLUMN_MAJOR
    ):
        # 列布局缓冲按 F 序解释才是逻辑内容；结果统一发布为行布局。
        # A column-layout buffer only carries the logical content when read in F order; the
        # result is published as row layout throughout.
        reshaped = np.reshape(np.ravel(reshaped), shape.dims, order="F")

    # 普通 ndarray 没有可接管的特殊方法，一次类型比较即可跳过整条协议路径。
    # A plain ndarray declares no special method to own, so one exact-type check skips the
    # whole protocol path.
    dispatched = (
        _NO_DISPATCH
        if type(reshaped) is np.ndarray
        else _dispatch_once(reshaped, axis=axis)
    )
    # 分派结果是否参与归约只看 axis：全量归约走标量出口，指定轴走数组出口。
    # Whether the dispatched value is an all-reduction depends only on axis: an all-reduction
    # leaves through the scalar exit, an axis reduction through the array exit.
    if axis is None:
        total = np.sum(reshaped) if dispatched is _NO_DISPATCH else dispatched
    else:
        # FS-006：轴回调可能把 rank 缩小到 axis 之外，此时 np.sum 会静默返回错值
        # （实测：axis=1 对 (2,3)→(6,) 返回全部元素之和；axis=2 对 (2,3,4)→(4,6) 返回 24 个原值）。
        # 契约要求"最终不存在的轴安全返回 OUT_OF_RANGE"，但 fast_sum 返回裸值、无法承载 Result；
        # 在类型改造前先抛 ValueError，绝不返回静默错值。
        # FS-006: an axis callback can shrink the rank past `axis`, and np.sum then returns a
        # wrong value silently (measured: axis=1 over (2,3)->(6,) yields the full total;
        # axis=2 over (2,3,4)->(4,6) returns all 24 values). The contract wants OUT_OF_RANGE, but
        # fast_sum returns a bare value and cannot carry a Result; raise ValueError until the
        # return type is migrated, never return a silently wrong value.
        if dispatched is _NO_DISPATCH:
            rank = np.ndim(reshaped)
            # 只检查真正的 int：axis 也可以是任意实现 __index__ 的协议对象，
            # 其语义由该对象自己决定。rank 0 上 axis 0/-1 合法（NumPy 语义）。
            # Only real ints are checked: axis may be any protocol object implementing
            # __index__, whose meaning is its own. On rank 0, axis 0/-1 is legal in NumPy.
            # 用 tuple.__iter__ 直接遍历，绕过子类可能覆盖的 __iter__：
            # axis 的"元组内容"是合同语义，不能被序列协议改写。
            # Iterate through tuple.__iter__ to bypass any __iter__ override on a subclass: the
            # tuple *contents* of axis are contractual and must not be rewritten by the sequence
            # protocol.
            requested = tuple.__iter__(axis) if isinstance(axis, tuple) else (axis,)
            for single in requested:
                if type(single) is not int:
                    continue
                if rank == 0 and single in (0, -1):
                    continue
                if single >= rank or single < -rank:
                    raise ValueError(
                        f"axis {single} 在最终 rank {rank} 上不存在 / "
                        f"axis {single} does not exist on the final rank {rank}"
                    )
        result = (
            np.sum(reshaped, axis=axis) if dispatched is _NO_DISPATCH else dispatched
        )
        if not hasattr(result, "flatten"):
            # 秩归约到标量时没有 shape/flatten；按归约形状建标量数组，不要求叶实现 ndarray 属性。
            # A reduction to a scalar has no shape or flatten; build the scalar array from the
            # reduction shape instead of asking a leaf to behave like an ndarray.
            # 判据是"有没有 flatten"而不是 ndim：自定义输出协议对象的 ndim 为 0，但仍提供 flatten。
            # The test is "has flatten", not ndim: a custom output-protocol object reports ndim 0
            # yet still provides flatten.
            return MultiArray(
                DynShape(dims=()), np.array([result], dtype=reshaped.dtype)
            )
        new_shape = DynShape(dims=result.shape)
        flat_data = result.flatten()
        return MultiArray(new_shape, flat_data)

    # FS-002：复数全量归约必须保留虚部，不能经 float 包装静默丢弃。
    # FS-002: an all-reduction over complex values must keep the imaginary part instead of
    # silently discarding it through a float envelope.
    if isinstance(total, (complex, np.complexfloating)):
        return total
    try:
        converted = float(total)
    except (TypeError, ValueError):
        # FS-003 补充：float 无法转换的对象（如 tuple 叶）必须原样返回，不能抛错。
        # FS-003 addendum: an object float cannot convert (e.g. a tuple leaf) must be returned
        # as-is, not raised.
        return total
    # FS-003：超出 float 精确整数范围或非有限时保留原值，不能静默舍入。
    # FS-003: keep the original when it exceeds float's exact integer range or is non-finite;
    # never round silently.
    if not math.isfinite(converted):
        return total
    if isinstance(total, (int, np.integer)) and int(converted) != int(total):
        return total
    return converted
