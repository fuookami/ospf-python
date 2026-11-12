"""平方/曼哈顿距离的完整公开域合同，尚非 Rust 切换。

Full public-domain contracts for `distance_squared` and `manhattan_distance`.
These pin the current Python behaviour; they do not claim a Rust cutover.
"""

from __future__ import annotations

import decimal
import gc
import importlib
import math
import warnings
import weakref
from collections.abc import Callable
from decimal import Decimal
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

import ospf_python.math.geometry as geometry_package
from ospf_python.math.geometry import distance, distance_squared, manhattan_distance
from ospf_python.math.geometry.point import Point

# 公共签名注解写成 `-> float`，但本合同固定的实际公开域会返回 Decimal、Fraction、
# 复数、NumPy 标量与数组。测试显式把入口当作动态边界，不用注解否认实测行为。
# The public annotations claim ``float``; the observed domain is open, so these
# contracts call the entries through a dynamic boundary instead of trusting them.
squared_call: Callable[..., Any] = distance_squared
manhattan_call: Callable[..., Any] = manhattan_distance


def points(first: Any, second: Any) -> tuple[Point, Point]:
    """Return the two points whose axes are the mirrored operands.

    Args:
        first: coordinate used for ``p1.x`` and ``p2.y``.
        second: coordinate used for ``p1.y`` and ``p2.x``.
    """
    return Point(first, second), Point(second, first)


@pytest.mark.parametrize("function", [distance_squared, manhattan_distance])
def test_package_export_is_the_same_object_as_the_module_definition(
    function: Any,
) -> None:
    assert getattr(geometry_package, function.__name__) is function
    assert (
        getattr(importlib.import_module(function.__module__), function.__name__)
        is function
    )
    assert function.__module__ == "ospf_python.math.geometry.distance"
    assert function.__name__ in geometry_package.__all__


def test_package_namespace_shadows_the_distance_module_with_the_function() -> None:
    # `from ospf_python.math.geometry import distance` 取到的是函数，不是子模块。
    # The package re-export shadows the ``distance`` submodule, so alias identity is
    # only provable through the module object itself.
    assert distance is geometry_package.distance
    assert callable(distance) and not hasattr(distance, "distance_squared")
    assert (
        importlib.import_module("ospf_python.math.geometry.distance").distance
        is distance
    )


def test_squared_and_manhattan_follow_the_ambient_decimal_context() -> None:
    first, second = points(Decimal("1E+20"), Decimal("1"))
    with decimal.localcontext() as context:
        context.prec = 28
        squared = distance_squared(first, second)
        manhattan = manhattan_distance(first, second)
        context.prec = 60
        wide_squared = distance_squared(first, second)
    assert squared == Decimal("1.999999999999999999960000000E+40")
    assert manhattan == Decimal("199999999999999999998")
    assert wide_squared == Decimal("19999999999999999999600000000000000000002")


def test_decimal_overflow_signal_propagates_as_an_exception() -> None:
    first, second = points(Decimal("1E+3000000"), Decimal("1"))
    with decimal.localcontext() as context:
        context.traps[decimal.Overflow] = True
        with pytest.raises(decimal.Overflow):
            distance_squared(first, second)


@pytest.mark.parametrize(
    ("coordinate", "expected"),
    [
        (Decimal("Infinity"), Decimal("Infinity")),
        (Decimal("-0"), Decimal("0")),
    ],
)
def test_decimal_special_values_keep_decimal_semantics(
    coordinate: Decimal,
    expected: Decimal,
) -> None:
    first, second = points(coordinate, Decimal("0"))
    squared = squared_call(first, second)
    manhattan = manhattan_call(first, second)
    assert squared == expected and manhattan == expected
    assert type(squared) is Decimal and type(manhattan) is Decimal


def test_decimal_nan_propagates_in_both_paths() -> None:
    first, second = points(Decimal("NaN"), Decimal("0"))
    assert squared_call(first, second).is_nan()
    assert manhattan_call(first, second).is_nan()


def test_fraction_domain_stays_exact_and_signed_results_are_possible() -> None:
    first, second = points(Fraction(1, 3), Fraction(0))
    assert distance_squared(first, second) == Fraction(2, 9)
    assert manhattan_distance(first, second) == Fraction(2, 3)
    complex_first, complex_second = points(3 + 4j, 0j)
    assert distance_squared(complex_first, complex_second) == -14 + 48j
    assert manhattan_distance(complex_first, complex_second) == 10.0
    assert type(manhattan_distance(complex_first, complex_second)) is float


def test_bool_coordinates_widen_to_int() -> None:
    first, second = points(True, False)
    assert type(distance_squared(first, second)) is int
    assert type(manhattan_distance(first, second)) is int
    assert distance_squared(first, second) == 2
    assert manhattan_distance(first, second) == 2


def test_unsupported_operand_pairs_raise_the_original_type_error() -> None:
    first, second = points(Fraction(3, 2), Decimal("1"))
    with pytest.raises(TypeError):
        distance_squared(first, second)
    with pytest.raises(TypeError):
        manhattan_distance(first, second)
    text_first, text_second = points("3", "1")
    with pytest.raises(TypeError):
        distance_squared(text_first, text_second)


def test_numpy_integer_domain_wraps_and_warns_instead_of_growing() -> None:
    first, second = points(np.int8(20), np.int8(4))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        squared = squared_call(first, second)
        manhattan = manhattan_call(first, second)
    assert squared == np.int8(0) and manhattan == np.int8(32)
    assert squared.dtype == np.int8 and manhattan.dtype == np.int8
    assert [str(item.message) for item in caught] == [
        "overflow encountered in scalar multiply",
        "overflow encountered in scalar multiply",
    ]


def test_numpy_arrays_stay_elementwise_and_preserve_dtype_and_shape() -> None:
    first, second = points(
        np.array([300, 400], dtype=np.int16),
        np.array([0, 0], dtype=np.int16),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        squared = squared_call(first, second)
    np.testing.assert_array_equal(squared, np.array([-16608, -7680], dtype=np.int16))
    assert squared.dtype == np.int16 and squared.shape == (2,)
    assert manhattan_call(first, second).tolist() == [600, 800]


def test_float32_squares_overflow_to_infinity_while_distance_stays_finite() -> None:
    first, second = points(np.float32(1e20), np.float32(0))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert np.isinf(distance_squared(first, second))
    wide_first, wide_second = points(1e308, 0.0)
    assert math.isinf(distance_squared(wide_first, wide_second))
    assert math.isinf(manhattan_distance(wide_first, wide_second))
    tiny_first, tiny_second = points(1e-200, 0.0)
    assert distance_squared(tiny_first, tiny_second) == 0.0
    assert manhattan_distance(tiny_first, tiny_second) == 2e-200


@pytest.mark.parametrize("function", [distance_squared, manhattan_distance])
def test_nonfinite_combinations_match_the_pinned_probe_categories(
    function: Any,
) -> None:
    nan = math.nan
    inf = math.inf
    cases = [
        points(inf, 0.0),
        points(inf, inf),
        points(nan, inf),
        points(inf, nan),
        points(-0.0, 0.0),
    ]
    for first, second in cases:
        result = function(first, second)
        assert type(result) is float
        assert math.isnan(result) or math.isinf(result) or result == 0.0
    assert math.isnan(function(*points(inf, inf)))
    assert math.isnan(function(*points(nan, inf)))
    assert math.isnan(function(*points(inf, nan)))
    result = function(*points(-0.0, 0.0))
    assert result == 0.0 and math.copysign(1.0, result) == 1.0


def test_multiplication_failure_keeps_identity_and_stops_before_the_second_product() -> (
    None
):
    events: list[str] = []
    error = ValueError("mul-failed")

    class Difference:
        def __mul__(self, other: Difference) -> Any:
            events.append("multiply")
            raise error

        def __abs__(self) -> Any:
            events.append("abs")
            return 1

    class Coordinate:
        def __sub__(self, other: Coordinate) -> Difference:
            events.append("subtract")
            return Difference()

    class ObservedPoint:
        def __init__(self, *, side: str) -> None:
            self.side = side

        def __getattr__(self, axis: str) -> Any:
            events.append(f"read:{self.side}.{axis}")
            return Coordinate() if axis == "x" else 0.0

    a: Any = ObservedPoint(side="a")
    b: Any = ObservedPoint(side="b")
    with pytest.raises(ValueError) as caught:
        distance_squared(a, b)
    assert caught.value is error
    assert events == [
        "read:a.x",
        "read:b.x",
        "subtract",
        "read:a.y",
        "read:b.y",
        "multiply",
    ]


def test_absent_absolute_protocol_fails_before_the_second_axis_is_read() -> None:
    events: list[str] = []

    class Coordinate:
        def __sub__(self, other: Coordinate) -> Coordinate:
            events.append("subtract")
            return self

    class ObservedPoint:
        def __init__(self, *, side: str) -> None:
            self.side = side

        def __getattr__(self, axis: str) -> Any:
            events.append(f"read:{self.side}.{axis}")
            return Coordinate() if axis == "x" else 0.0

    a: Any = ObservedPoint(side="a")
    b: Any = ObservedPoint(side="b")
    with pytest.raises(TypeError):
        manhattan_distance(a, b)
    assert events == ["read:a.x", "read:b.x", "subtract"]


@pytest.mark.parametrize("function", [distance_squared, manhattan_distance])
def test_completed_calls_do_not_retain_point_owners(function: Any) -> None:
    a, b = Point(3.0, 4.0), Point(0.0, 0.0)
    refs = weakref.ref(a), weakref.ref(b)
    assert function(a, b)
    del a, b
    gc.collect()
    assert all(ref() is None for ref in refs)
