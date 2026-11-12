"""标量混沌映射的迁移边界 / Migration boundaries for scalar chaotic maps."""

from __future__ import annotations

import math
import sys
from typing import Any

import numpy as np
import pytest

from ospf_python.math.chaotic.arnold_tongue import ArnoldTongue
from ospf_python.math.chaotic.chebyshev_map import ChebyshevMap
from ospf_python.math.chaotic.circle_map import CircleMap
from ospf_python.math.chaotic.dyadic_transformation import DyadicTransformation
from ospf_python.math.chaotic.exponential_map import ExponentialMap
from ospf_python.math.chaotic.gauss_iterated_map import GaussIteratedMap
from ospf_python.math.chaotic.gauss_map import GaussMap
from ospf_python.math.chaotic.logistic_map import LogisticMap
from ospf_python.math.chaotic.sine_map import SineMap
from ospf_python.math.chaotic.singer_map import SingerMap
from ospf_python.math.chaotic.sinus_map import SinusMap
from ospf_python.math.chaotic.sinusoidal_map import SinusoidalMap
from ospf_python.math.chaotic.tent_map import TentMap


@pytest.mark.parametrize("value", [0.0, -0.0])
def test_gauss_zero_keeps_division_error(value: float) -> None:
    with pytest.raises(ZeroDivisionError):
        GaussMap()(value)


@pytest.mark.parametrize("value", [-0.4, 0.4])
def test_gauss_returns_fractional_reciprocal(value: float) -> None:
    assert GaussMap()(value) == 0.5


def test_exponential_map_is_population_map_and_propagates_overflow() -> None:
    assert ExponentialMap()(0.0) == 0.0
    with pytest.raises(OverflowError):
        ExponentialMap()(-1000.0)


def test_singer_keeps_all_public_polynomial_coefficients() -> None:
    assert SingerMap(mu=1.0, a1=0.0, a2=0.0, a3=1.0)(0.5) == -0.125
    assert SingerMap(mu=1.0, a1=0.0, a2=1.0, a3=0.0)(0.5) == -0.25


def test_sinus_and_tent_keep_python_formulas_and_defaults() -> None:
    assert SinusMap()(-0.5) == -1.0
    assert TentMap().mu == 2.0
    assert TentMap()(0.25) == 0.5


def test_circle_and_arnold_tongue_do_not_wrap_results() -> None:
    assert CircleMap(omega=0.5, k=0.0)(0.75) == 1.25
    assert ArnoldTongue(omega=0.5, k=0.0)(0.75) == 1.25


@pytest.mark.parametrize("value", [-1.5, 1.5, math.inf, -math.inf])
def test_chebyshev_preserves_acos_domain_errors(value: float) -> None:
    with pytest.raises(ValueError):
        ChebyshevMap()(value)


def test_chebyshev_preserves_nan() -> None:
    assert math.isnan(ChebyshevMap()(math.nan))


@pytest.mark.parametrize(
    "mapping", [SineMap(), SinusoidalMap(), ArnoldTongue(), SinusMap()]
)
@pytest.mark.parametrize("value", [math.inf, -math.inf, sys.float_info.max])
def test_sine_based_maps_propagate_math_domain_error(
    *, mapping: Any, value: float
) -> None:
    with pytest.raises(ValueError):
        mapping(value)


def test_gauss_iterated_propagates_exponential_overflow() -> None:
    with pytest.raises(OverflowError):
        GaussIteratedMap(alpha=-1.0, beta=0.0)(1000.0)


def test_logistic_preserves_array_numeric_protocol() -> None:
    value: Any = np.array([0.25, 0.75])
    result = LogisticMap()(value)
    assert isinstance(result, np.ndarray)
    np.testing.assert_allclose(result, [0.73125, 0.73125])


@pytest.mark.parametrize("value", [math.inf, -math.inf, sys.float_info.max])
def test_dyadic_nonfinite_result_is_nan(value: float) -> None:
    assert math.isnan(DyadicTransformation()(value))


@pytest.mark.parametrize(
    "mapping",
    [
        DyadicTransformation(),
        ExponentialMap(),
        GaussIteratedMap(),
        GaussMap(),
        LogisticMap(),
        SineMap(),
        SingerMap(),
        SinusMap(),
        SinusoidalMap(),
        TentMap(),
    ],
)
@pytest.mark.parametrize("count", [0, -1])
def test_nonpositive_scalar_iteration_preserves_input_identity(
    *, mapping: Any, count: int
) -> None:
    value = object()
    assert mapping.iterate(value, n=count) is value


@pytest.mark.parametrize("mapping", [ArnoldTongue(), ChebyshevMap(), CircleMap()])
@pytest.mark.parametrize("count", [0, -1])
def test_nonpositive_list_iteration_preserves_initial_identity(
    *, mapping: Any, count: int
) -> None:
    value = object()
    result = mapping.iterate(value, n=count)
    assert len(result) == 1
    assert result[0] is value


def test_logistic_preserves_python_numeric_dispatch_order() -> None:
    events: list[tuple[str, Any]] = []
    right = object()
    result = object()

    class Left:
        def __mul__(self, other: Any) -> object:
            events.append(("multiply", other))
            return result

    class Input:
        def __rmul__(self, other: Any) -> Left:
            events.append(("reflected_multiply", other))
            return Left()

        def __rsub__(self, other: Any) -> object:
            events.append(("reflected_subtract", other))
            return right

        def __float__(self) -> float:
            raise AssertionError("numeric protocols must not be coerced to float")

    value: Any = Input()
    actual: Any = LogisticMap()(value)
    assert actual is result
    assert events == [
        ("reflected_multiply", 3.9),
        ("reflected_subtract", 1.0),
        ("multiply", right),
    ]


def test_scalar_iteration_calls_the_overridden_public_step() -> None:
    calls: list[float] = []

    class CustomLogistic(LogisticMap):
        def __call__(self, value: float) -> float:
            calls.append(value)
            return value + 1.0

    assert CustomLogistic().iterate(2.0, n=3) == 5.0
    assert calls == [2.0, 3.0, 4.0]


def test_list_iteration_includes_initial_value_and_overridden_steps() -> None:
    class CustomCircle(CircleMap):
        def __call__(self, value: float) -> float:
            return value + 1.0

    assert CustomCircle().iterate(2.0, n=3) == [2.0, 3.0, 4.0, 5.0]
