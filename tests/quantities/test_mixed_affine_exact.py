"""精确点差运算复用原生换算。 / Exact point/difference arithmetic reuses native conversion."""

from __future__ import annotations

import copy
import pickle
from collections.abc import Callable
from decimal import Context, Decimal, Inexact, Rounded, localcontext
from fractions import Fraction
from typing import Any

import pytest

from ospf_python.quantities import Quantity, Unit
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

_TEMPERATURE = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
_SCALES = (
    (3, 1),
    (-3, 2),
    (3, -2),
    (-3, -2),
    (3, 3),
    (Decimal("1e100"), Decimal("1e-100")),
)


def _unit(*, scale: Any, offset: int | None, name: str) -> Unit:
    return Unit.create(
        name=name, symbol=name, powers=_TEMPERATURE, scale=scale, offset=offset
    ).unwrap()


@pytest.mark.parametrize("point_scale,difference_scale", _SCALES)
@pytest.mark.parametrize(
    "point_value,difference_value", ((0, 1), (Fraction(-17, 19), Fraction(5, 7)))
)
@pytest.mark.parametrize("offset", (0, 273))
@pytest.mark.parametrize("operation", ("point+delta", "delta+point", "point-delta"))
def test_mixed_affine_exact_values_and_actual_point_unit(
    *,
    point_scale: Any,
    difference_scale: Any,
    point_value: Any,
    difference_value: Any,
    offset: int,
    operation: str,
) -> None:
    point = _unit(scale=point_scale, offset=offset, name="point")
    difference = _unit(scale=difference_scale, offset=None, name="difference")
    if operation == "delta+point":
        output, unit = difference.binary_exact(
            value=difference_value, other=point_value, other_unit=point
        ).unwrap()
    else:
        output, unit = point.binary_exact(
            value=point_value,
            other=difference_value,
            other_unit=difference,
            subtract=operation == "point-delta",
        ).unwrap()
    delta = (
        Fraction(difference_value) * Fraction(difference_scale) / Fraction(point_scale)
    )
    expected = Fraction(point_value) + (-delta if operation == "point-delta" else delta)
    assert Fraction(*output.as_integer_ratio()) == expected
    assert unit.descriptor() == point.descriptor()
    assert unit.same_unit(point).unwrap()
    assert unit.is_affine


@pytest.mark.parametrize("roundtrip", ("copy", "deepcopy", "pickle", "json"))
def test_mixed_affine_point_survives_unit_roundtrip(roundtrip: str) -> None:
    original = _unit(scale=3, offset=1, name="point")
    difference = _unit(scale=1, offset=None, name="difference")
    factories: dict[str, Callable[[], Unit]] = {
        "copy": lambda: copy.copy(original),
        "deepcopy": lambda: copy.deepcopy(original),
        "pickle": lambda: pickle.loads(pickle.dumps(original)),
        "json": lambda: Unit.from_json(original.to_json()).unwrap(),
    }
    point = factories[roundtrip]()
    result, output = point.binary_exact(
        value=0, other=1, other_unit=difference
    ).unwrap()
    assert Fraction(*result.as_integer_ratio()) == Fraction(1, 3)
    assert output.descriptor() == point.descriptor() == original.descriptor()
    assert output.to_json() == original.to_json()


@pytest.mark.parametrize("reverse", (False, True))
def test_public_quantity_preserves_point_identity_and_exact_domain(
    reverse: bool,
) -> None:
    point = _unit(scale=3, offset=1, name="point")
    difference = _unit(scale=1, offset=None, name="difference")
    left, right = Quantity(value=0, unit=point), Quantity(value=1, unit=difference)
    result = (right + left if reverse else left + right).unwrap()
    assert type(result.value) is Fraction and result.value == Fraction(1, 3)
    assert result.unit is point
    standard = _unit(scale=1, offset=0, name="standard point")
    assert result.to(standard).unwrap().value == 2


def test_decimal_output_still_requires_explicit_rounding() -> None:
    point = _unit(scale=3, offset=1, name="point")
    difference = _unit(scale=1, offset=None, name="difference")
    left = Quantity(value=Decimal(0), unit=point)
    right = Quantity(value=Decimal(1), unit=difference)
    with localcontext(Context(prec=2)) as current:
        current.clear_flags()
        failure = left + right
        assert isinstance(failure, Failed) and failure.error.code is ErrorCode.DATA_LOSS
        assert current.flags[Inexact] and current.flags[Rounded]
        current.clear_flags()
        selected = Context(prec=8)
        result = left.add(right, context=selected, exact=False).unwrap()
        assert result.value == Decimal("0.33333333")
        assert result.unit is point
        assert selected.flags[Inexact] and selected.flags[Rounded]
        assert not any(current.flags.values())


def test_mixed_affine_invalid_operations_remain_failures() -> None:
    point = _unit(scale=3, offset=1, name="point")
    difference = _unit(scale=1, offset=None, name="difference")
    for failure in (
        point.binary_exact(value=1, other=1, other_unit=point),
        difference.binary_exact(value=1, other=1, other_unit=point, subtract=True),
    ):
        assert isinstance(failure, Failed)
        assert failure.error.code is ErrorCode.ILLEGAL_ARGUMENT
    length = Unit.create(
        name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    assert isinstance(point.binary_exact(value=1, other=1, other_unit=length), Failed)
