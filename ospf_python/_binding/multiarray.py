"""Rust 形状、精确数组与对象数组门面 / Facades for Rust shapes, exact arrays and object arrays."""

from __future__ import annotations

from dataclasses import dataclass, replace
from operator import eq
from sys import maxsize
from threading import local
from typing import TYPE_CHECKING, Any, cast

import numpy as np

from ospf_python import _native
from ospf_python._binding.array_callback import (
    FlatMapCallback,
    MapCallback,
    ReduceCallback,
    map_callback,
    map_callbacks,
    reduce_callback,
)
from ospf_python._binding.numeric import Rational, RationalArray
from ospf_python._binding.result import BindingResult, invalid, invoke, unsupported
from ospf_python.multiarray.shape import (
    DynShape,
    Shape1,
    Shape2,
    Shape3,
    Shape4,
    StorageOrder,
)
from ospf_python.multiarray.shape import Shape as ShapeProtocol
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Self

__all__ = [
    "MappedMultiArrayView",
    "MultiArray",
    "MultiArrayIterator",
    "MutableMultiArray",
    "MultiArrayView",
    "MutableMultiArrayView",
    "RationalMultiArray",
    "Shape",
]


def _integer_tuple(value: object) -> bool:
    return type(value) is tuple and all(
        isinstance(item, int) and not isinstance(item, bool) for item in value
    )


@dataclass(frozen=True, slots=True, eq=False)
class MultiArrayIterator[T]:
    """逐次读取 Rust 槽位的单一游标 / Single cursor reading Rust slots on each advance.

    Attributes:
        _handle: 持有源、访问元数据和唯一位置的原生游标 / Native cursor owning source, access metadata and the only position.
    """

    _handle: _native.MultiArrayIterator

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> T:
        return cast("T", next(self._handle))

    def __length_hint__(self) -> int:
        return self._handle.__length_hint__()

    def advance(self) -> BindingResult[tuple[bool, T | None]]:
        """受检消费一个位置，以存在标志区分 None 叶与耗尽 / Consume one checked position, distinguishing a None leaf from exhaustion.

        Returns:
            (True, 叶)、耗尽时 (False, None) 或 Failed / (True, leaf), (False, None) at exhaustion, or Failed.
        """
        return cast(
            "BindingResult[tuple[bool, T | None]]", invoke(self._handle.advance)
        )

    def close(self) -> None:
        """幂等终结并释放源，不再读取槽位 / Finalize idempotently and release the source without further slot reads."""
        self._handle.close()


def _live_iterator(
    *,
    owner: object,
    handle: _native.MultiArray | _native.MutableMultiArray,
    access_order: StorageOrder | None,
    region: _native.MultiArrayView | None = None,
) -> BindingResult[MultiArrayIterator[Any]]:
    if access_order is not None and not isinstance(access_order, StorageOrder):
        return invalid("无效访问顺序 / Invalid access order")
    return invoke(
        lambda: _native._create_reference_iterator(
            source=handle,
            owner=owner,
            region=region,
            column_major=(
                None
                if access_order is None
                else access_order is StorageOrder.COLUMN_MAJOR
            ),
        )
    ).map(MultiArrayIterator)


def _comparison_boolean(value: Any) -> bool | BindingResult[bool]:
    if type(value) in (bool, np.bool_):
        return bool(value)
    return invalid(
        "元素比较必须返回 bool 或 NumPy bool / Element comparison must return bool or NumPy bool"
    )


class _DescriptionState(local):
    def __init__(self) -> None:
        self.active: set[int] = set()


_description_state = _DescriptionState()


def _description_string(value: Any) -> str | BindingResult[str]:
    if type(value) is str:
        return value
    return invalid(
        "描述格式器必须返回内置 str / Description formatter must return a built-in str"
    )


def _described(
    *,
    handle: _native.MultiArray | _native.MutableMultiArray,
    region: _native.MultiArrayView | None = None,
    formatter: object,
    max_items: int,
    max_chars: int,
) -> BindingResult[str]:
    if not callable(formatter):
        return invalid("描述格式器必须可调用 / Description formatter must be callable")
    if type(max_items) is not int or not 0 <= max_items <= maxsize:
        return invalid(
            "max_items 必须为原生容量内非负整数 / max_items must be a nonnegative integer within native capacity"
        )
    if type(max_chars) is not int or not 3 <= max_chars <= maxsize:
        return invalid(
            "max_chars 必须为至少 3 的原生容量内整数 / max_chars must be an integer of at least 3 within native capacity"
        )
    key = id(handle)
    active = _description_state.active
    if key in active:
        return Ok("..." if max_chars < 17 else "<recursive array>")
    active.add(key)
    try:
        return map_callbacks(
            callbacks=(formatter, _description_string),
            flat=False,
            operation=lambda callback: _native._describe_reference_array(
                source=handle,
                region=region,
                callback=callback,
                max_items=max_items,
                max_chars=max_chars,
            ),
        )
    finally:
        # 只记录线程内原生源身份，不持久保活数组；异常和进程控制路径也清理。 / Keep only thread-local native source identities; clean up after exceptions and process-control exits.
        active.remove(key)


def _comparison_operand(
    value: object,
) -> BindingResult[
    tuple[_native.MultiArray | _native.MutableMultiArray, _native.MultiArrayView | None]
]:
    if isinstance(value, (MultiArray, MutableMultiArray)):
        return Ok((value._handle, None))
    if isinstance(value, MultiArrayView):
        return Ok((value._source._handle, value._handle))
    if isinstance(value, MappedMultiArrayView):
        return unsupported(
            "惰性映射须先显式物化再比较 / Lazy mappings must be explicitly materialized before comparison"
        )
    return invalid(
        "比较需要 Rust 引用数组或矩形视图 / Comparison requires Rust reference arrays or rectangular views"
    )


def _equals(
    *, source: object, other: object, comparator: object
) -> BindingResult[bool]:
    if not callable(comparator):
        return invalid("元素比较器必须可调用 / Element comparator must be callable")
    left = _comparison_operand(source)
    if isinstance(left, Failed):
        return Failed(left.error)
    right = _comparison_operand(other)
    if isinstance(right, Failed):
        return Failed(right.error)
    left_handle, left_region = left.unwrap()
    right_handle, right_region = right.unwrap()
    ordinal: int | None = None

    def compare(request: tuple[int, Any, Any]) -> Any:
        nonlocal ordinal
        ordinal = request[0]
        return comparator(request[1], request[2])

    result = map_callbacks(
        callbacks=(compare, _comparison_boolean),
        flat=False,
        operation=lambda callback: _native._compare_reference_arrays(
            left=left_handle,
            right=right_handle,
            callback=callback,
            left_region=left_region,
            right_region=right_region,
            builtin_equality=comparator is eq,
        ),
    )
    if isinstance(result, Failed) and result.error.value.callback_index is not None:
        return Failed(
            ExErr(
                _code=result.error.code,
                _message=result.error.message,
                value=replace(result.error.value, callback_index=ordinal),
            )
        )
    return result


def _object_state(instance: object) -> Any:
    """显式对象状态钩子，兼容 pickle 0/1 的槽位检查 / Explicit state hook satisfying pickle 0/1 slot checks.

    Args:
        instance: 本门面的对象 / Facade instance.

    Returns:
        标准字典/槽位状态 / Standard dict/slot state.
    """
    return object.__getstate__(instance)


def _restore_object_state(
    instance: object, state: tuple[dict[str, Any] | None, dict[str, Any]]
) -> None:
    """恢复标准对象协议的字典与槽位，不运行构造器 / Restore standard object dict/slots without running constructors.

    Args:
        instance: 已由 pickle/copy memo 登记的空对象 / Empty object already registered in the pickle/copy memo.
        state: object.__getstate__ 提供的字典与槽位 / Dict and slots supplied by object.__getstate__.
    """
    dictionary, slots = state
    if dictionary is not None:
        object.__getattribute__(instance, "__dict__").update(dictionary)
    for name, value in slots.items():
        object.__setattr__(instance, name, value)


def _reference_snapshot(
    handle: _native.MultiArray | _native.MutableMultiArray, kind: str
) -> BindingResult[dict[str, Any]]:
    shape = handle.shape
    return invoke(lambda: handle.flatten(shape.column_major)).map(
        lambda values: {
            "schema": "ospf.python-reference-array",
            "version": 1,
            "kind": kind,
            "dims": tuple(shape.dims),
            "storage_order": "COLUMN_MAJOR" if shape.column_major else "ROW_MAJOR",
            "values": values,
        }
    )


def _snapshot_input(
    payload: object, kind: str
) -> BindingResult[tuple[list[Any], Shape, StorageOrder]]:
    fields = {"schema", "version", "kind", "dims", "storage_order", "values"}
    if (
        type(payload) is not dict
        or not all(type(key) is str for key in payload)
        or set(payload) != fields
        or type(payload["schema"]) is not str
        or payload["schema"] != "ospf.python-reference-array"
        or type(payload["version"]) is not int
        or payload["version"] != 1
        or type(payload["kind"]) is not str
        or payload["kind"] != kind
        or type(payload["storage_order"]) is not str
        or payload["storage_order"] not in ("ROW_MAJOR", "COLUMN_MAJOR")
        or not _integer_tuple(payload["dims"])
        or type(payload["values"]) is not list
    ):
        return invalid("无效对象数组快照 / Invalid reference-array snapshot")
    order = StorageOrder[payload["storage_order"]]
    return cached_shape(dims=payload["dims"], storage_order=order).map(
        lambda shape: (payload["values"], shape, order)
    )


_SHAPE_CACHE: dict[tuple[tuple[int, ...], int], Shape] = {}
_SHAPE_CACHE_LIMIT = 512


def cached_shape(
    *, dims: object, storage_order: StorageOrder, cls: type[Shape] = None  # type: ignore[assignment]
) -> BindingResult[Shape]:
    """构造（或复用）不可变原生形状。

    `Shape` 是**不可变**的 Rust 动态形状（`_native.pyi` 的类文档原文：「不可变 Rust 动态形状」），
    所以同一个 `(dims, storage_order)` 复用同一个实例是安全的。
    实测每次 `_create_shape` 是一次原生往返；`reshape` 一次调用就要一次，
    而 reshape 常常是「同一个目标形状反复用」（例如循环里 reshape 到同一尺寸）。

    `Shape` is an IMMUTABLE Rust dynamic shape, so reusing one instance per
    `(dims, storage_order)` is safe. Each `_create_shape` is a native round trip and `reshape`
    performs one per call, while the same target shape is often reused.

    Args:
        dims: 正整数维度序列。/ Positive axis sizes.
        storage_order: 存储顺序。/ Storage order.
        cls: 形状类；子类不走缓存，以保持其工厂语义。/ Shape class; subclasses bypass the
            cache so their factory semantics are preserved.

    Returns:
        原生形状或失败。/ Native shape or failure.
    """
    if cls is not None and cls is not Shape:
        # 子类必须由它自己的工厂构造（`test_public_scalar_snapshot_and_native_subclass_factories`
        # 要求返回子类实例）。 / A subclass must be built by its own factory.
        return cls.create(dims=dims, storage_order=storage_order)  # type: ignore[arg-type]
    try:
        key = (tuple(int(value) for value in dims), int(storage_order.value))  # type: ignore[union-attr]
    except (TypeError, ValueError, AttributeError):
        # 键不可构造时退回原生校验路径，保持原有失败语义。
        # Fall back to the native path when a key cannot be built, preserving the original
        # failure semantics.
        return Shape.create(dims=dims, storage_order=storage_order)  # type: ignore[arg-type]
    cached = _SHAPE_CACHE.get(key)
    if cached is not None:
        return Ok(cached)
    built = Shape.create(dims=key[0], storage_order=storage_order)
    if isinstance(built, Failed):
        return Failed(built.error)
    shape = built.unwrap()
    if len(_SHAPE_CACHE) >= _SHAPE_CACHE_LIMIT:
        _SHAPE_CACHE.clear()
    _SHAPE_CACHE[key] = shape
    return Ok(shape)


def _numpy_snapshot(
    *, values: object, copy: bool, storage_order: StorageOrder
) -> BindingResult[tuple[list[Any], Shape]]:
    if not isinstance(copy, bool):
        return invalid("copy 必须为 bool / copy must be bool")
    if not copy:
        return unsupported(
            "尚不支持共享 NumPy 缓冲 / Shared NumPy buffers are not supported"
        )
    if type(values) is not np.ndarray:
        return invalid(
            "需要内置 ndarray，不隐式调用数组协议 / Built-in ndarray required; no implicit array protocol"
        )
    if values.dtype.kind not in "biufcUSmMO":
        return unsupported(
            "该 NumPy dtype 的所有权尚未支持 / Ownership for this NumPy dtype is not supported"
        )
    shape = cached_shape(dims=values.shape, storage_order=storage_order)
    if isinstance(shape, Failed):
        return Failed(shape.error)
    # 标量由 NumPy 取得；object 项保留身份，不持有外部缓冲。 / NumPy extracts scalars; object entries retain identity without retaining the external buffer.
    return Ok((list(values.ravel(order="C")), shape.unwrap()))


def _legacy_input(
    *, payload: object, copy: bool, standard_layout: bool
) -> BindingResult[tuple[list[Any], Shape]]:
    if not isinstance(copy, bool):
        return invalid("copy 必须为 bool / copy must be bool")
    if not copy:
        return unsupported(
            "旧字段导入不保留共享缓冲 / Legacy-state import does not preserve shared buffers"
        )
    if (
        type(payload) is not dict
        or not all(type(key) is str for key in payload)
        or set(payload) != {"_shape", "_data"}
    ):
        return invalid(
            "需要且仅接受旧 _shape/_data 字段 / Exactly the legacy _shape/_data fields are required"
        )
    data = payload["_data"]
    if type(data) is not np.ndarray or data.ndim != 1:
        return invalid(
            "旧数据必须为一维内置 ndarray / Legacy data must be a one-dimensional built-in ndarray"
        )
    shape = Shape.from_shape(payload["_shape"], standard_layout=standard_layout)
    if isinstance(shape, Failed):
        return Failed(shape.error)
    target = shape.unwrap()
    if data.size != target.size:
        return invalid(
            "旧数据数量与形状不符 / Legacy data count does not match its shape"
        )
    if data.dtype.kind not in "biufcUSmMO":
        return unsupported(
            "该 NumPy dtype 的所有权尚未支持 / Ownership for this NumPy dtype is not supported"
        )
    from ospf_python._binding.public_array_access import raw_snapshot

    # 旧字段是一维物理序列；原生收集器保留 scalar 类型，不再 ravel 或重建一维形状。 / Legacy fields are a physical sequence; native collection preserves scalar types without ravel or rebuilding a 1-D shape.
    return raw_snapshot(data=data, count=target.size).map(
        lambda values: (values, target)
    )


def _region(
    *,
    source: Shape,
    offsets: tuple[int, ...] | None,
    shape: Shape | ShapeProtocol | None,
) -> BindingResult[_native.MultiArrayView]:
    if offsets is not None and not _integer_tuple(offsets):
        return invalid("偏移必须为整数 tuple / Offsets must be an integer tuple")
    if shape is not None and not isinstance(shape, Shape):
        snapshot = Shape.from_shape(shape)
        if isinstance(snapshot, Failed):
            return Failed(snapshot.error)
        shape = snapshot.unwrap()
    return invoke(
        lambda: _native._create_multiarray_view(
            source_shape=source._handle,
            offsets=None if offsets is None else list(offsets),
            shape=None if shape is None else shape._handle,
        )
    )


def _updates[T](values: list[tuple[tuple[int, ...], T]]) -> bool:
    return type(values) is list and all(
        type(item) is tuple and len(item) == 2 and _integer_tuple(item[0])
        for item in values
    )


def _mapped[U](
    *,
    handle: _native.MultiArray | _native.MutableMultiArray,
    callback: object,
    flat: bool,
    access_order: StorageOrder,
    shape: Shape | ShapeProtocol | None = None,
    region: _native.MultiArrayView | None = None,
) -> BindingResult[MultiArray[U]]:
    if not isinstance(access_order, StorageOrder):
        return invalid("无效访问顺序 / Invalid access order")
    output_shape = None
    if flat:
        if shape is None:
            return invalid(
                "flat_map 必须指定输出形状 / flat_map requires an output shape"
            )
        if not isinstance(shape, Shape):
            snapshot = Shape.from_shape(shape)
            if isinstance(snapshot, Failed):
                return Failed(snapshot.error)
            shape = snapshot.unwrap()
        output_shape = shape._handle
    if region is None:
        return map_callback(
            callback=callback,
            flat=flat,
            operation=lambda adapted: handle.mapped(
                callback=adapted,
                column_major=access_order is StorageOrder.COLUMN_MAJOR,
                output_shape=output_shape,
            ),
        ).map(MultiArray)
    return map_callback(
        callback=callback,
        flat=flat,
        operation=lambda adapted: handle.region_mapped(
            region=region,
            callback=adapted,
            column_major=access_order is StorageOrder.COLUMN_MAJOR,
            output_shape=output_shape,
        ),
    ).map(MultiArray)


def _reduced[T](
    *,
    handle: _native.MultiArray | _native.MutableMultiArray,
    callback: ReduceCallback[T],
    access_order: StorageOrder,
    region: _native.MultiArrayView | None = None,
) -> BindingResult[T]:
    if not isinstance(access_order, StorageOrder):
        return invalid("无效访问顺序 / Invalid access order")
    return reduce_callback(
        callback=callback,
        operation=lambda adapted: handle.reduced(
            callback=adapted,
            column_major=access_order is StorageOrder.COLUMN_MAJOR,
            region=region,
        ),
    )


@dataclass(frozen=True, slots=True, eq=False)
class Shape:
    """只由 Rust 持有维度和步长的形状 / Shape with dimensions and strides owned only by Rust.

    使用 create 创建；零维表示单个标量，不接受零长维度。
    Use create; zero dimensions mean one scalar, not a zero-length axis.
    """

    _handle: _native.Shape

    __getstate__ = _object_state
    __setstate__ = _restore_object_state

    @classmethod
    def create(
        cls,
        *,
        dims: tuple[int, ...],
        storage_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[Self]:
        """检查形状边界后委托 Rust / Check shape boundaries and delegate to Rust.

        Args:
            dims: 正整数维度；空 tuple 为标量 / Positive axes; empty tuple is a scalar.
            storage_order: 行或列存储顺序 / Row or column storage order.

        Returns:
            Rust 形状或输入/大小溢出失败 / Rust shape or input/size-overflow failure.
        """
        if not _integer_tuple(dims) or not isinstance(storage_order, StorageOrder):
            return invalid(
                "需要整数维度与存储顺序 / Integer dimensions and storage order required"
            )
        return invoke(
            lambda: _native._create_shape(
                dims=list(dims),
                column_major=storage_order is StorageOrder.COLUMN_MAJOR,
            )
        ).map(cls)

    @classmethod
    def from_shape(
        cls, source: ShapeProtocol, *, standard_layout: bool = False
    ) -> BindingResult[Self]:
        """从公开形状协议取得受检快照，不调用旧索引算法 / Take a checked public-shape snapshot without legacy indexing.

        Args:
            source: 内置或用户实现的公开 Shape 协议 / Built-in or user-defined public Shape protocol.
            standard_layout: 自定义类型必须显式确认 dims/order 为标准映射 / Custom types must explicitly confirm standard dims/order mapping.

        Returns:
            独立 Rust 形状或协议/整数范围失败 / Detached Rust shape or protocol/integer-range failure.
        """
        if not isinstance(standard_layout, bool):
            return invalid("standard_layout 必须为 bool / standard_layout must be bool")
        builtin = type(source) in (Shape1, Shape2, Shape3, Shape4, DynShape)
        if not builtin and not standard_layout:
            return invalid(
                "自定义形状必须显式确认标准布局 / Custom shapes require explicit standard-layout confirmation"
            )
        try:
            if not builtin and not isinstance(source, ShapeProtocol):
                return invalid(
                    "需要公开 Shape 协议 / The public Shape protocol is required"
                )
            dims = source.dims
            storage_order = source.storage_order
        except Exception as error:
            # 用户协议属性是外部回调边界；不中断 Result 传播。 / User protocol properties are an external callback boundary.
            return invalid(f"读取形状协议失败 / Reading shape protocol failed: {error}")
        # 走带缓存的构造器：同一个 `(dims, order)` 复用同一个不可变原生形状。
        # Use the cached builder: one immutable native shape per `(dims, order)`.
        return cached_shape(dims=dims, storage_order=storage_order, cls=cls)

    @property
    def dims(self) -> tuple[int, ...]:
        """返回独立的维度快照 / Return a detached dimension snapshot."""
        return tuple(self._handle.dims)

    @property
    def ndim(self) -> int:
        """维度数量 / Number of axes."""
        return len(self._handle.dims)

    @property
    def size(self) -> int:
        """元素数量，最大 sys.maxsize / Element count, at most sys.maxsize."""
        return self._handle.size

    @property
    def storage_order(self) -> StorageOrder:
        """返回 Rust 存储顺序 / Return the Rust storage order."""
        return (
            StorageOrder.COLUMN_MAJOR
            if self._handle.column_major
            else StorageOrder.ROW_MAJOR
        )

    def strides(self) -> tuple[int, ...]:
        """返回 Rust 计算的步长快照 / Return a snapshot of Rust-computed strides."""
        return tuple(self._handle.strides())

    def index_of(self, indices: tuple[int, ...]) -> BindingResult[int]:
        """严格转换坐标，不截断或处理负索引 / Convert coordinates strictly without truncation or negative indexing.

        Args:
            indices: 与 ndim 一致的非负整数 tuple / Nonnegative integer tuple matching ndim.

        Returns:
            存储线性索引或 Failed / Storage offset or Failed.
        """
        if not _integer_tuple(indices):
            return invalid("索引必须为整数 tuple / Indices must be an integer tuple")
        return invoke(lambda: self._handle.index_of(list(indices)))

    def vector_of(self, index: int) -> BindingResult[tuple[int, ...]]:
        """将合法线性索引转换为坐标 / Convert a valid storage offset to coordinates.

        Args:
            index: 范围为 [0, size) 的整数 / Integer in [0, size).

        Returns:
            独立坐标或 Failed / Detached coordinates or Failed.
        """
        if not isinstance(index, int) or isinstance(index, bool):
            return invalid("索引必须为整数 / Index must be an integer")
        return invoke(lambda: self._handle.vector_of(index)).map(tuple)

    def indices_of(self, vectors: list[tuple[int, ...]]) -> BindingResult[list[int]]:
        """单次 FFI 原子转换坐标批次 / Convert coordinates atomically in one FFI call.

        Args:
            vectors: 坐标 tuple 的 list / List of coordinate tuples.

        Returns:
            全部线性索引或 Failed，不返回部分值 / All storage offsets or Failed, never partial output.
        """
        if not isinstance(vectors, list) or not all(_integer_tuple(v) for v in vectors):
            return invalid(
                "需要坐标 tuple 的 list / A list of coordinate tuples is required"
            )
        return invoke(lambda: self._handle.indices_of([list(v) for v in vectors]))


@dataclass(frozen=True, slots=True, eq=False)
class MultiArray[T]:
    """Rust 存储、保留 Python 元素身份的不可变容器 / Immutable Rust storage preserving Python element identity.

    仅容器独立，元素不深拷贝；不共享 NumPy 缓冲。
    Containers are independent, elements are not deep-copied; no NumPy buffer sharing.
    """

    _handle: _native.MultiArray

    __getstate__ = _object_state
    __setstate__ = _restore_object_state

    def describe(
        self, *, formatter: object = repr, max_items: int = 20, max_chars: int = 4096
    ) -> BindingResult[str]:
        """受检描述逻辑前缀，不更改 Python repr / Describe a checked logical prefix without changing Python repr.

        Args:
            formatter: 每叶字符串格式器，可返回单层 Result / Per-leaf string formatter, optionally returning one Result layer.
            max_items: 最多显示的逻辑叶数，允许零 / Maximum logical leaves displayed, allowing zero.
            max_chars: 包括元数据与省略号的字符上限，至少为 3 / Character limit including metadata and ellipses, at least 3.

        Returns:
            有界字符串或保留格式器上下文的 Failed / Bounded string or Failed retaining formatter context.
        """
        return _described(
            handle=self._handle,
            formatter=formatter,
            max_items=max_items,
            max_chars=max_chars,
        )

    def equals(self, other: object, *, comparator: object = eq) -> BindingResult[bool]:
        """受检比较逻辑坐标，不忽略布局或静默改变 __eq__ / Compare checked logical coordinates without ignoring layout or changing __eq__.

        Args:
            other: Rust 引用数组或矩形视图 / Rust reference array or rectangular view.
            comparator: 二元比较器，返回 bool/NumPy bool 或相应 Result / Binary comparator returning bool/NumPy bool or the corresponding Result.

        Returns:
            相等与否或保留元素回调上下文的 Failed / Equality or Failed retaining element callback context.
        """
        return _equals(source=self, other=other, comparator=comparator)

    @classmethod
    def from_list(
        cls, *, data: object, shape: Shape | ShapeProtocol
    ) -> BindingResult[Self]:
        """按显式形状解析嵌套结构，不推断 dtype 或广播 / Parse nested structure against an explicit shape without dtype inference or broadcasting.

        Args:
            data: 结构层仅为内置 list/tuple；到达 ndim 后是不透明叶 / Structural axes are built-in list/tuple; values at ndim are opaque leaves.
            shape: 每轴长度严格匹配的 Rust 或内置公开形状 / Rust or built-in public shape with exact axis lengths.

        Returns:
            保持逻辑坐标与叶身份的独立 Rust 存储或 Failed / Independent Rust storage preserving logical coordinates and leaf identity, or Failed.
        """
        if not isinstance(shape, Shape):
            snapshot = Shape.from_shape(shape)
            if isinstance(snapshot, Failed):
                return Failed(snapshot.error)
            shape = snapshot.unwrap()
        native_shape = shape._handle
        return invoke(
            lambda: _native._multiarray_from_nested(data=data, shape=native_shape)
        ).map(cls)

    def to_snapshot(self) -> BindingResult[dict[str, Any]]:
        """导出版本化 Python 引用快照，不序列化叶对象 / Export a versioned Python-reference snapshot without serializing leaves.

        Returns:
            独立 DTO 容器或 Failed；叶对象仍共享 / Detached DTO container or Failed, with shared leaves.
        """
        return _reference_snapshot(self._handle, "immutable")

    @classmethod
    def from_snapshot(cls, payload: object) -> BindingResult[Self]:
        """受检恢复 Python 引用快照，不隐式深拷贝 / Restore a checked Python-reference snapshot without implicit deep-copy.

        Args:
            payload: schema/version/kind/布局/值齐全的内置 dict / Built-in dict with schema, version, kind, layout and values.

        Returns:
            独立 Rust 容器或 Failed；对象环的重定位由 pickle/copy memo 负责 / Independent Rust storage or Failed; pickle/copy memo handles graph relocation.
        """
        return _snapshot_input(payload, "immutable").flat_map(
            lambda parts: cls.create(
                values=parts[0], shape=parts[1], access_order=parts[2]
            )
        )

    @classmethod
    def from_legacy_state(
        cls, *, payload: object, copy: bool, standard_layout: bool = False
    ) -> BindingResult[Self]:
        """显式复制旧字段为 Rust 存储，不接管旧 pickle / Explicitly copy legacy fields into Rust storage, not legacy pickle restoration.

        Args:
            payload: 仅含 _shape 和一维 ndarray _data 的内置 dict / Built-in dict containing only _shape and flat ndarray _data.
            copy: 必须显式为 True；不保留共享缓冲 / Must explicitly be True; shared buffers are not preserved.
            standard_layout: 自定义形状须显式确认标准映射 / Custom shapes require explicit standard-mapping confirmation.

        Returns:
            独立容器或 Failed；保留叶身份及 NumPy 标量类型，不重定位对象图 / Independent storage or Failed; preserves leaf identity and NumPy scalar types, without graph relocation.
        """
        return _legacy_input(
            payload=payload, copy=copy, standard_layout=standard_layout
        ).flat_map(
            lambda parts: cls.create(
                values=parts[0], shape=parts[1], access_order=parts[1].storage_order
            )
        )

    @classmethod
    def full(cls, *, shape: Shape | ShapeProtocol, value: T) -> BindingResult[Self]:
        """由 Rust 填充同一对象引用，不推断 dtype 或广播 / Fill identical references in Rust without dtype inference or broadcasting.

        Args:
            shape: Rust 或内置公开形状 / Rust or built-in public shape.
            value: 每个槽位持有的同一对象，允许 None / Identical object held by every slot, including None.

        Returns:
            独立容器或形状/容量失败 / Independent container or shape/capacity failure.
        """
        if not isinstance(shape, Shape):
            snapshot = Shape.from_shape(shape)
            if isinstance(snapshot, Failed):
                return Failed(snapshot.error)
            shape = snapshot.unwrap()
        native_shape = shape._handle
        return invoke(
            lambda: _native._full_multiarray(shape=native_shape, value=value)
        ).map(cls)

    @staticmethod
    def zeros(*, shape: Shape | ShapeProtocol) -> BindingResult[MultiArray[float]]:
        """填充内置 float 零，不建立 NumPy 镜像 / Fill built-in float zeros without a NumPy mirror.

        Args:
            shape: Rust 或内置公开形状 / Rust or built-in public shape.

        Returns:
            全零基础容器或 Failed / Zero-filled base container or Failed.
        """
        return MultiArray[float].full(shape=shape, value=0.0)

    @staticmethod
    def ones(*, shape: Shape | ShapeProtocol) -> BindingResult[MultiArray[float]]:
        """填充内置 float 一，不建立 NumPy 镜像 / Fill built-in float ones without a NumPy mirror.

        Args:
            shape: Rust 或内置公开形状 / Rust or built-in public shape.

        Returns:
            全一基础容器或 Failed / One-filled base container or Failed.
        """
        return MultiArray[float].full(shape=shape, value=1.0)

    @classmethod
    def from_numpy(
        cls,
        *,
        values: object,
        copy: bool,
        storage_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[Self]:
        """显式快照 NumPy 输入，不隐式共享 / Explicitly snapshot NumPy input without implicit sharing.

        Args:
            values: 内置 ndarray，支持 strided/read-only/object / Built-in ndarray, including strided/read-only/object.
            copy: 必须显式为 True；False 返回 NOT_SUPPORTED / Must explicitly be True; False returns NOT_SUPPORTED.
            storage_order: Rust 内部存储顺序 / Rust storage order.

        Returns:
            独立 Rust 容器或 Failed；object 项仍保持身份 / Independent Rust container or Failed; object entries keep identity.
        """
        return _numpy_snapshot(
            values=values, copy=copy, storage_order=storage_order
        ).flat_map(lambda snapshot: cls.create(values=snapshot[0], shape=snapshot[1]))

    @classmethod
    def create(
        cls,
        *,
        values: list[T],
        shape: Shape | ShapeProtocol,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[Self]:
        """原子接收元素引用并按 Rust 布局存储 / Atomically ingest element references into Rust storage.

        Args:
            values: 内置 list；保持元素身份 / Built-in list; preserves element identity.
            shape: Rust 或内置公开形状 / Rust or built-in public shape.
            access_order: 输入遍历顺序 / Input traversal order.

        Returns:
            独立数组或 Failed / Independent array or Failed.
        """
        if type(values) is not list or not isinstance(access_order, StorageOrder):
            return invalid(
                "需要内置 list 和访问顺序 / Built-in list and access order required"
            )
        if not isinstance(shape, Shape):
            snapshot = Shape.from_shape(shape)
            if isinstance(snapshot, Failed):
                return Failed(snapshot.error)
            shape = snapshot.unwrap()
        native_shape = shape._handle
        return invoke(
            lambda: _native._create_multiarray(
                values=values,
                shape=native_shape,
                column_major=access_order is StorageOrder.COLUMN_MAJOR,
            )
        ).map(cls)

    @property
    def shape(self) -> Shape:
        """返回独立形状快照 / Return a detached shape snapshot."""
        return Shape(self._handle.shape)

    def __len__(self) -> int:
        return self._handle.shape.size

    def at(self, indices: tuple[int, ...]) -> BindingResult[T]:
        """返回同一元素对象 / Return the identical element object.

        Args:
            indices: 完整非负整数坐标 / Complete nonnegative integer coordinates.

        Returns:
            原元素（包括 None）或 Failed / Original element (including None) or Failed.
        """
        if not _integer_tuple(indices):
            return invalid("索引必须为整数 tuple / Indices must be an integer tuple")
        return cast("BindingResult[T]", invoke(lambda: self._handle.at(list(indices))))

    def get(self, *indices: int) -> T:
        """旧 `get` 的等价物，按原始 Python 顺序返回叶值。 / Equivalent of the legacy `get`, returning the leaf in the original Python order.

        Args:
            indices: 多维索引 / Multi-dimensional indices.

        Returns:
            指定位置的元素 / Element at the position.

        Raises:
            ValueError: 坐标越界或不是整数时 / When a coordinate is out of range or not an integer.
        """
        result = self.at(indices)
        return result.unwrap()

    def at_many(
        self, indices: list[tuple[int, ...]]
    ) -> BindingResult[list[T]]:
        """整批读取共享槽位，供公共 `at_many` 原样保留。 / Batch read shared slots so the public `at_many` is preserved verbatim.

        Args:
            indices: 完整非负坐标列表 / List of complete nonnegative coordinates.

        Returns:
            按输入顺序排列的原元素，或 Failed / Original elements in input order, or Failed.
        """
        for coordinate in indices:
            if not _integer_tuple(coordinate):
                return invalid(
                    "索引必须为整数 tuple / Indices must be an integer tuple"
                )
        return cast(
            "BindingResult[list[T]]",
            invoke(lambda: self._handle.at_many([list(c) for c in indices])),
        )

    def to_list(self) -> BindingResult[T | list[Any]]:
        """按逻辑行坐标构建嵌套 list，标量返回原元素 / Build nested lists in logical row order; a scalar returns its element.

        Returns:
            独立容器结构或 Failed，元素身份不变 / Independent container structure or Failed, preserving element identity.
        """
        return invoke(self._handle.to_list)

    def reduce(
        self,
        callback: ReduceCallback[T],
        *,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[T]:
        """在完整 Rust 槽位快照上左结合归约 / Left-fold a complete Rust slot snapshot.

        Args:
            callback: 二元函数，可返回普通值或单层 Result / Binary function returning a value or one Result layer.
            access_order: 坐标遍历顺序，与存储布局独立 / Coordinate traversal order independent of storage layout.

        Returns:
            完整归约值或 Failed；单元素不执行函数 / Complete fold value or Failed; singleton input skips the function.
        """
        return _reduced(
            handle=self._handle,
            callback=callback,
            access_order=access_order,
        )

    def iter_live(
        self, *, access_order: StorageOrder | None = None
    ) -> BindingResult[MultiArrayIterator[T]]:
        """创建逐次读取的原生游标，不预先快照元素 / Create a native cursor reading per advance without snapshotting elements.

        Args:
            access_order: None 为物理顺序，否则显式按坐标遍历 / None for physical order, otherwise explicit coordinate traversal.

        Returns:
            保活源且观察后续槽位写入的游标或 Failed / Cursor retaining its source and observing later slot writes, or Failed.
        """
        return _live_iterator(
            owner=self, handle=self._handle, access_order=access_order
        )

    def iter_snapshot(
        self, *, access_order: StorageOrder = StorageOrder.ROW_MAJOR
    ) -> BindingResult[Iterator[T]]:
        """一次受检快照后返回标准迭代器 / Return a standard iterator after one checked snapshot.

        Args:
            access_order: 坐标遍历顺序 / Coordinate traversal order.

        Returns:
            不观察后续槽位写入的迭代器或 Failed / Iterator unaffected by later slot writes or Failed.
        """
        return self.flatten(access_order=access_order).map(iter)

    def flatten(
        self, *, access_order: StorageOrder = StorageOrder.ROW_MAJOR
    ) -> BindingResult[list[T]]:
        """返回独立列表，保持每个元素身份 / Return an independent list retaining each element identity.

        Args:
            access_order: 输出遍历顺序 / Output traversal order.

        Returns:
            独立列表或 Failed / Detached list or Failed.
        """
        if not isinstance(access_order, StorageOrder):
            return invalid("无效访问顺序 / Invalid access order")
        return cast(
            "BindingResult[list[T]]",
            invoke(
                lambda: self._handle.flatten(access_order is StorageOrder.COLUMN_MAJOR)
            ),
        )

    def to_storage_order(self, storage_order: StorageOrder) -> BindingResult[Self]:
        """转换布局，保持坐标与元素身份 / Convert layout preserving coordinates and identity.

        Args:
            storage_order: 目标布局 / Target layout.

        Returns:
            独立容器或 Failed / Independent container or Failed.
        """
        if not isinstance(storage_order, StorageOrder):
            return invalid("无效存储顺序 / Invalid storage order")
        return invoke(
            lambda: self._handle.to_storage_order(
                storage_order is StorageOrder.COLUMN_MAJOR
            )
        ).map(type(self))

    def reshape(self, shape: Shape | ShapeProtocol) -> BindingResult[Self]:
        """保持元素数与存储顺序进行重塑 / Reshape preserving element count and storage order.

        Args:
            shape: 同元素数、同顺序的形状 / Shape with the same count and storage order.

        Returns:
            独立容器或 Failed / Independent container or Failed.
        """
        if not isinstance(shape, Shape):
            snapshot = Shape.from_shape(shape)
            if isinstance(snapshot, Failed):
                return Failed(snapshot.error)
            shape = snapshot.unwrap()
        native_shape = shape._handle
        return invoke(lambda: self._handle.reshape(native_shape)).map(type(self))

    def view(
        self,
        *,
        offsets: tuple[int, ...] | None = None,
        shape: Shape | ShapeProtocol | None = None,
    ) -> BindingResult[MultiArrayView[T]]:
        """创建持有源所有权的矩形只读视图 / Create a rectangular read-only view retaining its source.

        Args:
            offsets: 每轴非负起点，None 为全零 / Nonnegative starts, with None meaning all zeros.
            shape: 同维数同顺序的正轴形状；None 由 Rust 推导剩余范围 / Same-rank/order positive shape; None derives remaining extents in Rust.

        Returns:
            无元素副本的视图或 Failed / View without element copies or Failed.
        """
        return _region(source=self.shape, offsets=offsets, shape=shape).map(
            lambda region: MultiArrayView(self, region)
        )

    def transpose(self) -> BindingResult[MultiArray[T]]:
        """反转轴并翻转存储顺序为独立快照 / Reverse axes and storage order into an independent snapshot.

        Returns:
            保持元素身份的不可变容器或 Failed / Immutable container retaining element identity or Failed.
        """
        return invoke(self._handle.transpose).map(MultiArray)

    def map[U](
        self,
        callback: MapCallback[T, U],
        *,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[MultiArray[U]]:
        """在 Rust 快照上执行回调，保持坐标和形状 / Map a Rust snapshot preserving coordinates and shape.

        Args:
            callback: 普通值或 Ok 成功；Failed/Fatal/Warn 停止 / Plain values or Ok succeed; Failed/Fatal/Warn stop.
            access_order: 回调调用顺序 / Callback invocation order.

        Returns:
            完整不可变输出或保留来源的 Failed / Complete immutable output or Failed retaining provenance.
        """
        return _mapped(
            handle=self._handle,
            callback=callback,
            flat=False,
            access_order=access_order,
        )

    def flat_map[U](
        self,
        callback: FlatMapCallback[T, U],
        *,
        shape: Shape | ShapeProtocol,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[MultiArray[U]]:
        """拼接回调 iterable 并严格校验输出形状 / Concatenate callback iterables and strictly validate output shape.

        Args:
            callback: 返回 iterable 或 Ok(iterable) / Return an iterable or Ok(iterable).
            shape: 元素数恰好匹配的显式输出形状 / Explicit output shape with an exactly matching count.
            access_order: 输入调用及输出赋值的坐标顺序 / Coordinate order for input callbacks and output assignment.

        Returns:
            完整不可变输出或 Failed，不发布部分输出 / Complete immutable output or Failed, never partial output.
        """
        return _mapped(
            handle=self._handle,
            callback=callback,
            flat=True,
            shape=shape,
            access_order=access_order,
        )


@dataclass(frozen=True, slots=True, eq=False)
class MutableMultiArray[T]:
    """单一 Rust 存储的可变容器 / Mutable container with one Rust storage authority.

    元素保留身份，写入不回传构造用 list/ndarray。
    Elements retain identity; writes do not propagate into input lists/ndarrays.
    """

    _handle: _native.MutableMultiArray

    __getstate__ = _object_state
    __setstate__ = _restore_object_state

    def describe(
        self, *, formatter: object = repr, max_items: int = 20, max_chars: int = 4096
    ) -> BindingResult[str]:
        """快照逻辑前缀后解锁格式化 / Snapshot a logical prefix and unlock before formatting.

        Args:
            formatter: 字符串格式器，可返回 Result / String formatter optionally returning Result.
            max_items: 最多显示的叶数 / Maximum leaves displayed.
            max_chars: 全部输出的字符上限，至少为 3 / Character limit for the entire output, at least 3.

        Returns:
            有界描述或 Failed；不回滚格式器写入 / Bounded description or Failed; formatter writes are not rolled back.
        """
        return _described(
            handle=self._handle,
            formatter=formatter,
            max_items=max_items,
            max_chars=max_chars,
        )

    def equals(self, other: object, *, comparator: object = eq) -> BindingResult[bool]:
        """比较双方槽位快照，回调不持源锁 / Compare operand slot snapshots without holding source locks during callbacks.

        Args:
            other: Rust 引用数组或矩形视图 / Rust reference array or rectangular view.
            comparator: 返回受检布尔结果的二元比较器 / Binary comparator returning a checked boolean result.

        Returns:
            bool 或 Failed；同源双方在一次锁内快照 / Bool or Failed; same-source operands snapshot under one lock.
        """
        return _equals(source=self, other=other, comparator=comparator)

    @classmethod
    def from_list(
        cls, *, data: object, shape: Shape | ShapeProtocol
    ) -> BindingResult[Self]:
        """从严格嵌套结构创建独立可变存储 / Create independent mutable storage from strict nested structure.

        Args:
            data: 各结构轴为内置 list/tuple，叶不转换 / Structural axes are built-in list/tuple; leaves are not coerced.
            shape: 明确规定结构深度及各轴长度 / Explicit structural depth and axis lengths.

        Returns:
            单一 Rust 容器或 Failed，不写回输入 / Single Rust container or Failed, without input write-back.
        """
        if not isinstance(shape, Shape):
            snapshot = Shape.from_shape(shape)
            if isinstance(snapshot, Failed):
                return Failed(snapshot.error)
            shape = snapshot.unwrap()
        native_shape = shape._handle
        return invoke(
            lambda: _native._mutable_multiarray_from_nested(
                data=data, shape=native_shape
            )
        ).map(cls)

    def to_snapshot(self) -> BindingResult[dict[str, Any]]:
        """导出可变数组的完整引用快照 / Export a complete reference snapshot of mutable storage.

        Returns:
            与槽位后续写入独立的版本化 DTO 或 Failed / Versioned DTO independent of later slot writes, or Failed.
        """
        return _reference_snapshot(self._handle, "mutable")

    @classmethod
    def from_snapshot(cls, payload: object) -> BindingResult[Self]:
        """受检恢复单一可变 Rust 存储 / Restore checked single-authority mutable Rust storage.

        Args:
            payload: kind=mutable 的版本化内置 dict / Versioned built-in dict with mutable kind.

        Returns:
            完整新容器或 Failed，不保留 DTO 的 values list / Complete new storage or Failed, without retaining the DTO values list.
        """
        return _snapshot_input(payload, "mutable").flat_map(
            lambda parts: cls.create(
                values=parts[0], shape=parts[1], access_order=parts[2]
            )
        )

    @classmethod
    def from_legacy_state(
        cls, *, payload: object, copy: bool, standard_layout: bool = False
    ) -> BindingResult[Self]:
        """受检复制旧物理序列，不写回旧缓冲 / Copy a checked legacy physical sequence without writing back to its buffer.

        Args:
            payload: 仅含 _shape/_data 的内置 dict / Built-in dict containing only _shape/_data.
            copy: 显式 True；False 返回 NOT_SUPPORTED / Explicit True; False returns NOT_SUPPORTED.
            standard_layout: 自定义形状须显式确认标准映射 / Custom shapes require explicit standard-mapping confirmation.

        Returns:
            唯一新 Rust 可变存储或 Failed，不保留 ndarray / Single new mutable Rust storage or Failed, without retaining the ndarray.
        """
        return _legacy_input(
            payload=payload, copy=copy, standard_layout=standard_layout
        ).flat_map(
            lambda parts: cls.create(
                values=parts[0], shape=parts[1], access_order=parts[1].storage_order
            )
        )

    @classmethod
    def full(cls, *, shape: Shape | ShapeProtocol, value: T) -> BindingResult[Self]:
        """由 Rust 原子填充可变槽位，不复制叶对象 / Atomically fill mutable Rust slots without copying leaf objects.

        Args:
            shape: Rust 或内置公开形状 / Rust or built-in public shape.
            value: 每个槽位共享的原对象 / Original object shared by every slot.

        Returns:
            独立可变容器或形状/容量失败 / Independent mutable container or shape/capacity failure.
        """
        if not isinstance(shape, Shape):
            snapshot = Shape.from_shape(shape)
            if isinstance(snapshot, Failed):
                return Failed(snapshot.error)
            shape = snapshot.unwrap()
        native_shape = shape._handle
        return invoke(
            lambda: _native._full_mutable_multiarray(shape=native_shape, value=value)
        ).map(cls)

    @staticmethod
    def zeros(
        *, shape: Shape | ShapeProtocol
    ) -> BindingResult[MutableMultiArray[float]]:
        """创建内置 float 全零可变数组 / Create a mutable array filled with built-in float zeros.

        Args:
            shape: Rust 或内置公开形状 / Rust or built-in public shape.

        Returns:
            全零基础可变容器或 Failed / Zero-filled base mutable container or Failed.
        """
        return MutableMultiArray[float].full(shape=shape, value=0.0)

    @staticmethod
    def ones(
        *, shape: Shape | ShapeProtocol
    ) -> BindingResult[MutableMultiArray[float]]:
        """创建内置 float 全一可变数组 / Create a mutable array filled with built-in float ones.

        Args:
            shape: Rust 或内置公开形状 / Rust or built-in public shape.

        Returns:
            全一基础可变容器或 Failed / One-filled base mutable container or Failed.
        """
        return MutableMultiArray[float].full(shape=shape, value=1.0)

    @classmethod
    def create(
        cls,
        *,
        values: list[T],
        shape: Shape | ShapeProtocol,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[Self]:
        """原子创建可变 Rust 存储 / Atomically create mutable Rust storage.

        Args:
            values: 内置 list，元素保留身份 / Built-in list with identity-preserving entries.
            shape: Rust 或内置公开形状 / Rust or built-in public shape.
            access_order: 输入遍历顺序 / Input traversal order.

        Returns:
            独立容器或 Failed / Independent container or Failed.
        """
        if type(values) is not list or not isinstance(access_order, StorageOrder):
            return invalid(
                "需要内置 list 和访问顺序 / Built-in list and access order required"
            )
        if not isinstance(shape, Shape):
            snapshot = Shape.from_shape(shape)
            if isinstance(snapshot, Failed):
                return Failed(snapshot.error)
            shape = snapshot.unwrap()
        native_shape = shape._handle
        return invoke(
            lambda: _native._create_mutable_multiarray(
                values=values,
                shape=native_shape,
                column_major=access_order is StorageOrder.COLUMN_MAJOR,
            )
        ).map(cls)

    @classmethod
    def from_numpy(
        cls,
        *,
        values: object,
        copy: bool,
        storage_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[Self]:
        """从显式 NumPy 快照创建可写容器 / Create writable storage from an explicit NumPy snapshot.

        Args:
            values: 内置 ndarray；允许只读源 / Built-in ndarray; read-only sources allowed.
            copy: 显式快照为 True；共享 False 不支持 / Explicit snapshot True; shared False unsupported.
            storage_order: Rust 存储顺序 / Rust storage order.

        Returns:
            不修改源的可变容器或 Failed / Mutable container not modifying the source, or Failed.
        """
        return _numpy_snapshot(
            values=values, copy=copy, storage_order=storage_order
        ).flat_map(lambda snapshot: cls.create(values=snapshot[0], shape=snapshot[1]))

    @property
    def shape(self) -> Shape:
        """返回独立形状 / Return a detached shape."""
        return Shape(self._handle.shape)

    def __len__(self) -> int:
        return self._handle.shape.size

    def at(self, indices: tuple[int, ...]) -> BindingResult[T]:
        """读取原元素 / Read the original element.

        Args:
            indices: 完整非负坐标 / Complete nonnegative coordinates.

        Returns:
            元素或 Failed / Element or Failed.
        """
        if not _integer_tuple(indices):
            return invalid("索引必须为整数 tuple / Indices must be an integer tuple")
        return cast("BindingResult[T]", invoke(lambda: self._handle.at(list(indices))))

    def to_list(self) -> BindingResult[T | list[Any]]:
        """按逻辑行坐标构建嵌套 list，标量返回原元素 / Build nested lists in logical row order; a scalar returns its element.

        Returns:
            独立容器结构或 Failed，元素身份不变 / Independent container structure or Failed, preserving element identity.
        """
        return invoke(self._handle.to_list)

    def reduce(
        self,
        callback: ReduceCallback[T],
        *,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[T]:
        """在完整 Rust 槽位快照上左结合归约 / Left-fold a complete Rust slot snapshot.

        Args:
            callback: 二元函数，可返回普通值或单层 Result / Binary function returning a value or one Result layer.
            access_order: 坐标遍历顺序，与存储布局独立 / Coordinate traversal order independent of storage layout.

        Returns:
            完整归约值或 Failed；单元素不执行函数 / Complete fold value or Failed; singleton input skips the function.
        """
        return _reduced(
            handle=self._handle,
            callback=callback,
            access_order=access_order,
        )

    def iter_live(
        self, *, access_order: StorageOrder | None = None
    ) -> BindingResult[MultiArrayIterator[T]]:
        """创建非快照游标，槽位在每次消费时读取 / Create a non-snapshot cursor reading slots on each consumption.

        Args:
            access_order: None 沿用物理顺序；显式行/列顺序与布局独立 / None follows physical order; explicit row/column order is independent of layout.

        Returns:
            保活源的单一游标或 Failed，不承诺跨调用事务 / Single cursor retaining its source or Failed, without a cross-call transaction.
        """
        return _live_iterator(
            owner=self, handle=self._handle, access_order=access_order
        )

    def iter_snapshot(
        self, *, access_order: StorageOrder = StorageOrder.ROW_MAJOR
    ) -> BindingResult[Iterator[T]]:
        """一次受检快照后返回标准迭代器 / Return a standard iterator after one checked snapshot.

        Args:
            access_order: 坐标遍历顺序 / Coordinate traversal order.

        Returns:
            不观察后续槽位写入的迭代器或 Failed / Iterator unaffected by later slot writes or Failed.
        """
        return self.flatten(access_order=access_order).map(iter)

    def flatten(
        self, *, access_order: StorageOrder = StorageOrder.ROW_MAJOR
    ) -> BindingResult[list[T]]:
        """按指定顺序快照元素引用 / Snapshot element references in the specified order.

        Args:
            access_order: 输出遍历顺序 / Output traversal order.

        Returns:
            独立列表或 Failed / Independent list or Failed.
        """
        if not isinstance(access_order, StorageOrder):
            return invalid("无效访问顺序 / Invalid access order")
        return cast(
            "BindingResult[list[T]]",
            invoke(
                lambda: self._handle.flatten(access_order is StorageOrder.COLUMN_MAJOR)
            ),
        )

    def set(self, *, indices: tuple[int, ...], value: T) -> BindingResult[None]:
        """受检替换一个元素 / Replace one checked element.

        Args:
            indices: 完整非负坐标 / Complete nonnegative coordinates.
            value: 新元素，保留身份 / New element, retained by identity.

        Returns:
            成功或 Failed / Success or Failed.
        """
        return self.set_many([(indices, value)])

    def set_many(self, updates: list[tuple[tuple[int, ...], T]]) -> BindingResult[None]:
        """原子写入互不重复的坐标批次 / Atomically write a batch of distinct coordinates.

        Args:
            updates: 坐标/元素 list；任何无效项均不写入 / Coordinate/value list; invalid entries cause no writes.

        Returns:
            成功或 Failed；解锁后才释放旧元素 / Success or Failed; old elements released only after unlocking.
        """
        if not _updates(updates):
            return invalid(
                "需要坐标和元素的内置 list / Built-in list of coordinates and values required"
            )
        return invoke(lambda: self._handle.set_many([(list(i), v) for i, v in updates]))

    def to_immutable(self) -> BindingResult[MultiArray[T]]:
        """复制容器而非元素为只读快照 / Copy the container, not elements, into a read-only snapshot.

        Returns:
            独立不可变容器或 Failed / Independent immutable container or Failed.
        """
        return invoke(self._handle.to_immutable).map(MultiArray)

    def view(
        self,
        *,
        offsets: tuple[int, ...] | None = None,
        shape: Shape | ShapeProtocol | None = None,
    ) -> BindingResult[MutableMultiArrayView[T]]:
        """创建写入回传同一 Rust 存储的视图 / Create a view writing through to the same Rust storage.

        Args:
            offsets: 每轴起点，None 为全零 / Starts on each axis, with None meaning all zeros.
            shape: 同维数同顺序的形状；None 由 Rust 推导剩余范围 / Same-rank/order shape; None derives remaining extents in Rust.

        Returns:
            共享源存储的视图或 Failed / View sharing source storage or Failed.
        """
        return _region(source=self.shape, offsets=offsets, shape=shape).map(
            lambda region: MutableMultiArrayView(self, region)
        )

    def transpose(self) -> BindingResult[MultiArray[T]]:
        """反转轴与布局为独立不可变快照 / Reverse axes and layout into an independent immutable snapshot.

        Returns:
            独立容器或 Failed / Independent container or Failed.
        """
        return invoke(self._handle.transpose).map(MultiArray)

    def map[U](
        self,
        callback: MapCallback[T, U],
        *,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[MultiArray[U]]:
        """快照引用并解锁后映射 / Snapshot references and unlock before mapping.

        Args:
            callback: 普通值或现有 Result 回调 / Callback returning a plain value or existing Result.
            access_order: 输入回调顺序 / Input callback order.

        Returns:
            独立不可变输出或 Failed；不回滚回调主动写入 / Independent immutable output or Failed; explicit callback writes are not rolled back.
        """
        return _mapped(
            handle=self._handle,
            callback=callback,
            flat=False,
            access_order=access_order,
        )

    def flat_map[U](
        self,
        callback: FlatMapCallback[T, U],
        *,
        shape: Shape | ShapeProtocol,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[MultiArray[U]]:
        """对一致槽位快照执行扁平映射 / Flat-map a consistent slot snapshot.

        Args:
            callback: 返回 iterable 或现有 Result / Return an iterable or existing Result.
            shape: 显式输出形状 / Explicit output shape.
            access_order: 输入回调及输出赋值顺序 / Order for input callbacks and output assignment.

        Returns:
            完整不可变输出或 Failed / Complete immutable output or Failed.
        """
        return _mapped(
            handle=self._handle,
            callback=callback,
            flat=True,
            shape=shape,
            access_order=access_order,
        )


@dataclass(frozen=True, slots=True, eq=False)
class MultiArrayView[T]:
    """持有源门面与 Rust 区域元数据的只读视图 / Read-only view retaining its source facade and Rust region metadata.

    不拥有第二份元素缓冲，源的可变写入立即可见。
    No second element buffer; mutable source writes are immediately visible.
    """

    _source: MultiArray[T] | MutableMultiArray[T]
    _handle: _native.MultiArrayView

    __getstate__ = _object_state
    __setstate__ = _restore_object_state

    @staticmethod
    def from_legacy_state(
        *, payload: object, copy: bool, standard_layout: bool = False
    ) -> BindingResult[MultiArrayView[Any]]:
        """显式复制旧视图的源字段并修正剩余范围 / Explicitly copy legacy view source fields and correct remaining extents.

        Args:
            payload: 仅含 _source/_offsets 的内置 dict，源须为内置公开数组 / Built-in dict with only _source/_offsets and a built-in public array source.
            copy: 必须显式为 True，不保留旧缓冲共享 / Must explicitly be True; legacy buffer sharing is not retained.
            standard_layout: 自定义形状须显式确认标准映射 / Custom shapes require explicit standard-mapping confirmation.

        Returns:
            独立源快照上的只读基础视图或 Failed，不重定位对象图 / Base read-only view over a detached source snapshot or Failed, without graph relocation.
        """
        from ospf_python.multiarray.multi_array import MultiArray as PublicArray
        from ospf_python.multiarray.multi_array import (
            MutableMultiArray as PublicMutableArray,
        )

        if not isinstance(copy, bool):
            return invalid("copy 必须为 bool / copy must be bool")
        if not copy:
            return unsupported(
                "旧视图导入不保留共享缓冲 / Legacy view import does not preserve shared buffers"
            )
        if (
            type(payload) is not dict
            or not all(type(key) is str for key in payload)
            or set(payload) != {"_source", "_offsets"}
            or type(payload["_source"]) not in (PublicArray, PublicMutableArray)
            or not _integer_tuple(payload["_offsets"])
        ):
            return invalid(
                "需要内置数组源及旧 _source/_offsets 字段 / Built-in array source and legacy _source/_offsets fields are required"
            )
        offsets = payload["_offsets"]
        return MultiArray.from_legacy_state(
            payload=vars(payload["_source"]),
            copy=True,
            standard_layout=standard_layout,
        ).flat_map(lambda source: source.view(offsets=offsets))

    def describe(
        self, *, formatter: object = repr, max_items: int = 20, max_chars: int = 4096
    ) -> BindingResult[str]:
        """受检描述视图区域和 offset / Describe a checked view region and its offset.

        Args:
            formatter: 字符串格式器，可返回 Result / String formatter optionally returning Result.
            max_items: 最多显示的区域内逻辑叶数 / Maximum logical leaves displayed within the region.
            max_chars: 全部输出的字符上限，至少为 3 / Character limit for the entire output, at least 3.

        Returns:
            有界描述或 Failed，不隐式物化 / Bounded description or Failed, without implicit materialization.
        """
        return _described(
            handle=self._source._handle,
            region=self._handle,
            formatter=formatter,
            max_items=max_items,
            max_chars=max_chars,
        )

    def equals(self, other: object, *, comparator: object = eq) -> BindingResult[bool]:
        """受检比较视图的逻辑区域，保留 offset / Compare checked logical view regions, preserving offsets.

        Args:
            other: Rust 引用数组或矩形视图 / Rust reference array or rectangular view.
            comparator: 二元布尔比较器，允许返回 Result / Binary boolean comparator, optionally returning Result.

        Returns:
            相等与否或 Failed，不执行惰性物化 / Equality or Failed, without implicit lazy materialization.
        """
        return _equals(source=self, other=other, comparator=comparator)

    @property
    def shape(self) -> Shape:
        """返回视图自身形状而非源形状 / Return the view's shape rather than the source shape."""
        return Shape(self._handle.shape)

    def __len__(self) -> int:
        return self._handle.shape.size

    def at(self, indices: tuple[int, ...]) -> BindingResult[T]:
        """读取经受检偏移映射的元素 / Read an element through checked offset projection.

        Args:
            indices: 视图内完整坐标 / Complete coordinates within the view.

        Returns:
            原元素或 Failed / Original element or Failed.
        """
        if not _integer_tuple(indices):
            return invalid("索引必须为整数 tuple / Indices must be an integer tuple")
        return cast(
            "BindingResult[T]",
            invoke(lambda: self._source._handle.region_at(self._handle, list(indices))),
        )

    def to_list(self) -> BindingResult[T | list[Any]]:
        """按逻辑行坐标构建嵌套 list，标量返回原元素 / Build nested lists in logical row order; a scalar returns its element.

        Returns:
            独立容器结构或 Failed，元素身份不变 / Independent container structure or Failed, preserving element identity.
        """
        return invoke(lambda: self._source._handle.to_list(region=self._handle))

    def reduce(
        self,
        callback: ReduceCallback[T],
        *,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[T]:
        """在完整 Rust 槽位快照上左结合归约 / Left-fold a complete Rust slot snapshot.

        Args:
            callback: 二元函数，可返回普通值或单层 Result / Binary function returning a value or one Result layer.
            access_order: 坐标遍历顺序，与存储布局独立 / Coordinate traversal order independent of storage layout.

        Returns:
            完整归约值或 Failed；单元素不执行函数 / Complete fold value or Failed; singleton input skips the function.
        """
        return _reduced(
            handle=self._source._handle,
            callback=callback,
            access_order=access_order,
            region=self._handle,
        )

    def iter_live(
        self, *, access_order: StorageOrder | None = None
    ) -> BindingResult[MultiArrayIterator[T]]:
        """在受检区域内逐次读取，不物化源 / Read per advance inside the checked region without materializing the source.

        Args:
            access_order: None 为区域的存储顺序；否则显式坐标顺序 / None for the region's storage order, otherwise explicit coordinate order.

        Returns:
            保活视图和源的游标或 Failed / Cursor retaining the view and source, or Failed.
        """
        return _live_iterator(
            owner=self,
            handle=self._source._handle,
            region=self._handle,
            access_order=access_order,
        )

    def iter_snapshot(
        self, *, access_order: StorageOrder = StorageOrder.ROW_MAJOR
    ) -> BindingResult[Iterator[T]]:
        """一次受检快照后返回标准迭代器 / Return a standard iterator after one checked snapshot.

        Args:
            access_order: 坐标遍历顺序 / Coordinate traversal order.

        Returns:
            不观察后续槽位写入的迭代器或 Failed / Iterator unaffected by later slot writes or Failed.
        """
        return self.flatten(access_order=access_order).map(iter)

    def flatten(
        self, *, access_order: StorageOrder = StorageOrder.ROW_MAJOR
    ) -> BindingResult[list[T]]:
        """通过 Rust 视图遍历独立快照 / Take an independent snapshot using Rust view traversal.

        Args:
            access_order: 输出遍历顺序 / Output traversal order.

        Returns:
            保留元素身份的列表或 Failed / List retaining element identity or Failed.
        """
        if not isinstance(access_order, StorageOrder):
            return invalid("无效访问顺序 / Invalid access order")
        return cast(
            "BindingResult[list[T]]",
            invoke(
                lambda: self._source._handle.region_flatten(
                    self._handle, access_order is StorageOrder.COLUMN_MAJOR
                )
            ),
        )

    def materialize(self) -> BindingResult[MultiArray[T]]:
        """正确应用 offset 后物化独立容器 / Materialize an independent container with offsets applied.

        Returns:
            独立不可变 Rust 数组或 Failed / Independent immutable Rust array or Failed.
        """
        return invoke(
            lambda: self._source._handle.region_materialize(self._handle)
        ).map(MultiArray)

    def transpose(self) -> BindingResult[MultiArray[T]]:
        """应用 offset 后反转区域轴和布局 / Apply offsets, then reverse region axes and layout.

        Returns:
            独立不可变容器或 Failed / Independent immutable container or Failed.
        """
        return invoke(lambda: self._source._handle.region_transpose(self._handle)).map(
            MultiArray
        )

    def map[U](
        self,
        callback: MapCallback[T, U],
        *,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[MultiArray[U]]:
        """对区域快照映射，锁内不调用 Python / Map a region snapshot without Python calls under the source lock.

        Args:
            callback: 元素回调 / Element callback.
            access_order: 区域回调顺序 / Region callback order.

        Returns:
            完整不可变输出或 Failed / Complete immutable output or Failed.
        """
        return _mapped(
            handle=self._source._handle,
            region=self._handle,
            callback=callback,
            flat=False,
            access_order=access_order,
        )

    def flat_map[U](
        self,
        callback: FlatMapCallback[T, U],
        *,
        shape: Shape | ShapeProtocol,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[MultiArray[U]]:
        """对区域快照进行指定形状的扁平映射 / Flat-map a region snapshot to an explicit shape.

        Args:
            callback: 返回 iterable 或现有 Result / Return an iterable or existing Result.
            shape: 显式输出形状 / Explicit output shape.
            access_order: 输入区域和输出赋值的坐标顺序 / Coordinate order for the input region and output assignment.

        Returns:
            完整不可变输出或 Failed / Complete immutable output or Failed.
        """
        return _mapped(
            handle=self._source._handle,
            region=self._handle,
            callback=callback,
            flat=True,
            shape=shape,
            access_order=access_order,
        )

    def view(
        self,
        *,
        offsets: tuple[int, ...] | None = None,
        shape: Shape | ShapeProtocol | None = None,
    ) -> BindingResult[Self]:
        """在 Rust 中组合偏移，保留最终源 / Compose offsets in Rust and retain the ultimate source.

        Args:
            offsets: 相对当前视图的偏移，None 为全零 / Offsets relative to this view, with None meaning all zeros.
            shape: 子区域形状；None 为当前区域内的剩余范围 / Subregion shape; None means remaining extents within the current region.

        Returns:
            同类型子视图或 Failed / Subview of the same type or Failed.
        """
        if offsets is not None and not _integer_tuple(offsets):
            return invalid("偏移必须为整数 tuple / Offsets must be an integer tuple")
        if shape is not None and not isinstance(shape, Shape):
            snapshot = Shape.from_shape(shape)
            if isinstance(snapshot, Failed):
                return Failed(snapshot.error)
            shape = snapshot.unwrap()
        native_shape = None if shape is None else shape._handle
        return invoke(
            lambda: self._handle.subview(
                None if offsets is None else list(offsets), native_shape
            )
        ).map(lambda region: type(self)(self._source, region))


@dataclass(frozen=True, slots=True, eq=False)
class MutableMultiArrayView[T](MultiArrayView[T]):
    """写入与源共享同一 Rust 存储的视图 / View writing to the source's single Rust storage."""

    _source: MutableMultiArray[T]

    __getstate__ = _object_state
    __setstate__ = _restore_object_state

    def set(self, *, indices: tuple[int, ...], value: T) -> BindingResult[None]:
        """经 offset 映射写入一个元素 / Write one element through offset projection.

        Args:
            indices: 视图内完整坐标 / Complete view coordinates.
            value: 原样保留的新元素 / New element retained as-is.

        Returns:
            成功或 Failed / Success or Failed.
        """
        return self.set_many([(indices, value)])

    def set_many(self, updates: list[tuple[tuple[int, ...], T]]) -> BindingResult[None]:
        """在源存储中原子写入视图坐标批次 / Atomically write view coordinates into source storage.

        Args:
            updates: 互不重复的视图坐标/元素 list / List of distinct view coordinates and elements.

        Returns:
            成功或 Failed，失败不部分写入 / Success or Failed, without partial writes on failure.
        """
        if not _updates(updates):
            return invalid(
                "需要坐标和元素的内置 list / Built-in list of coordinates and values required"
            )
        return invoke(
            lambda: self._source._handle.region_set_many(
                self._handle, [(list(i), v) for i, v in updates]
            )
        )


@dataclass(frozen=True, slots=True, eq=False)
class MappedMultiArrayView[T]:
    """保留源更新的惰性元素映射，不缓存输出 / Lazy element mapping retaining live source updates, without output caching.

    使用 create 构造；每次 at 重新读取槽位并调用全部函数，materialize 使用一次 Rust 槽位快照。
    Use create; at re-reads one slot and applies every callback, while materialize uses one Rust slot snapshot.
    这不是 Rust 的轴映射视图，也不改变现有 view.map 的 eager 语义。
    This is not a Rust axis-mapping view and does not change existing eager view.map semantics.
    """

    _source: MultiArray[Any] | MutableMultiArray[Any] | MultiArrayView[Any]
    _callbacks: tuple[MapCallback[Any, Any], ...]

    __getstate__ = _object_state
    __setstate__ = _restore_object_state

    @staticmethod
    def create[S, U](
        *,
        source: MultiArray[S]
        | MutableMultiArray[S]
        | MultiArrayView[S]
        | MappedMultiArrayView[S],
        callback: MapCallback[S, U],
    ) -> BindingResult[MappedMultiArrayView[U]]:
        """保活源和函数而不执行回调或复制元素 / Retain source and functions without invoking callbacks or copying elements.

        Args:
            source: Rust 通用数组、矩形视图或惰性映射 / Rust object array, rectangular view or lazy mapping.
            callback: 访问时执行的元素函数 / Element callback evaluated on access.

        Returns:
            惰性视图或受检输入失败 / Lazy view or checked input failure.
        """
        if not callable(callback):
            return invalid("映射回调必须可调用 / Mapping callback must be callable")
        if isinstance(source, MappedMultiArrayView):
            return Ok(
                MappedMultiArrayView(source._source, (*source._callbacks, callback))
            )
        if not isinstance(source, (MultiArray, MutableMultiArray, MultiArrayView)):
            return invalid("需要原生数组或视图 / Native array or view required")
        return Ok(MappedMultiArrayView(source, (callback,)))

    @property
    def shape(self) -> Shape:
        """读取最终源的形状而不执行回调 / Read the ultimate source shape without invoking callbacks."""
        return self._source.shape

    def __len__(self) -> int:
        return len(self._source)

    def _native_source(
        self,
    ) -> tuple[
        _native.MultiArray | _native.MutableMultiArray, _native.MultiArrayView | None
    ]:
        source = self._source
        if isinstance(source, MultiArrayView):
            return source._source._handle, source._handle
        return source._handle, None

    def at(self, indices: tuple[int, ...]) -> BindingResult[T]:
        """在单次原生调用中受检读取并惰性映射 / Checked read and lazy mapping in one native call.

        Args:
            indices: 视图内完整非负坐标 / Complete nonnegative coordinates within the view.

        Returns:
            当前映射值或保留原始回调失败的 Failed / Current mapped value or Failed retaining the original callback failure.
        """
        if not _integer_tuple(indices):
            return invalid("索引必须为整数 tuple / Indices must be an integer tuple")
        handle, region = self._native_source()
        return map_callbacks(
            callbacks=self._callbacks,
            flat=False,
            operation=lambda adapted: handle.mapped_at(
                indices=list(indices), callback=adapted, region=region
            ),
        )

    def materialize(
        self, *, access_order: StorageOrder = StorageOrder.ROW_MAJOR
    ) -> BindingResult[MultiArray[T]]:
        """快照源槽位后批量映射并原子发布独立数组 / Snapshot source slots, batch-map and atomically publish an independent array.

        Args:
            access_order: 元素回调顺序，不改变输出坐标和布局 / Callback order, without changing output coordinates or layout.

        Returns:
            独立不可变数组或 Failed / Independent immutable array or Failed.
        """
        if not isinstance(access_order, StorageOrder):
            return invalid("无效访问顺序 / Invalid access order")
        handle, region = self._native_source()
        column_major = access_order is StorageOrder.COLUMN_MAJOR
        if region is None:
            return map_callbacks(
                callbacks=self._callbacks,
                flat=False,
                operation=lambda adapted: handle.mapped(
                    callback=adapted, column_major=column_major
                ),
            ).map(MultiArray)
        return map_callbacks(
            callbacks=self._callbacks,
            flat=False,
            operation=lambda adapted: handle.region_mapped(
                region=region, callback=adapted, column_major=column_major
            ),
        ).map(MultiArray)


@dataclass(frozen=True, slots=True, eq=False)
class RationalMultiArray:
    """单个不可变 Rust 精确多维数组 / One immutable Rust exact multiarray.

    不保存 NumPy 或 Python 元素镜像；构造、展平与重塑均为独立所有权快照。
    No NumPy/Python element mirror; construction, flatten and reshape own independent snapshots.
    """

    _handle: _native.RationalMultiArray

    @classmethod
    def create(
        cls,
        *,
        values: RationalArray,
        shape: Shape | ShapeProtocol,
        access_order: StorageOrder = StorageOrder.ROW_MAJOR,
    ) -> BindingResult[RationalMultiArray]:
        """从精确批次按访问顺序创建 / Create from an exact batch in the given access order.

        Args:
            values: 不经浮点或逐项 Python 包装的精确批次 / Exact batch, without floats or per-item Python wrappers.
            shape: Rust 形状或公开 Shape 协议的受检快照 / Rust shape or checked snapshot of a public Shape protocol.
            access_order: 输入列表的坐标遍历顺序，不是存储布局 / Input coordinate traversal, not storage layout.

        Returns:
            Rust 多维数组或 Failed / Rust multiarray or Failed.
        """
        if not isinstance(values, RationalArray) or not isinstance(
            access_order, StorageOrder
        ):
            return invalid(
                "需要精确批次、形状和访问顺序 / Exact batch, shape and access order required"
            )
        if not isinstance(shape, Shape):
            snapshot = Shape.from_shape(shape)
            if isinstance(snapshot, Failed):
                return Failed(snapshot.error)
            shape = snapshot.unwrap()
        native_shape = shape._handle
        return invoke(
            lambda: _native._create_rational_multiarray(
                values=values._handle,
                shape=native_shape,
                column_major=access_order is StorageOrder.COLUMN_MAJOR,
            )
        ).map(cls)

    @property
    def shape(self) -> Shape:
        """返回独立形状快照 / Return a detached shape snapshot."""
        return Shape(self._handle.shape)

    def __len__(self) -> int:
        return self._handle.shape.size

    def at(self, indices: tuple[int, ...]) -> BindingResult[Rational]:
        """读取独立精确元素 / Read a detached exact element.

        Args:
            indices: 完整非负整数坐标 / Complete nonnegative integer coordinates.

        Returns:
            独立 Rust 有理数或 Failed / Independent Rust rational or Failed.
        """
        if not _integer_tuple(indices):
            return invalid("索引必须为整数 tuple / Indices must be an integer tuple")
        return invoke(lambda: self._handle.at(list(indices))).map(Rational)

    def flatten(
        self, *, access_order: StorageOrder = StorageOrder.ROW_MAJOR
    ) -> BindingResult[RationalArray]:
        """按显式访问顺序返回独立批次 / Return an independent batch in explicit access order.

        Args:
            access_order: 坐标遍历顺序，与内部存储无关 / Coordinate traversal independent of storage.

        Returns:
            精确批次或 Failed / Exact batch or Failed.
        """
        if not isinstance(access_order, StorageOrder):
            return invalid("无效访问顺序 / Invalid access order")
        return invoke(
            lambda: (
                self._handle.flatten(access_order is StorageOrder.COLUMN_MAJOR),
                None,
            )
        ).map(RationalArray)

    def to_storage_order(
        self, storage_order: StorageOrder
    ) -> BindingResult[RationalMultiArray]:
        """转换内部布局但保持坐标值 / Convert storage layout preserving coordinate values.

        Args:
            storage_order: 目标存储顺序 / Target storage order.

        Returns:
            独立数组或 Failed / Independent array or Failed.
        """
        if not isinstance(storage_order, StorageOrder):
            return invalid("无效存储顺序 / Invalid storage order")
        return invoke(
            lambda: (
                self._handle.to_storage_order(
                    storage_order is StorageOrder.COLUMN_MAJOR
                ),
                None,
            )
        ).map(RationalMultiArray)

    def reshape(
        self, shape: Shape | ShapeProtocol
    ) -> BindingResult[RationalMultiArray]:
        """按相同存储顺序重塑，不截断或补值 / Reshape in the same storage order without truncation or padding.

        Args:
            shape: 同元素数、同存储顺序的 Rust 或内置公开形状 / Rust or built-in public shape with the same count and storage order.

        Returns:
            独立数组或 Failed / Independent array or Failed.
        """
        if not isinstance(shape, Shape):
            snapshot = Shape.from_shape(shape)
            if isinstance(snapshot, Failed):
                return Failed(snapshot.error)
            shape = snapshot.unwrap()
        native_shape = shape._handle
        return invoke(lambda: self._handle.reshape(native_shape)).map(
            RationalMultiArray
        )
