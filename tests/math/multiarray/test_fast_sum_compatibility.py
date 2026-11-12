"""迁移前有效归约行为与待修缺陷 / Valid pre-migration reductions and known defects.

本文件不表示归约已经切换到 Rust；严格 xfail 记录错误而不是将其固化为合同。
This does not claim a Rust cutover; strict xfails record defects rather than bless them.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python.math.multiarray.fast_sum import fast_sum
from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import (
    DimensionMismatchingException,
    DynShape,
    StorageOrder,
)

_DTYPES = [
    "bool",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "float16",
    "float32",
    "float64",
    "longdouble",
    "complex64",
    "complex128",
    "clongdouble",
    ">i4",
    ">f8",
]


@pytest.mark.parametrize("dtype", _DTYPES)
@pytest.mark.parametrize("axis", [0, 1, 2, -1, -3, np.int64(-2)])
def test_numeric_axis_dtype_promotion_and_negative_axes(dtype: str, axis: Any) -> None:
    data = np.arange(24).astype(dtype)
    if data.dtype.kind in "fc":
        data /= 8
    if data.dtype.kind == "c":
        data += 2j
    source: MultiArray[Any, DynShape] = MultiArray(DynShape((2, 3, 4)), data)
    expected = np.sum(data.reshape((2, 3, 4)), axis=axis)
    result = fast_sum(source, axis=axis)
    assert result.shape.dims == expected.shape
    assert result.shape.storage_order is StorageOrder.ROW_MAJOR
    assert result._data.dtype == expected.dtype
    np.testing.assert_array_equal(result._data, expected.reshape(-1))
    assert not np.shares_memory(result._data, data)


@pytest.mark.parametrize("dtype", _DTYPES[:13])
def test_current_all_reduction_has_a_python_float_envelope(dtype: str) -> None:
    data = np.arange(24).astype(dtype)
    source: MultiArray[Any, DynShape] = MultiArray(DynShape((2, 3, 4)), data)
    result = fast_sum(source)
    assert type(result) is float
    assert result == float(np.sum(data))


@pytest.mark.parametrize("cls", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("axis", [None, 0, -1])
def test_rank_zero_current_numpy_axis_special_case(cls: Any, axis: Any) -> None:
    result = fast_sum(cls(DynShape(()), np.array([7], dtype=np.int16)), axis=axis)
    if axis is None:
        assert result == 7.0
    else:
        assert result.shape.dims == ()
        assert result._data.dtype == np.dtype(np.intp)
        np.testing.assert_array_equal(result._data, [7])


@pytest.mark.parametrize("dims", [(0,), (0, 3), (2, 0, 3)])
def test_legacy_public_shape_rejects_zero_dimensions(
    dims: tuple[int, ...],
) -> None:
    with pytest.raises(DimensionMismatchingException):
        DynShape(dims)


@pytest.mark.parametrize("stride", [2, -2, 0])
@pytest.mark.parametrize("cls", [MultiArray, MutableMultiArray])
def test_shared_strided_input_is_reread_but_outputs_are_independent(
    stride: int, cls: Any
) -> None:
    backing = np.arange(48, dtype=np.float64)
    data = np.broadcast_to(backing[:1], (24,)) if stride == 0 else backing[::stride]
    source = cls(DynShape((2, 3, 4)), data)
    first = fast_sum(source, axis=1)
    frozen = first._data.copy()
    backing[:] = 5
    second = fast_sum(source, axis=1)
    np.testing.assert_array_equal(first._data, frozen)
    np.testing.assert_array_equal(second._data, np.full(8, 15))
    assert fast_sum(source) == 120.0
    assert not np.shares_memory(second._data, backing)


@pytest.mark.parametrize("dtype", ["int64", "uint64"])
def test_integer_accumulation_is_modular_not_debug_overflow(dtype: str) -> None:
    info = np.iinfo(dtype)
    data = np.array([info.max, 1], dtype=dtype)
    expected = info.min if dtype == "int64" else 0
    result = fast_sum(MultiArray(DynShape((2,)), data), axis=0)
    assert result.shape.dims == ()
    assert result._data[0] == expected


@pytest.mark.parametrize("factory", [Fraction, Decimal])
@pytest.mark.parametrize("axis", [0, 1])
def test_object_axis_reduction_preserves_exact_arithmetic(
    factory: Any, axis: int
) -> None:
    data = np.array([factory(1) / factory(3)] * 6, dtype=object)
    result = fast_sum(MultiArray(DynShape((2, 3)), data), axis=axis)
    expected = np.sum(data.reshape((2, 3)), axis=axis)
    assert result._data.dtype == np.dtype(object)
    assert all(type(value) is factory for value in result._data)
    np.testing.assert_array_equal(result._data, expected)


@pytest.mark.parametrize("dtype", ["timedelta64[D]", "timedelta64[ns]"])
def test_timedelta_axis_reduction_retains_unit(dtype: str) -> None:
    data = np.arange(6).astype(dtype)
    result = fast_sum(MultiArray(DynShape((2, 3)), data), axis=0)
    assert result._data.dtype == data.dtype
    np.testing.assert_array_equal(result._data, np.sum(data.reshape((2, 3)), axis=0))


def test_numpy_pairwise_cancellation_is_not_a_left_fold() -> None:
    data = np.array([1e16, 1, 1, 1, 1, 1, 1, -1e16], dtype=np.float64)
    assert fast_sum(MultiArray(DynShape((8,)), data)) == 4.0
    accumulator = 0.0
    for value in data:
        accumulator += value
    assert accumulator == 0.0


@pytest.mark.parametrize(
    "values",
    [[np.nan, 1], [np.inf, 1], [-np.inf, 1], [np.inf, -np.inf], [-0.0, -0.0]],
)
@pytest.mark.parametrize("axis", [None, 0, 1])
def test_nonfinite_values_and_signed_zero(values: list[float], axis: Any) -> None:
    data = np.array(values, dtype=np.float64)
    with np.errstate(invalid="ignore"):
        expected = np.sum(data.reshape((1, 2)), axis=axis)
        result = fast_sum(MultiArray(DynShape((1, 2)), data), axis=axis)
    observed = np.array(result) if axis is None else result._data
    np.testing.assert_array_equal(observed.reshape(-1), expected.reshape(-1))
    np.testing.assert_array_equal(
        np.signbit(observed).reshape(-1), np.signbit(expected).reshape(-1)
    )


def test_nonempty_object_groups_do_not_require_adding_an_integer_zero() -> None:
    class Leaf:
        def __init__(self, trace: str) -> None:
            self.trace = trace

        def __add__(self, other: Leaf) -> Leaf:
            assert type(other) is Leaf
            return Leaf(f"({self.trace}+{other.trace})")

    data = np.array([Leaf("a"), Leaf("b"), Leaf("c"), Leaf("d")], dtype=object)
    source: MultiArray[Any, DynShape] = MultiArray(DynShape((2, 2)), data)
    axis0 = fast_sum(source, axis=0)
    axis1 = fast_sum(source, axis=1)
    assert [value.trace for value in axis0._data] == ["(a+c)", "(b+d)"]
    assert [value.trace for value in axis1._data] == ["(a+b)", "(c+d)"]
    assert [value.trace for value in data] == ["a", "b", "c", "d"]


def test_object_arithmetic_original_failure_does_not_publish_or_mutate() -> None:
    failure = RuntimeError("外部叶失败 / External leaf failure")

    class Leaf:
        def __add__(self, other: Any) -> Any:
            raise failure

    data = np.array([Leaf() for _ in range(4)], dtype=object)
    before = list(data)
    source: MultiArray[Any, DynShape] = MultiArray(DynShape((2, 2)), data)
    with pytest.raises(RuntimeError) as caught:
        fast_sum(source, axis=0)
    assert caught.value is failure
    assert all(old is new for old, new in zip(before, data, strict=True))


@pytest.mark.parametrize("axis", [0, 1, 2])
def test_column_layout_must_reduce_logical_axes(axis: int) -> None:
    data = np.arange(24, dtype=np.int64)
    source: MultiArray[Any, DynShape] = MultiArray(
        DynShape((2, 3, 4), StorageOrder.COLUMN_MAJOR), data
    )
    result = fast_sum(source, axis=axis)
    expected = np.sum(data.reshape((2, 3, 4), order="F"), axis=axis)
    np.testing.assert_array_equal(result._data, expected.reshape(-1))


def test_complex_all_must_not_discard_imaginary_part() -> None:
    data = np.array([1 + 2j, 3 + 4j])
    result = fast_sum(MultiArray(DynShape((2,)), data))
    assert result == 4 + 6j


def test_object_sum_that_float_cannot_convert_is_returned_not_raised() -> None:
    """NumPy 能求和的元组元素不能因 float() 而崩。 / Tuple-valued sums must not crash on float()."""
    data = np.empty(2, dtype=object)
    data[0] = (1, 2)
    data[1] = (3, 4)
    result = fast_sum(MultiArray(DynShape((2,)), data))
    assert result == (1, 2, 3, 4)


def test_integer_all_must_not_round_exact_result() -> None:
    data = np.array([2**53, 1], dtype=np.int64)
    result = fast_sum(MultiArray(DynShape((2,)), data))
    assert result == 2**53 + 1


@pytest.mark.parametrize("value", [Fraction(1, 3), Decimal("0.1")])
def test_rank_one_object_axis_must_publish_a_scalar_array(value: Any) -> None:
    data = np.array([value, value], dtype=object)
    result = fast_sum(MultiArray(DynShape((2,)), data), axis=0)
    assert result.shape.dims == ()
    assert result._data[0] == value + value


class TestInvalidAxisIsNeverSilentlyWrong:
    """FS-006：最终不存在的轴绝不能静默返回错值 / An axis missing from the final rank must never be silently wrong."""

    @staticmethod
    def _array(dims: tuple[int, ...]) -> MultiArray[Any, Any]:
        total = 1
        for dim in dims:
            total *= dim
        return MultiArray(
            DynShape(dims=dims), np.arange(1, total + 1, dtype=np.float64)
        )

    @pytest.mark.parametrize(
        ("dims", "axis"),
        [((2, 3), 2), ((2, 3), 3), ((3,), 1), ((3,), 5), ((2, 3), -5)],
        ids=["2x3-axis2", "2x3-axis3", "3-axis1", "3-axis5", "2x3-axis-minus5"],
    )
    def test_axis_outside_final_rank_raises(
        self, dims: tuple[int, ...], axis: int
    ) -> None:
        """越界轴必须抛 ValueError，而不是返回一个错的和。

        实测过旧行为：axis=1 对 (2,3) 秩归约后返回全部元素之和（15），
        axis=2 对 (2,3,4) 返回未归约的 24 个原值 —— 都是静默错值。
        An out-of-range axis must raise instead of returning a wrong sum. The old behaviour
        was measured: axis=1 over (2,3) returned the full total (15), and axis=2 over
        (2,3,4) returned all 24 unreduced values.
        """
        with pytest.raises(ValueError, match="does not exist on the final rank"):
            fast_sum(self._array(dims), axis=axis)

    @pytest.mark.parametrize(
        ("dims", "axis", "expected"),
        [
            ((2, 3), 0, [5.0, 7.0, 9.0]),
            ((2, 3), 1, [6.0, 15.0]),
            ((2, 3), -1, [6.0, 15.0]),
        ],
        ids=["axis0", "axis1", "axis-minus1"],
    )
    def test_valid_axis_still_reduces(
        self, dims: tuple[int, ...], axis: int, expected: list[float]
    ) -> None:
        """合法轴（含负轴）仍然正常归约。 / Valid axes, including negative ones, still reduce."""
        result = fast_sum(self._array(dims), axis=axis)
        np.testing.assert_allclose(
            result._data.reshape(result.shape.dims), np.array(expected)
        )
