"""公开形状计算与外部数值协议 / Public shape arithmetic and external numeric protocols."""

from __future__ import annotations

import builtins
import gc
import itertools
import math
import sys
import weakref
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.multiarray.shape import (
    DynShape,
    Shape2,
    Shape3,
    Shape4,
    StorageOrder,
    _compute_flat_index,
    _compute_strides,
)


@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("dims", [(), (2,), (2, 3), (2, 3, 4), (2, 3, 4, 5)])
def test_dense_public_arithmetic_against_independent_numpy_oracle(
    order: StorageOrder, dims: tuple[int, ...]
) -> None:
    shape = DynShape(dims, order)
    assert shape.size == int(np.prod(dims))
    array = np.empty(
        dims, dtype=np.int8, order="C" if order is StorageOrder.ROW_MAJOR else "F"
    )
    assert shape.strides() == array.strides
    for indices in itertools.product(*(range(dim) for dim in dims)):
        expected = (
            int(
                np.ravel_multi_index(
                    indices, dims, order="C" if order is StorageOrder.ROW_MAJOR else "F"
                )
            )
            if dims
            else 0
        )
        assert shape.flat_index(*indices) == expected


@pytest.mark.parametrize("order", list(StorageOrder))
def test_sparse_arithmetic_remains_unbounded_and_legacy_index_is_permissive(
    order: StorageOrder,
) -> None:
    big = 1 << 200
    shape = DynShape((big, 3, 5), order)
    expected = (15, 5, 1) if order is StorageOrder.ROW_MAJOR else (1, big, big * 3)
    assert shape.size == big * 15 and shape.strides() == expected
    for indices in [(), (-1,), (big, 3, 5), (1, 2), (2, 3, 4, 5)]:
        assert shape.flat_index(*indices) == sum(
            stride * index for stride, index in zip(expected, indices, strict=False)
        )


@pytest.mark.parametrize(
    ("strides", "indices"),
    [
        ((1 << 80, -3), (1, 2)),
        ((-(1 << 127),), (1,)),
        (((1 << 127) - 1,), (1,)),
        ((1 << 126, 1 << 126), (1, 1)),
        ((-(1 << 127),), (-1,)),
        ((1 << 126, 1 << 126, -(1 << 126), -(1 << 126)), (1, 1, 1, 1)),
        ((1 << 200, -7), (1 << 100, -3)),
        ((2, 3, 1 << 200), (-1, 4)),
        ((2,), (-5, 1 << 200)),
        ((), (1 << 200,)),
        ((-(1 << 200), 1 << 200), (7, 7)),
        ((1 << 4096, -(1 << 4096)), (1 << 513, (1 << 513) - 1)),
        ((3, -(1 << 300), 1 << 299), (-7, 2, -4)),
    ],
)
def test_permissive_index_preserves_integer_boundaries(
    *, strides: tuple[int, ...], indices: tuple[int, ...]
) -> None:
    """宽松点积不截断整数 / Permissive dot products never truncate integers."""
    value = _compute_flat_index((), strides, indices)
    expected = sum(left * right for left, right in zip(strides, indices, strict=False))
    assert type(value) is int and value == expected


@pytest.mark.parametrize("storage", [Shape2, Shape3, Shape4])
@pytest.mark.parametrize("first", [0, -1, sys.maxsize, sys.maxsize + 1, 1 << 200])
def test_fixed_size_preserves_mutated_sparse_and_nondense_metadata(
    *, storage: type[Any], first: int
) -> None:
    """实时字段仍保留无限精度 / Live fields retain unbounded arithmetic."""
    rank = {Shape2: 2, Shape3: 3, Shape4: 4}[storage]
    shape = storage(*([2] * rank))
    vars(shape)["d0"] = first
    assert shape.size == first * (2 ** (rank - 1))


def test_fixed_size_reads_each_live_axis_once_in_order() -> None:
    """本次调用按序读取字段 / Read each live axis once in order."""
    events: list[str] = []

    class Owner:
        def __getattribute__(self, name: str) -> Any:
            if name in {"d0", "d1", "d2", "d3"}:
                events.append(name)
                return {"d0": 2, "d1": 3, "d2": 4, "d3": 5}[name]
            return super().__getattribute__(name)

    assert _native._shape_size(Owner(), 4) == 120
    assert events == ["d0", "d1", "d2", "d3"]


def test_dynamic_size_supports_large_rank_without_changing_the_result() -> None:
    """高维元数据仍按原值计算 / Preserve the value for high-rank metadata."""
    assert DynShape((1,) * 100_000).size == 1


@pytest.mark.parametrize(
    "dims",
    [
        (2, 3, 4, 5, 6),
        (2, 1, 3, 1, 4, 1, 5),
        (2, 1, 3, 1, 4, 1, 5, 1),
        (1, 2, 1, 3, 1, 4, 1, 5, 1),
        (1, 1, 1, 1, 1, sys.maxsize),
        (1, 1, 1, 1, sys.maxsize, 2, 0),
    ],
)
def test_dynamic_size_keeps_batch_boundaries_and_sparse_values(
    dims: tuple[int, ...],
) -> None:
    """分组仍精确保留整数结果 / Grouping preserves exact integer results."""
    shape = DynShape((1,) * len(dims))
    vars(shape)["dims"] = dims
    assert shape.size == math.prod(dims)


@pytest.mark.parametrize(
    "dims",
    [
        (-(1 << 256), -3, 7),
        (1 << 500, 1 << 750, -5),
        (sys.maxsize, 2, 0, 1 << 200),
        (0, -(1 << 500), 1 << 750),
    ],
)
def test_dynamic_size_keeps_exact_sparse_integer_products(
    dims: tuple[int, ...],
) -> None:
    """非稠密整数精确计算 / Non-dense integer products remain exact."""
    shape = DynShape((1,) * len(dims))
    vars(shape)["dims"] = dims
    result = shape.size
    assert type(result) is int and result == math.prod(dims)


@pytest.mark.parametrize("storage", [Shape2, Shape3, Shape4])
@pytest.mark.parametrize("implementation", ["legacy", "native"])
def test_fixed_size_preserves_first_operand_identity_and_left_association(
    storage: type[Any], implementation: str
) -> None:
    first = 1 << 100
    events: list[str] = []

    class Factor:
        def __le__(self, other: Any) -> bool:
            return False

        def __rmul__(self, other: Any) -> Any:
            assert other is first
            events.append("reflected")
            return self

        def __mul__(self, other: Any) -> Any:
            events.append("multiply")
            return self

    factor = Factor()
    rank = {Shape2: 2, Shape3: 3, Shape4: 4}[storage]
    shape = storage(first, factor, *([2] * (rank - 2)))
    if implementation == "native":
        value = shape.size
    else:
        value = shape.d0 * shape.d1
        if rank >= 3:
            value = value * shape.d2
        if rank >= 4:
            value = value * shape.d3
    assert value is factor and events == ["reflected"] + ["multiply"] * (rank - 2)


@pytest.mark.parametrize("implementation", ["legacy", "native"])
def test_dynamic_size_releases_sequence_before_consuming_independent_iterator(
    implementation: str,
) -> None:
    events: list[str] = []

    class Iterator:
        def __init__(self) -> None:
            self.values = iter((2, 3))

        def __iter__(self) -> Any:
            return self

        def __next__(self) -> int:
            assert events == ["iter", "release"]
            return next(self.values)

    class Sequence:
        def __iter__(self) -> Any:
            events.append("iter")
            return Iterator()

        def __del__(self) -> None:
            events.append("release")

    class Owner:
        @property
        def dims(self) -> Any:
            return Sequence()

    def legacy(owner: Any) -> Any:
        value = 1
        for dim in owner.dims:
            assert events == ["iter", "release"]
            value *= dim
        return value

    value = (
        _native._shape_size(Owner(), None)
        if implementation == "native"
        else legacy(Owner())
    )
    assert value == 6 and events == ["iter", "release"]


@pytest.mark.parametrize("implementation", ["legacy", "native"])
def test_dynamic_size_uses_inplace_protocol_not_plain_multiplication(
    implementation: str,
) -> None:
    events: list[str] = []

    class Value:
        def __rmul__(self, other: Any) -> Any:
            assert other == 1
            events.append("initial")
            return self

        def __imul__(self, other: Any) -> Any:
            assert other == 3
            events.append("inplace")
            return self

        def __mul__(self, other: Any) -> Any:
            pytest.fail(
                "不能替换原地数值协议 / Must not replace in-place numeric protocol"
            )

    item = Value()
    owner = SimpleNamespace(dims=(item, 3))
    if implementation == "native":
        result = _native._shape_size(owner, None)
    else:
        result = 1
        for dim in owner.dims:
            result *= dim
    assert cast("Any", result) is item and events == ["initial", "inplace"]


@pytest.mark.parametrize("implementation", ["legacy", "native"])
def test_dot_product_retains_generator_operands_through_accumulation(
    implementation: str,
) -> None:
    events: list[str] = []
    reference: Any = None

    class Term:
        def __radd__(self, other: Any) -> int:
            assert other == 0 and reference() is not None
            events.append("add")
            return 7

    class Stride:
        def __mul__(self, other: Any) -> Any:
            assert other == 1
            events.append("multiply")
            return Term()

        def __del__(self) -> None:
            events.append("release")

    class Operands:
        done = False

        def __iter__(self) -> Any:
            return self

        def __next__(self) -> Any:
            nonlocal reference
            if self.done:
                raise StopIteration
            self.done = True
            value = Stride()
            reference = weakref.ref(value)
            return value

    strides: Any = Operands()
    indices: Any = iter((1,))
    result = (
        _compute_flat_index((), strides, indices)
        if implementation == "native"
        else sum(s * i for s, i in zip(strides, indices, strict=False))
    )
    assert result == 7 and events == ["multiply", "add", "release"]


def test_dot_product_keeps_cpython_compensated_float_sum() -> None:
    assert (
        _compute_flat_index(
            (), cast("Any", (1.0, 1.0, 1.0)), cast("Any", (1e16, 1.0, -1e16))
        )
        == 1.0
    )


def test_arithmetic_stop_iteration_has_generator_cause_and_context() -> None:
    error = StopIteration("original")

    class Stride:
        def __mul__(self, other: Any) -> Any:
            raise error

    with pytest.raises(RuntimeError) as caught:
        _compute_flat_index((), cast("Any", (Stride(),)), (1,))
    assert caught.value.__cause__ is error
    assert caught.value.__context__ is error


@pytest.mark.parametrize("order", list(StorageOrder))
def test_external_stride_sequence_never_reads_the_unused_end_axis(
    order: StorageOrder,
) -> None:
    events: list[int] = []
    unused = 0 if order is StorageOrder.ROW_MAJOR else 2

    class Dims:
        def __len__(self) -> int:
            return 3

        def __getitem__(self, axis: int) -> int:
            assert axis != unused
            events.append(axis)
            return (2, 3, 4)[axis]

    value = _compute_strides(cast("Any", Dims()), order)
    assert value == ((12, 4, 1) if unused == 0 else (1, 2, 6))
    assert events == ([2, 1] if unused == 0 else [0, 1])


@pytest.mark.parametrize("implementation", ["legacy", "native"])
def test_dot_generator_releases_operands_at_exhaustion_before_sum_returns(
    implementation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    reference: Any = None

    class Stride:
        def __mul__(self, other: Any) -> int:
            return 7

    class Operands:
        done = False

        def __iter__(self) -> Any:
            return self

        def __next__(self) -> Any:
            nonlocal reference
            if self.done:
                raise StopIteration
            self.done = True
            value = Stride()
            reference = weakref.ref(value)
            return value

    def summation(values: Any) -> int:
        assert list(values) == [7]
        assert reference() is None
        return 7

    strides: Any = Operands()
    with monkeypatch.context() as patch:
        patch.setattr(builtins, "sum", summation)
        value = (
            _compute_flat_index((), strides, (1,))
            if implementation == "native"
            else sum(s * i for s, i in zip(strides, (1,), strict=False))
        )
    assert value == 7


def test_native_dot_cursor_is_gc_visible_and_reentry_fails_without_locking() -> None:
    class Stride:
        def __mul__(self, other: Any) -> int:
            cursors = [
                value
                for value in gc.get_referrers(self)
                if type(value).__name__ == "ShapeTerms"
            ]
            assert len(cursors) == 1
            with pytest.raises(ValueError, match="generator already executing"):
                next(cursors[0])
            return 7

    assert _compute_flat_index((), cast("Any", (Stride(),)), (1,)) == 7


@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize(
    "dims", [(), (1,), (1, 1, 1), (2, 1, 1), (1, 1, 2), (1, 2, 1), (2, 1, 3)]
)
def test_unit_axes_keep_both_dense_layouts_and_permissive_indices(
    order: StorageOrder, dims: tuple[int, ...]
) -> None:
    shape = DynShape(dims, order)
    expected = tuple(
        int(
            np.prod(
                dims[axis + 1 :] if order is StorageOrder.ROW_MAJOR else dims[:axis]
            )
        )
        for axis in range(len(dims))
    )
    assert shape.strides() == expected
    vectors = list(itertools.product(*(range(dim) for dim in dims)))
    vectors.extend([(), (-1,), tuple(dims), (3,) * (len(dims) + 1)])
    for indices in vectors:
        assert shape.flat_index(*indices) == sum(
            stride * index for stride, index in zip(expected, indices, strict=False)
        )


@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize(
    "dims",
    [
        (7,),
        (2, 3),
        (2, 1, 3),
        (2, 3, 1, 5),
        (2, 1, 3, 1, 5),
        (2, 3, 1, 1, 5, 1, 7, 1),
        (2, 1, 3, 1, 5, 1, 7, 1, 11),
        (sys.maxsize, 1, 1, 1, 1),
    ],
)
def test_dense_strides_across_group_boundaries(
    order: StorageOrder, dims: tuple[int, ...]
) -> None:
    """分组边界仍遵守完整布局 / Group boundaries retain the full layout."""
    expected = tuple(
        math.prod(dims[axis + 1 :] if order is StorageOrder.ROW_MAJOR else dims[:axis])
        for axis in range(len(dims))
    )
    assert DynShape(dims, order).strides() == expected


@pytest.mark.parametrize("order", list(StorageOrder))
def test_dense_strides_preserve_high_rank(order: StorageOrder) -> None:
    """高维结果与输入秩一致 / High-rank strides retain the input rank."""
    result = DynShape((1,) * 100_000, order).strides()
    assert len(result) == 100_000 and all(value == 1 for value in result)


@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize(
    "dims",
    [
        (),
        (7,),
        (2, 3, 1, 5),
        (2, 1, 3, 1, 5),
        (2, 3, 1, 1, 5, 1, 7, 1),
        (2, 1, 3, 1, 5, 1, 7, 1, 11),
        (sys.maxsize, 1, 1, 1, 1),
    ],
)
def test_dense_flat_index_across_group_boundaries(
    order: StorageOrder, dims: tuple[int, ...]
) -> None:
    """分组索引与布局一致 / Grouped indices follow the complete layout."""
    shape = DynShape(dims, order)
    for indices in (
        (0,) * len(dims),
        tuple(dim // 2 for dim in dims),
        tuple(dim - 1 for dim in dims),
    ):
        expected = sum(
            index
            * math.prod(
                dims[axis + 1 :] if order is StorageOrder.ROW_MAJOR else dims[:axis]
            )
            for axis, index in enumerate(indices)
        )
        assert shape.flat_index(*indices) == expected


@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize(
    "dims", [(sys.maxsize,), (sys.maxsize, 2), (1 << 200, 3), (0, 3), (-2, 3)]
)
def test_machine_boundary_never_truncates_permissive_metadata(
    order: StorageOrder, dims: tuple[int, ...]
) -> None:
    expected: tuple[int, ...] = (
        (1,)
        if len(dims) == 1
        else ((dims[1], 1) if order is StorageOrder.ROW_MAJOR else (1, dims[0]))
    )
    strides = _compute_strides(dims, order)
    assert strides == expected
    for indices in [dims, (-1,), (sys.maxsize, sys.maxsize), (1 << 300, -7, 9)]:
        assert _compute_flat_index(dims, strides, indices) == sum(
            stride * index for stride, index in zip(expected, indices, strict=False)
        )


def test_integer_subclasses_keep_numeric_hooks_instead_of_machine_extraction() -> None:
    events: list[tuple[str, int]] = []

    class Index(int):
        def __rmul__(self, other: Any) -> int:
            events.append(("multiply", other))
            return 101

        def __index__(self) -> int:
            pytest.fail("不能读取子类索引钩子 / Must not read a subclass index hook")

    indices = (Index(1), Index(2))
    assert _compute_flat_index((2, 3), (3, 1), indices) == 202
    assert events == [("multiply", 3), ("multiply", 1)]


def test_public_flat_index_still_observes_overridden_strides_and_attribute_order() -> (
    None
):
    events: list[str] = []

    class Derived(Shape2):
        @property
        def dims(self) -> tuple[int, ...]:
            events.append("dims")
            return (2, 3)

        def strides(self) -> tuple[int, ...]:
            events.append("strides")
            return (100, 7)

    assert Derived(2, 3).flat_index(1, 2) == 114
    assert events == ["dims", "strides"]
