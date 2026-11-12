"""几何距离旧公开合同，尚非 Rust 切换。 / Geometry distance baseline, not a Rust cutover."""

from __future__ import annotations

import gc
import math
import weakref
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python.math.geometry.distance import (
    distance,
    distance3,
    distance_squared,
    manhattan_distance,
)
from ospf_python.math.geometry.edge import Edge
from ospf_python.math.geometry.point import Point, Point3
from ospf_python.math.geometry.vector import Vector


@pytest.mark.parametrize("value", [1e308, 1e-200, math.ulp(0.0)])
def test_euclidean_paths_do_not_overflow_or_underflow_intermediate_squares(
    value: float,
) -> None:
    a, b = Point(value, value), Point(0.0, 0.0)
    expected = math.hypot(value, value)
    assert math.isfinite(expected) and expected > 0
    assert distance(a, b) == expected
    assert Edge(start=b, end=a).length() == expected
    assert Vector(value, value).magnitude() == expected
    assert distance3(Point3(value, value, 0.0), Point3(0.0, 0.0, 0.0)) == expected


@pytest.mark.parametrize("value", [math.nan, -math.nan])
def test_euclidean_infinity_dominates_nan(value: float) -> None:
    a, b = Point(math.inf, value), Point(0.0, 0.0)
    assert distance(a, b) == math.inf
    assert Edge(start=b, end=a).length() == math.inf
    assert Vector(math.inf, value).magnitude() == math.inf
    assert distance3(Point3(math.inf, value, 0.0), Point3(0.0, 0.0, 0.0)) == math.inf


def test_zero_and_coincident_infinity_follow_python_math_semantics() -> None:
    result = distance(Point(-0.0, -0.0), Point(0.0, 0.0))
    assert result == 0.0 and math.copysign(1.0, result) == 1.0
    assert math.isnan(distance(Point(math.inf, 0.0), Point(math.inf, 0.0)))
    assert math.isnan(distance3(Point3(math.inf, 0.0, 0.0), Point3(math.inf, 0.0, 0.0)))


def test_two_and_three_dimensional_paths_convert_at_different_times() -> None:
    large: Any = 2**1024
    assert distance(Point(large, 0), Point(large - 3, 0)) == 3.0
    with pytest.raises(OverflowError):
        distance3(Point3(large, 0, 0), Point3(large - 3, 0, 0))


@pytest.mark.parametrize("kind", [int, Decimal, Fraction])
def test_squared_and_manhattan_keep_exact_input_domain(kind: type[Any]) -> None:
    big = 2**256
    x, y = kind(big), kind(3)
    zero = kind(0)
    with localcontext() as context:
        context.prec = 200
        squared = distance_squared(Point(x, y), Point(zero, zero))
        manhattan = manhattan_distance(Point(x, y), Point(zero, zero))
    assert type(squared) is kind and squared == big * big + 9
    assert type(manhattan) is kind and manhattan == big + 3


def test_squared_and_manhattan_preserve_numpy_array_operations() -> None:
    point: Any = Point
    a = point(np.array([1, 3]), np.array([2, 4]))
    b = point(np.array([0, 1]), np.array([0, 1]))
    np.testing.assert_array_equal(distance_squared(a, b), np.array([5, 13]))
    np.testing.assert_array_equal(manhattan_distance(a, b), np.array([3, 5]))


def test_two_dimensional_distance_reads_and_converts_in_expression_order() -> None:
    events: list[str] = []

    class Difference:
        def __init__(self, *, axis: str, value: float) -> None:
            self.axis, self.value = axis, value

        def __float__(self) -> float:
            events.append(f"float:{self.axis}")
            return self.value

    class Coordinate:
        def __init__(self, *, axis: str, value: float) -> None:
            self.axis, self.value = axis, value

        def __sub__(self, other: Coordinate) -> Difference:
            events.append(f"subtract:{self.axis}")
            return Difference(axis=self.axis, value=self.value - other.value)

    class ObservedPoint:
        def __init__(self, *, side: str, x: float, y: float) -> None:
            self.side, self.values = side, {"x": x, "y": y}

        def __getattr__(self, axis: str) -> Coordinate:
            events.append(f"read:{self.side}.{axis}")
            return Coordinate(axis=axis, value=self.values[axis])

    a: Any = ObservedPoint(side="a", x=3.0, y=4.0)
    b: Any = ObservedPoint(side="b", x=0.0, y=0.0)
    assert distance(a, b) == 5.0
    assert events == [
        "read:a.x",
        "read:b.x",
        "subtract:x",
        "read:a.y",
        "read:b.y",
        "subtract:y",
        "float:x",
        "float:y",
    ]


def test_three_dimensional_distance_reads_both_points_before_float_conversion() -> None:
    events: list[str] = []

    class Coordinate:
        def __init__(self, *, name: str, value: float) -> None:
            self.name, self.value = name, value

        def __float__(self) -> float:
            events.append(f"float:{self.name}")
            return self.value

    class ObservedPoint:
        def __init__(self, *, side: str, values: tuple[float, float, float]) -> None:
            self.side, self.values = side, dict(zip("xyz", values, strict=True))

        def __getattr__(self, axis: str) -> Coordinate:
            name = f"{self.side}.{axis}"
            events.append(f"read:{name}")
            return Coordinate(name=name, value=self.values[axis])

    a: Any = ObservedPoint(side="a", values=(1.0, 2.0, 2.0))
    b: Any = ObservedPoint(side="b", values=(0.0, 0.0, 0.0))
    assert distance3(a, b) == 3.0
    assert events == [
        *(f"read:{side}.{axis}" for side in "ab" for axis in "xyz"),
        *(f"float:{side}.{axis}" for axis in "xyz" for side in "ab"),
    ]


@pytest.mark.parametrize("operation", ["squared", "manhattan"])
def test_squared_and_manhattan_preserve_numeric_slot_order(operation: str) -> None:
    events: list[str] = []
    output = object()

    class Term:
        def __init__(self, axis: str) -> None:
            self.axis = axis

        def __add__(self, other: Term) -> object:
            events.append(f"add:{self.axis}:{other.axis}")
            return output

    class Difference:
        def __init__(self, axis: str) -> None:
            self.axis = axis

        def __mul__(self, other: Difference) -> Term:
            assert self is other
            events.append(f"multiply:{self.axis}")
            return Term(self.axis)

        def __abs__(self) -> Term:
            events.append(f"abs:{self.axis}")
            return Term(self.axis)

    class Coordinate:
        def __init__(self, axis: str) -> None:
            self.axis = axis

        def __sub__(self, other: Coordinate) -> Difference:
            events.append(f"subtract:{self.axis}")
            return Difference(self.axis)

    class ObservedPoint:
        def __init__(self, side: str) -> None:
            self.side = side

        def __getattr__(self, axis: str) -> Coordinate:
            events.append(f"read:{self.side}.{axis}")
            return Coordinate(axis)

    a: Any = ObservedPoint("a")
    b: Any = ObservedPoint("b")
    if operation == "squared":
        assert distance_squared(a, b) is output
        assert events == [
            "read:a.x",
            "read:b.x",
            "subtract:x",
            "read:a.y",
            "read:b.y",
            "subtract:y",
            "multiply:x",
            "multiply:y",
            "add:x:y",
        ]
    else:
        assert manhattan_distance(a, b) is output
        assert events == [
            "read:a.x",
            "read:b.x",
            "subtract:x",
            "abs:x",
            "read:a.y",
            "read:b.y",
            "subtract:y",
            "abs:y",
            "add:x:y",
        ]


@pytest.mark.parametrize("error_type", [ValueError, MemoryError, KeyboardInterrupt])
def test_original_subtraction_error_stops_before_the_next_axis(
    error_type: type[BaseException],
) -> None:
    error = error_type("original")
    events: list[str] = []

    class Coordinate:
        def __sub__(self, other: object) -> Any:
            events.append("subtract")
            raise error

    class ObservedPoint:
        def __getattr__(self, axis: str) -> Coordinate:
            events.append(f"read:{axis}")
            return Coordinate()

    a: Any = ObservedPoint()
    b: Any = ObservedPoint()
    for function in (distance, distance_squared, manhattan_distance):
        events.clear()
        with pytest.raises(error_type) as caught:
            function(a, b)
        assert caught.value is error
        assert events == ["read:x", "read:x", "subtract"]


def test_completed_distance_does_not_retain_point_owners() -> None:
    a, b = Point(3.0, 4.0), Point(0.0, 0.0)
    refs = weakref.ref(a), weakref.ref(b)
    assert distance(a, b) == 5.0
    del a, b
    gc.collect()
    assert all(ref() is None for ref in refs)
